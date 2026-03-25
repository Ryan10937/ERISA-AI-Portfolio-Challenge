"""
Main CLI for ERISA claim denial workup agent.

Usage:
    python -m scripts.main workup --claim-id C-CO45-001 --session-id demo_01
    python -m scripts.main ask --session-id demo_01 --message "Why did you recommend that?"
"""
import asyncio
import argparse
import sys
from pathlib import Path
from pprint import pprint

import pandas as pd
from ollama_responses_agent import OllamaResponsesAgent
from pandas import read_csv

async def run_workup(agent: OllamaResponsesAgent, claim_id: str, session_id: str):
    """Process single claim by ID."""
    claims_df = read_csv('data/claims.csv')
    
    claim_row = claims_df[claims_df['claim_id'] == claim_id]
    if claim_row.empty:
        print(f"Claim {claim_id} not found!")
        return
    
    claim_dict = claim_row.iloc[0].to_dict()
    print(f"Processing claim {claim_id}...")
    
    result = await agent.run(str(claim_dict))
    print(f"\nResult for {claim_id}:")
    pprint(result.final_output)
    
    print(f"\nSaved to session: {session_id}")

async def run_ask(agent: OllamaResponsesAgent, message: str, session_id: str):
    """Ask question about existing session."""
    print(f"Asking: {message}")
    
    result = await agent.run(message, ask=True)
    print(f"\nResponse:")
    print(result.final_output)
    
    print(f"\nSaved to session: {session_id}")

def main():
    parser = argparse.ArgumentParser(description="ERISA Claim Denial Workup Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Workup command
    workup_parser = subparsers.add_parser("workup", help="Process a claim")
    workup_parser.add_argument("--claim-id", "-c", required=True, help="Claim ID (e.g. C-CO45-001)")
    workup_parser.add_argument("--session-id", "-s", required=True, help="Session ID (e.g. demo_01)")
    
    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask question about session")
    ask_parser.add_argument("--session-id", "-s", required=True, help="Session ID (e.g. demo_01)")
    ask_parser.add_argument("--message", "-m", required=True, help="Question to ask")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Override session ID in agent init for consistency
    agent = OllamaResponsesAgent(sqlite_path=f"database/agentic.db",session_id=args.session_id)
    
    if args.command == "workup":
        asyncio.run(run_workup(agent, args.claim_id, args.session_id))
    elif args.command == "ask":
        asyncio.run(run_ask(agent, args.message, args.session_id))

if __name__ == "__main__":
    main()
