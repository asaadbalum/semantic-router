#!/usr/bin/env python3
"""
Compare old and new models on typo robustness.
Evaluates both models on clean and typo-laden test prompts.

Usage:
    python compare_models.py --old-model ../../../models/mom-domain-classifier --new-model ./lora_intent_classifier_bert-base-uncased_r16_model_rust
"""

import argparse
import json
import os
import random
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Test cases: (text, expected_category, has_typos)
TEST_CASES = [
    # Clean math prompts
    ("Please solve the following mathematical problem step by step", "math", False),
    ("What is the derivative of x squared plus 3x", "math", False),
    ("Calculate the integral of sin(x) from 0 to pi", "math", False),
    
    # Typo math prompts (the bug we're fixing)
    ("Plese slove the follwing mathemtical prblem step by step", "math", True),
    ("Waht is teh derivtive of x squred plus 3x", "math", True),
    ("Calclate the intgral of sin(x) frm 0 to pi", "math", True),
    
    # Clean chemistry prompts
    ("What is the molecular structure of benzene", "chemistry", False),
    ("Explain the process of oxidation reduction", "chemistry", False),
    
    # Typo chemistry prompts
    ("Waht is teh molcular strcture of benzne", "chemistry", True),
    ("Expalin the procss of oxidtion reducton", "chemistry", True),
    
    # Clean physics prompts
    ("Calculate the velocity of an object in free fall", "physics", False),
    ("Explain Newton's laws of motion", "physics", False),
    
    # Typo physics prompts
    ("Calclate the velocty of an objct in fre fall", "physics", True),
    ("Expalin Newtons laws of moton", "physics", True),
    
    # Clean biology prompts
    ("Describe the process of cellular respiration", "biology", False),
    ("What is the structure of DNA", "biology", False),
    
    # Typo biology prompts
    ("Descrbe the procss of celluar respiraton", "biology", True),
    ("Waht is the strcture of DNA", "biology", True),
]


def load_model(model_path):
    """Load model and tokenizer from path."""
    # Convert to absolute path for local files
    model_path = os.path.abspath(model_path)
    print(f"Loading model from: {model_path}")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model path does not exist: {model_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)
    
    # Load label mapping
    label_map_path = os.path.join(model_path, "label_mapping.json")
    if not os.path.exists(label_map_path):
        label_map_path = os.path.join(model_path, "category_mapping.json")
    
    with open(label_map_path, "r") as f:
        label_mapping = json.load(f)
    
    # Get idx_to_category mapping
    if "idx_to_category" in label_mapping:
        idx_to_label = {int(k): v for k, v in label_mapping["idx_to_category"].items()}
    elif "idx_to_label" in label_mapping:
        idx_to_label = {int(k): v for k, v in label_mapping["idx_to_label"].items()}
    else:
        # Try to get from model config
        idx_to_label = model.config.id2label
    
    return model, tokenizer, idx_to_label


def predict(model, tokenizer, text, idx_to_label, device="cpu"):
    """Make a prediction."""
    model.eval()
    model.to(device)
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        confidence, pred_idx = torch.max(probs, dim=-1)
    
    pred_label = idx_to_label.get(pred_idx.item(), "unknown")
    return pred_label, confidence.item()


def evaluate_model(model, tokenizer, idx_to_label, test_cases, device="cpu"):
    """Evaluate model on test cases."""
    results = {
        "clean_correct": 0,
        "clean_total": 0,
        "typo_correct": 0,
        "typo_total": 0,
        "details": []
    }
    
    for text, expected, has_typos in test_cases:
        pred_label, confidence = predict(model, tokenizer, text, idx_to_label, device)
        is_correct = pred_label.lower() == expected.lower()
        
        if has_typos:
            results["typo_total"] += 1
            if is_correct:
                results["typo_correct"] += 1
        else:
            results["clean_total"] += 1
            if is_correct:
                results["clean_correct"] += 1
        
        results["details"].append({
            "text": text[:50] + "...",
            "expected": expected,
            "predicted": pred_label,
            "confidence": confidence,
            "has_typos": has_typos,
            "correct": is_correct
        })
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Compare old and new models")
    parser.add_argument("--old-model", type=str, required=True, help="Path to old model")
    parser.add_argument("--new-model", type=str, required=True, help="Path to new model")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use")
    args = parser.parse_args()
    
    print("=" * 70)
    print("MODEL COMPARISON: Typo Robustness Evaluation")
    print("=" * 70)
    
    # Load models
    print("\nLoading models...")
    old_model, old_tokenizer, old_labels = load_model(args.old_model)
    new_model, new_tokenizer, new_labels = load_model(args.new_model)
    
    # Evaluate
    print("\nEvaluating old model...")
    old_results = evaluate_model(old_model, old_tokenizer, old_labels, TEST_CASES, args.device)
    
    print("Evaluating new model...")
    new_results = evaluate_model(new_model, new_tokenizer, new_labels, TEST_CASES, args.device)
    
    # Print results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    print("\n📊 ACCURACY COMPARISON:")
    print("-" * 50)
    
    old_clean_acc = old_results["clean_correct"] / old_results["clean_total"] * 100
    old_typo_acc = old_results["typo_correct"] / old_results["typo_total"] * 100
    new_clean_acc = new_results["clean_correct"] / new_results["clean_total"] * 100
    new_typo_acc = new_results["typo_correct"] / new_results["typo_total"] * 100
    
    print(f"{'Metric':<25} {'Old Model':<15} {'New Model':<15} {'Diff':<10}")
    print("-" * 65)
    print(f"{'Clean Text Accuracy':<25} {old_clean_acc:>12.1f}% {new_clean_acc:>12.1f}% {new_clean_acc - old_clean_acc:>+8.1f}%")
    print(f"{'Typo Text Accuracy':<25} {old_typo_acc:>12.1f}% {new_typo_acc:>12.1f}% {new_typo_acc - old_typo_acc:>+8.1f}%")
    
    print("\n📋 DETAILED RESULTS (Typo prompts only):")
    print("-" * 70)
    
    for i, (old_detail, new_detail) in enumerate(zip(old_results["details"], new_results["details"])):
        if old_detail["has_typos"]:
            old_status = "✅" if old_detail["correct"] else "❌"
            new_status = "✅" if new_detail["correct"] else "❌"
            print(f"\nPrompt: {old_detail['text']}")
            print(f"  Expected: {old_detail['expected']}")
            print(f"  Old: {old_status} {old_detail['predicted']} ({old_detail['confidence']:.2f})")
            print(f"  New: {new_status} {new_detail['predicted']} ({new_detail['confidence']:.2f})")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if new_typo_acc > old_typo_acc and new_clean_acc >= old_clean_acc - 5:
        print("✅ NEW MODEL IS BETTER: Improved typo robustness without sacrificing clean accuracy")
        print("   RECOMMENDATION: Deploy the new model")
    elif new_typo_acc > old_typo_acc and new_clean_acc < old_clean_acc - 5:
        print("⚠️  TRADE-OFF: Better typo handling but worse clean accuracy")
        print("   RECOMMENDATION: Review carefully before deploying")
    elif new_typo_acc <= old_typo_acc:
        print("❌ NO IMPROVEMENT: New model is not better at handling typos")
        print("   RECOMMENDATION: Do NOT deploy, investigate training")
    
    print("=" * 70)


if __name__ == "__main__":
    main()

