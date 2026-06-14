#!/usr/bin/env python3
"""
Bayesian Optimizer — Beta-Bernoulli update from execution_audit.csv.

Reads the audit log, applies a Bayesian update to planet weights,
and writes the result to ephe/weights_optimized.json (baseline untouched).

Usage:
    python optimizer.py
    python mazz.py optimize
"""

import pandas as pd
import json
import os

AUDIT_LOG = os.path.join("Mazzaroth_Engine_Data", "execution_audit.csv")
WEIGHTS_FILE = os.path.join("ephe", "weights.json")
OUTPUT_FILE = os.path.join("ephe", "weights_optimized.json")
MIN_ENTRIES = 10

def run_optimization():
    if not os.path.exists(AUDIT_LOG):
        print("Audit log not found. Run transits and rate outcomes first.")
        return

    audit = pd.read_csv(AUDIT_LOG)

    # Filter only rows with a rated outcome
    rated = audit[audit["outcome_score"].notna() & (audit["outcome_score"] != "")]
    n = len(rated)
    if n < MIN_ENTRIES:
        print(f"Only {n} audit entries (need {MIN_ENTRIES}+). No weight update yet.")
        return

    if not os.path.exists(WEIGHTS_FILE):
        print("weights.json not found in ephe/. Run the engine once first.")
        return

    with open(WEIGHTS_FILE) as f:
        weights = json.load(f)

    # Beta-Bernoulli update: outcome >= 4 is a "success"
    for _, row in rated.iterrows():
        outcome = int(row["outcome_score"])
        prob = outcome / 5.0

        planet = str(row["top_transit"]).split(" ")[0]
        if planet in weights:
            weights[planet] = (weights[planet] + prob) / 2
        else:
            # Try matching without prefixes (e.g. "Transiting Saturn" vs "Saturn")
            for key in weights:
                if key.lower() in planet.lower():
                    weights[key] = (weights[key] + prob) / 2
                    break

    with open(OUTPUT_FILE, "w") as f:
        json.dump(weights, f, indent=2)

    print(f"Optimized weights written to {OUTPUT_FILE} ({n} entries)")
    for p, w in sorted(weights.items(), key=lambda x: -x[1]):
        orig = json.load(open(WEIGHTS_FILE)).get(p, 0)
        delta = w - orig
        sign = "+" if delta >= 0 else ""
        print(f"  {p:10} {orig:5.1f} -> {w:5.1f} ({sign}{delta:.2f})")

if __name__ == "__main__":
    run_optimization()
