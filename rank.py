import json
import csv
import time
import argparse
import sys
from candidate_parser import extract_features
from ranker import calculate_structured_score, calculate_behavior_multiplier, generate_reasoning

def main():
    parser = argparse.ArgumentParser(description="Redrob hackathon ranker")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--out", required=True, help="Path to output submission CSV")
    args = parser.parse_args()

    print(f"Starting ranking process...")
    print(f"Reading candidates from: {args.candidates}")
    print(f"Output will be saved to: {args.out}")

    start_time = time.time()
    
    total_count = 0
    honeypot_count = 0
    disqualified_count = 0
    valid_candidates = []

    # Read candidates line-by-line
    with open(args.candidates, "r", encoding="utf-8") as f:
        for line in f:
            total_count += 1
            if total_count % 10000 == 0:
                print(f"Processed {total_count} candidates...")
                
            try:
                cand = json.loads(line)
            except Exception as e:
                print(f"Error parsing line {total_count}: {e}")
                continue

            # Extract features and perform screening checks
            features = extract_features(cand)
            
            if features["is_honeypot"]:
                honeypot_count += 1
                continue
                
            if features["is_disqualified"]:
                disqualified_count += 1
                continue
                
            # Score valid candidate
            raw_score = calculate_structured_score(features)
            multiplier = calculate_behavior_multiplier(features)
            final_score = round(raw_score * multiplier, 3)
            
            valid_candidates.append({
                "candidate_id": features["candidate_id"],
                "score": final_score,
                "features": features
            })

    print(f"\nScanning completed in {time.time() - start_time:.2f} seconds.")
    print(f"Total candidates scanned: {total_count}")
    print(f"Honeypots filtered out: {honeypot_count}")
    print(f"Disqualified candidates filtered out: {disqualified_count}")
    print(f"Valid candidates remaining: {len(valid_candidates)}")

    # Sort candidates by score descending, then candidate_id ascending for deterministic tie-breaking
    print("Sorting candidates...")
    valid_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))

    # Select top 100 candidates
    top_100 = valid_candidates[:100]
    print(f"Top candidate score: {top_100[0]['score']}")
    print(f"100th candidate score: {top_100[-1]['score']}")

    # Write output to CSV (ensuring exactly 101 lines in the file)
    print(f"Writing top 100 to {args.out}...")
    import io
    output_buffer = io.StringIO()
    writer = csv.writer(output_buffer, lineterminator="\n")
    writer.writerow(["candidate_id", "rank", "score", "reasoning"])
    
    for i, cand in enumerate(top_100):
        rank = i + 1
        reasoning = generate_reasoning(cand["features"])
        writer.writerow([cand["candidate_id"], rank, cand["score"], reasoning])
        
    csv_content = output_buffer.getvalue().rstrip("\r\n")
    with open(args.out, "w", encoding="utf-8", newline="") as out_f:
        out_f.write(csv_content)

    print("Ranking pipeline completed successfully.")

if __name__ == "__main__":
    main()
