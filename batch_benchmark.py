import csv
import json
import time
import argparse
import asyncio
from pathlib import Path

# Adjust imports to use your FastAPI backend logic directly
# We must run this from the backend directory or add it to PYTHONPATH
import sys
sys.path.append("backend")

from app.api.routes.benchmark import _run_pipeline

async def run_batch(input_csv: str, output_json: str, provider: str, enforce_firewall: bool, k_threshold: int):
    results = []
    
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    print(f"Starting batch processing of {len(rows)} prompts using provider '{provider}'...")
    print(f"Firewall Enforcement: {enforce_firewall} | K-Threshold: {k_threshold}")
    
    for i, row in enumerate(rows):
        prompt = row.get("prompt") or row.get("text")
        if not prompt:
            print(f"Row {i+1}: Skipped (no 'prompt' or 'text' column)")
            continue
            
        print(f"Processing row {i+1}/{len(rows)}...")
        try:
            # We run the pipeline directly, bypassing HTTP overhead
            response = await _run_pipeline(
                prompt=prompt,
                provider=provider,
                model_name=None,
                temperature=0.0,  # 0.0 for deterministic benchmarking
                enforce_firewall=enforce_firewall,
                k_threshold=k_threshold
            )
            
            # Extract utility scores
            scores = {r.method: r.utility_score for r in response.results}
            results.append({
                "row": i + 1,
                "original": prompt,
                "blocked": not response.firewall.passed,
                "k_anonymity_warnings": len(response.indirect_pii_warnings),
                "scores": scores
            })
            
        except Exception as e:
            # Catch 403 blocks from the firewall
            if "403" in str(e) or "Privacy policy violation" in str(e):
                print(f" -> Blocked by Firewall!")
                results.append({
                    "row": i + 1,
                    "original": prompt,
                    "blocked": True,
                    "k_anonymity_warnings": k_threshold,
                    "scores": None
                })
            else:
                print(f" -> Error: {e}")
                
        # Sleep to respect free-tier API rate limits (e.g. Gemini 15 RPM)
        if provider != "mock":
            time.sleep(4)
        
    # Aggregate statistics
    successful = [r for r in results if not r["blocked"]]
    if successful:
        avg_hard = sum(r["scores"]["Hard Redaction"] for r in successful) / len(successful)
        avg_cat = sum(r["scores"]["Categorical Tokenization"] for r in successful) / len(successful)
        avg_syn = sum(r["scores"]["Synthetic Swapping"] for r in successful) / len(successful)
        
        print("\n--- BATCH RESULTS ---")
        print(f"Total Processed: {len(results)}")
        print(f"Blocked by Firewall: {len(results) - len(successful)}")
        print("Average Utility Scores (for allowed prompts):")
        print(f" - Hard Redaction: {avg_hard:.2f}")
        print(f" - Categorical Tokenization: {avg_cat:.2f}")
        print(f" - Synthetic Swapping: {avg_syn:.2f}")
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved detailed results to {output_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run VUL-LLM Benchmarks in Batch via CSV")
    parser.add_argument("input_csv", help="Path to input CSV (must have a 'prompt' column)")
    parser.add_argument("--output", default="batch_results.json", help="Output JSON file")
    parser.add_argument("--provider", default="gemini", help="LLM Provider to use")
    parser.add_argument("--enforce-firewall", action="store_true", help="Turn on strict blocking")
    parser.add_argument("--k-threshold", type=int, default=3, help="K-Anonymity density limit")
    
    args = parser.parse_args()
    
    asyncio.run(run_batch(args.input_csv, args.output, args.provider, args.enforce_firewall, args.k_threshold))
