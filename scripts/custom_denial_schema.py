"""
CustomDenialSchema Class
========================
Custom output schema for agent responses. Loads JSON schema from file and provides
validation for structured claim denial workup output (claim_id, denial_taxonomy, etc.).
"""
import json
from typing import Any
from agents.agent_output import AgentOutputSchemaBase

class CustomDenialSchema(AgentOutputSchemaBase):
    def __init__(self):
        # Load your schema file
        with open("docs/workup_output_schema.json", "r") as f:
            self._schema = json.load(f)
    
    def is_plain_text(self) -> bool:
        return False  # We want JSON output, not plain text
    
    def is_strict_json_schema(self) -> bool:
        return False  # Your schema has advanced features (null unions, etc.) not in strict mode
    
    def name(self) -> str:
        return "DenialWorkupOutput"  # Human-readable name for the output type
    
    def json_schema(self) -> dict[str, Any]:
        return self._schema  # Returns your exact raw schema
    
    def validate_json(self, json_str: str) -> dict[str, Any]:
        try:
            result = json.loads(json_str)
            # Basic validation: check required top-level keys from your schema
            required = {
                "claim_id", "denial_taxonomy", "payment_analysis", "pursuit_recommendation", 
                "reasons", "missing_fields", "open_questions", "recommended_next_steps", 
                "supporting_playbook_citations", "draft_narrative", "trace"
            }
            if not all(key in result for key in required):
                raise ValueError("Missing required fields")
            return result  # Return as dict (no further typing)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")  # Use ValueError
        except Exception as e:
            raise ValueError(f"Validation failed: {e}")
