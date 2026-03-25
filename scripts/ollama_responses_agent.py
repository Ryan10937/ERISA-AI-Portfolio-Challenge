"""
OllamaResponsesAgent Class
==========================
Main agent orchestrator for ERISA claim denial analysis. Integrates:
- Ollama LLM via OpenAI-compatible API
- ML classifier for denial taxonomy prediction
- Playbook retrieval via tag matching
- Two sub-agents (Tag Agent, Question Agent)
Provides `run()` method for processing claims or answering questions.
"""
import time
import json
import random
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from agents import (
    Agent, set_default_openai_client, OpenAIResponsesModel, 
    SQLiteSession, FunctionTool, Runner, set_tracing_disabled
)
from agents.agent import ToolContext

from playbook import Playbook
from custom_denial_schema import CustomDenialSchema

set_tracing_disabled(True)  # Disable for production

class OllamaResponsesAgent:
    def __init__(
        self,
        *,
        ollama_base_url: str = "http://localhost:11434/v1",
        model_name: str = 'gpt-oss:20b',
        sqlite_path: str = "database/agentic.db",
        session_id: str = "",
    ):
        """
        Initialise the agent, its memory store, and the Ollama Responses model.

        Parameters
        ----------
        ollama_base_url : str
            Base URL of the Ollama instance 
        model_name : str
            Name of the model to use inside Ollama.
        sqlite_path : str
            Path for the SQLite session store.
        """
        self.session = SQLiteSession(
            session_id=session_id,
            db_path=sqlite_path
        )

        client = AsyncOpenAI(
            api_key='ollama',
            base_url=ollama_base_url,  # key detail: route requests to Ollama (local or cloud)
        )
        set_default_openai_client(client)

        self.model = OpenAIResponsesModel(
            model=model_name,
            openai_client=client,
        )

        # Load ML models for denial classification
        pipeline = joblib.load('models/denial_classifier.pkl')
        le = joblib.load('models/label_encoder.pkl')
        self.denial_taxonomy_classifier = {'pipeline': pipeline, 'encoder': le}

        self.tools = [
            self._predict_denial_taxonomy_tool(),
            self._retrieve_playbook_tool(),
            self._gather_ICD10_code_context(),
            self._gather_CPT_code_context(),
        ]

        self.agent = Agent(
            name="Claim Agent",
            model=self.model,
            tools=self.tools,
            output_type=CustomDenialSchema(),
            instructions="""You are a patient advocate. 
                            Always call the tools predict_denial_taxonomy and retrieve_playbook.
                            If you're given a claim information dictionary, then your job is to suggest a recommendation for how to best proceed.
                            This recommendation can be one of the following options and nothing else: pursue, do_not_pursue, or needs_info. Always use
                            the retrieve_playbook tool to get more information and instructions specific to the type of claim and denial code.

                            If the claim lacks denial text, do not use the predict_with_explain tool.
                            
                            Always use the get_ICD10_code_context and get_CPT_code_context tools to get additional medical context if the denial was due to the procedure was not medically necessary.

                            Ensure format follows output schema specified and JSON format is correct.
                         """
        )
        
        self.playbook = Playbook('data/playbook_chunks.jsonl')
        
        self.tag_agent = Agent(
            name="Tag Assigning Agent",
            instructions="""You will be given an insurance claim and asked to assign any number of tags to it. Your first tag will always be 'general'
                            If you find any of the following in the claim, it MUST be one of your tags: CO-16, CO-27, CO-29, CO-45, CO-97.
                            Also assign any of the following tags if appropriate: coding_bundling, eligibility, general, medical_necessity, missing_info, other, timely_filing, underpayment
                         """,
            model=self.model,
        )

        self.question_agent = Agent(
            name="Question Agent",
            model=self.model,
            instructions="""You will be asked about a claim within this session. Answer using the history as context."""
        )

        self.icd_10_code_df = pd.read_excel('data/section111_valid_icd10_october2025.xlsx')
        self.cpt_code_df = pd.read_excel('data/2026_DHS_Code_List_Addendum_12_01_2025.xlsx')

    def _predict_denial_taxonomy_tool(self) -> FunctionTool:
        """ML-powered denial taxonomy prediction tool using pre-trained scikit-learn pipeline."""

        def predict_with_explain(pipeline, le, sample_df):
            if sample_df['denial_text'].isna().all() and sample_df['denial_code'].isna().all():
                return {'label': 'unknown', 'confidence': 0.0, 'top_features': []}
            
            X_trans = pipeline.named_steps['preprocessor'].transform(sample_df)
            probs = pipeline.named_steps['classifier'].predict_proba(X_trans)
            pred_idx = np.argmax(probs, axis=1)[0]
            confidence = np.max(probs[0])
            
            if confidence < 0.5:  # replace with entropy?
                return {'label': 'unknown', 'confidence': confidence, 'top_features': []}
            
            pred_label = le.inverse_transform([pred_idx])[0]
            
            # Top features
            coefs = pipeline.named_steps['classifier'].coef_[pred_idx]
            feature_names = (
                pipeline.named_steps['preprocessor'].named_transformers_['text']
                .get_feature_names_out().tolist() +
                list(pipeline.named_steps['preprocessor'].named_transformers_['code']
                     .get_feature_names_out())
            )
            top_indices = np.argsort(np.abs(coefs))[-10:]
            top_features = [(feature_names[i], float(coefs[i])) for i in top_indices[::-1]]
            
            return {'label': pred_label, 'confidence': float(confidence), 'top_features': top_features}

        async def predict_denial_taxonomy(_: ToolContext, denial_info: dict) -> dict:
            """Predict denial taxonomy for claim using denial code + text."""
            # Type error handling
            if isinstance(denial_info, str):
                denial_info = json.loads(denial_info)
            denial_code = denial_info.get('denial_info', 'UNKNOWN')
            denial_text = denial_info.get('denial_text', 'UNKNOWN')

            # Format claim for inference
            denied_claim = pd.DataFrame({
                'denial_code': [denial_code],
                'denial_text': [denial_text]
            })
            result = predict_with_explain(
                self.denial_taxonomy_classifier['pipeline'],
                self.denial_taxonomy_classifier['encoder'],
                denied_claim
            )
            return result

        return FunctionTool(
            name="predict_denial_taxonomy",
            description="predict denial reason for a claim. Provide denial code and denial text and no other parameters",
            on_invoke_tool=predict_denial_taxonomy,
            params_json_schema={
                "type": "object",
                "properties": {
                    "denial_code": {"type": "string", "description": "the 4-6 digit code representing the reason the claim was denied"}, 
                    "denial_text": {"type": "string", "description": "the text describing why the claim was denied"}, 
                },
            },
        )

    def _retrieve_playbook_tool(self) -> FunctionTool:
        """Retrieves playbook guidance by running tag agent on claim description."""

        async def retrieve_playbook(_: ToolContext, tag_prompt: str) -> dict:
            """Get playbook markdown by tag matching."""
            tags_result = await Runner.run(self.tag_agent, tag_prompt)
            return self.playbook.load_markdown_for_tags(tags_result.final_output)

        return FunctionTool(
            name="retrieve_playbook",
            description="Get playbook guidance using denial code/reason. Provide claim description as single string.",
            on_invoke_tool=retrieve_playbook,
            params_json_schema={
                "type": "object",
                "properties": {
                    "claim_information": {"type": "string", "description": "the denial text for the claim"}
                },
                "required": ["claim_information"],
                "additionalProperties": False,
            },
        )
    def _gather_ICD10_code_context(self) -> FunctionTool:

        async def get_ICD10_code_context(_: ToolContext, info: dict) -> dict:

            if isinstance(info, str):
                info = json.loads(info)
            icd10_context = ''
            for code in info['icd10_codes'].split(';'):
                context_to_add = self.icd_10_code_df[self.icd_10_code_df['CODE'] == code]['LONG DESCRIPTION (VALID ICD-10 FY2026)'].to_string(index=False)
                icd10_context += context_to_add if len(context_to_add) > 1 else ''
            return icd10_context

        return FunctionTool(
            name="get_ICD10_code_context",
            description="Get context for why the procedure was performed.",
            on_invoke_tool=get_ICD10_code_context,
            params_json_schema={
                "type": "object",
                "properties": {
                    "icd10_codes": {"type": "string", "description": "the ICD-10 code field for the claim"}
                },
                "required": ["icd10_codes"],
                "additionalProperties": False,
            },
        )
    def _gather_CPT_code_context(self) -> FunctionTool:

        async def get_CPT_code_context(_: ToolContext, info: dict) -> dict:

            if isinstance(info, str):
                info = json.loads(info)
            cpt_context = ''
            for code in info['cpt_codes'].split(';'):
                context_to_add = self.cpt_code_df[self.cpt_code_df['CODE'] == code]['DEFINITION'].to_string(index=False)
                cpt_context += context_to_add if len(context_to_add) > 1 else ''
            return cpt_context

        return FunctionTool(
            name="get_CPT_code_context",
            description="Get context for which procedure was performed.",
            on_invoke_tool=get_CPT_code_context,
            params_json_schema={
                "type": "object",
                "properties": {
                    "cpt_codes": {"type": "string", "description": "the CPT code field for the claim"}
                },
                "required": ["cpt_codes"],
                "additionalProperties": False,
            },
        )
    async def run(self, prompt: str, ask: bool = False):
        """
        Send prompt to agent (claim workup or Q&A mode).

        Parameters
        ----------
        prompt : str
            User message/claim dict string
        ask : bool
            Use Question Agent (history-based Q&A) vs Claim Agent (workup)

        Returns
        -------
        Agent result object
        """
        for attempt in range(5):
            try:
                if ask:
                    result = await Runner.run(self.question_agent, prompt, session=self.session)
                else:
                    result = await Runner.run(self.agent, prompt, session=self.session)
                return result
            except Exception as e:
                print('Model error:', e)
                prompt = 'The previous JSON output failed due to {e}, please fix' + prompt
            
