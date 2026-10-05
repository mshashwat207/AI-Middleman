import asyncio
import json
import csv
import argparse
from pathlib import Path

# Need to set up environment for FastAPI context if running directly
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.routes.benchmark import _run_pipeline
from app.core.config import settings

async def run_batch(input_csv: str, output_csv: str, provider: str, model: str):
    print(f"Starting batch job: {input_csv} -> {output_csv}")
    print(f"Provider: {provider} | Model: {model}")
    
    results = []
    
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompt_id = row.get("id", "unknown")
            prompt_text = row.get("text", "")
            
            if not prompt_text:
                continue
                
            print(f"Processing prompt {prompt_id}...")
            
            try:
                response = await _run_pipeline(
                    prompt=prompt_text,
                    provider=provider,
                    model_name=model,
                    temperature=0.7
                )
                
                # Extract results
                r_redact = next(r for r in response.results if r.method == "Hard Redaction")
                r_token = next(r for r in response.results if r.method == "Categorical Tokenization")
                r_synth = next(r for r in response.results if r.method == "Synthetic Swapping")
                
                results.append({
                    "id": prompt_id,
                    "provider": response.provider_used,
                    "model": response.model_used,
                    "latency_ms": response.total_latency_ms,
                    "pii_entities_found": r_redact.entities_found,
                    "redact_utility": r_redact.utility_score,
                    "token_utility": r_token.utility_score,
                    "synth_utility": r_synth.utility_score,
                })
            except Exception as e:
                print(f"Error processing prompt {prompt_id}: {e}")
                
    if results:
        keys = results[0].keys()
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        print(f"Batch completed! Saved {len(results)} rows to {output_csv}")
    else:
        print("No results to save.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run VUL-LLM Benchmark in Batch")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file (must have 'id' and 'text' columns)")
    parser.add_argument("--output", type=str, required=True, help="Output CSV file")
    parser.add_argument("--provider", type=str, default="mock", help="LLM Provider (e.g. groq, openai, mock)")
    parser.add_argument("--model", type=str, default="", help="Model name (e.g. openai/gpt-oss-20b)")
    
    args = parser.parse_args()
    asyncio.run(run_batch(args.input, args.output, args.provider, args.model))
