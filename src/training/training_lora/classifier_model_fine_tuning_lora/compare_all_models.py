#!/usr/bin/env python3
"""
Three-way model comparison:
1. Old (deployed) vs Snapshot1 (v1)
2. Old (deployed) vs V2 (maximum effort)
3. Snapshot1 (v1) vs V2 (maximum effort)
"""

import json
import os
import sys
from pathlib import Path

# Import from comprehensive_test
sys.path.insert(0, os.path.dirname(__file__))
from comprehensive_test import TEST_SET, load_model, evaluate_model

def print_comparison(name1, name2, results1, results2):
    """Print comparison between two models."""
    print("\n" + "=" * 80)
    print(f"COMPARISON: {name1} vs {name2}")
    print("=" * 80)
    
    clean_delta = results2["clean_accuracy"] - results1["clean_accuracy"]
    typo_delta = results2["typo_accuracy"] - results1["typo_accuracy"]
    
    print(f"\n{'Metric':<25} {name1:<15} {name2:<15} {'Delta':<10}")
    print("-" * 65)
    print(f"{'Clean Accuracy':<25} {results1['clean_accuracy']:.1f}%{'':<10} {results2['clean_accuracy']:.1f}%{'':<10} {clean_delta:+.1f}%")
    print(f"{'Typo Accuracy':<25} {results1['typo_accuracy']:.1f}%{'':<10} {results2['typo_accuracy']:.1f}%{'':<10} {typo_delta:+.1f}%")
    print(f"{'Avg Clean Confidence':<25} {results1['avg_clean_conf']:.3f}{'':<12} {results2['avg_clean_conf']:.3f}")
    print(f"{'Avg Typo Confidence':<25} {results1['avg_typo_conf']:.3f}{'':<12} {results2['avg_typo_conf']:.3f}")
    
    print(f"\nSamples: {results1['total']}")
    print(f"{name1}: {results1['clean_correct']}/{results1['total']} clean, {results1['typo_correct']}/{results1['total']} typo")
    print(f"{name2}: {results2['clean_correct']}/{results2['total']} clean, {results2['typo_correct']}/{results2['total']} typo")
    
    # Winner determination
    if clean_delta > 0 and typo_delta > 0:
        print(f"\n✅ {name2} is BETTER on both metrics")
    elif clean_delta < 0 and typo_delta < 0:
        print(f"\n✅ {name1} is BETTER on both metrics")
    elif typo_delta > 5 and clean_delta >= -2:
        print(f"\n✅ {name2} is BETTER (strong typo improvement, minimal clean regression)")
    elif clean_delta > 2 and typo_delta >= -5:
        print(f"\n✅ {name2} is BETTER (strong clean improvement, acceptable typo change)")
    else:
        print(f"\n⚠️  MIXED RESULTS - need to decide based on priority")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Three-way model comparison")
    parser.add_argument("--old-model", required=True, help="Path to old (deployed) model")
    parser.add_argument("--snapshot1", required=True, help="Path to snapshot1 (v1) model")
    parser.add_argument("--v2-model", required=True, help="Path to v2 (maximum effort) model")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("THREE-WAY MODEL COMPARISON")
    print("=" * 80)
    print(f"Test set size: {len(TEST_SET)} samples")
    print("\nModels:")
    print(f"  1. OLD (deployed): {args.old_model}")
    print(f"  2. SNAPSHOT1 (v1): {args.snapshot1}")
    print(f"  3. V2 (maximum effort): {args.v2_model}")
    
    # Load all models
    print("\n" + "=" * 80)
    print("Loading models...")
    print("=" * 80)
    
    print("\nLoading OLD model...")
    old_model, old_tok, old_labels = load_model(args.old_model)
    
    print("Loading SNAPSHOT1 (v1) model...")
    v1_model, v1_tok, v1_labels = load_model(args.snapshot1)
    
    print("Loading V2 model...")
    v2_model, v2_tok, v2_labels = load_model(args.v2_model)
    
    # Evaluate all models
    print("\n" + "=" * 80)
    print("Evaluating models...")
    print("=" * 80)
    
    print("\nEvaluating OLD model...")
    old_results = evaluate_model(old_model, old_tok, old_labels, TEST_SET)
    
    print("Evaluating SNAPSHOT1 (v1) model...")
    v1_results = evaluate_model(v1_model, v1_tok, v1_labels, TEST_SET)
    
    print("Evaluating V2 model...")
    v2_results = evaluate_model(v2_model, v2_tok, v2_labels, TEST_SET)
    
    # Print all comparisons
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    
    # 1. Old vs Snapshot1 (v1)
    print_comparison("OLD (deployed)", "SNAPSHOT1 (v1)", old_results, v1_results)
    
    # 2. Old vs V2
    print_comparison("OLD (deployed)", "V2 (maximum effort)", old_results, v2_results)
    
    # 3. Snapshot1 (v1) vs V2
    print_comparison("SNAPSHOT1 (v1)", "V2 (maximum effort)", v1_results, v2_results)
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    print("\nImprovements over OLD (deployed) model:")
    v1_clean_improve = v1_results["clean_accuracy"] - old_results["clean_accuracy"]
    v1_typo_improve = v1_results["typo_accuracy"] - old_results["typo_accuracy"]
    v2_clean_improve = v2_results["clean_accuracy"] - old_results["clean_accuracy"]
    v2_typo_improve = v2_results["typo_accuracy"] - old_results["typo_accuracy"]
    
    print(f"\n  SNAPSHOT1 (v1):")
    print(f"    Clean: {old_results['clean_accuracy']:.1f}% → {v1_results['clean_accuracy']:.1f}% ({v1_clean_improve:+.1f}%)")
    print(f"    Typo:  {old_results['typo_accuracy']:.1f}% → {v1_results['typo_accuracy']:.1f}% ({v1_typo_improve:+.1f}%)")
    
    print(f"\n  V2 (maximum effort):")
    print(f"    Clean: {old_results['clean_accuracy']:.1f}% → {v2_results['clean_accuracy']:.1f}% ({v2_clean_improve:+.1f}%)")
    print(f"    Typo:  {old_results['typo_accuracy']:.1f}% → {v2_results['typo_accuracy']:.1f}% ({v2_typo_improve:+.1f}%)")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    # Determine best model
    v1_total_improve = v1_clean_improve + v1_typo_improve
    v2_total_improve = v2_clean_improve + v2_typo_improve
    
    if v2_total_improve > v1_total_improve and v2_results["clean_accuracy"] >= v1_results["clean_accuracy"] - 2:
        print("\n✅ RECOMMENDATION: Use V2 (maximum effort) model")
        print("   - Better overall improvement")
        print("   - Acceptable clean accuracy")
    elif v1_total_improve > v2_total_improve or v2_results["clean_accuracy"] < v1_results["clean_accuracy"] - 5:
        print("\n✅ RECOMMENDATION: Use SNAPSHOT1 (v1) model")
        print("   - Better balance or V2 regressed on clean accuracy")
    else:
        print("\n⚠️  RECOMMENDATION: Both models are similar")
        print("   - Choose based on specific requirements")
        print("   - V2 has more training, V1 is more conservative")


if __name__ == "__main__":
    main()

