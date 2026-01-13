#!/usr/bin/env python3
"""
Test script to verify typo robustness of trained models.
Run this after training to validate the model handles misspellings correctly.

Usage:
    python test_typo_robustness.py --model-path ./multitask_bert_model

Issue: #967 - Classification inconsistency with spelling errors
"""

import argparse
import json
import os
import torch
from transformers import AutoModel, AutoTokenizer


def load_model(model_path):
    """Load the trained multitask model."""
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    # Load config
    with open(os.path.join(model_path, "task_configs.json"), "r") as f:
        task_configs = json.load(f)
    
    with open(os.path.join(model_path, "label_mappings.json"), "r") as f:
        label_mappings = json.load(f)
    
    return tokenizer, task_configs, label_mappings


def classify_text(text, tokenizer, model, task_name, label_mapping, device):
    """Classify a single text."""
    encoding = tokenizer(
        text,
        truncation=True,
        padding="max_length",
        max_length=512,
        return_tensors="pt",
    )
    
    with torch.no_grad():
        input_ids = encoding["input_ids"].to(device)
        attention_mask = encoding["attention_mask"].to(device)
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        
        logits = outputs[task_name]
        probs = torch.softmax(logits, dim=-1)
        confidence, predicted_idx = torch.max(probs, dim=-1)
    
    idx_to_label = label_mapping.get("idx_to_label", {})
    predicted_label = idx_to_label.get(str(predicted_idx.item()), "Unknown")
    
    return predicted_label, confidence.item()


# Test cases: (clean_text, typo_text, expected_category)
CATEGORY_TEST_CASES = [
    # Math
    (
        "Please solve the following mathematical problem step by step",
        "Plese slove the follwing mathemtical prblem step by step",
        "Mathematics"
    ),
    (
        "What is the derivative of x squared plus 3x",
        "Waht is teh derivtive of x squred plus 3x",
        "Mathematics"
    ),
    # Science
    (
        "Explain the process of photosynthesis in plants",
        "Expalin the proccess of photsynthesis in plnats",
        "Science"
    ),
    (
        "What is the chemical formula for water",
        "Waht is teh chemcial formla for wter",
        "Science"
    ),
    # Technology
    (
        "How do machine learning algorithms work",
        "How do machien lerning algortihms wrk",
        "Technology"
    ),
    # History
    (
        "What were the causes of World War II",
        "Waht were teh casues of Wrold War II",
        "History"
    ),
]

PII_TEST_CASES = [
    # Names
    (
        "My name is John Smith and I live in New York",
        "My nmae is Jonh Smtih and I liev in New Yrok",
        "PERSON"  # Should still detect as PII
    ),
    # Emails
    (
        "Contact me at john.smith@email.com",
        "Contcat me at jonh.smtih@email.com",
        "EMAIL"  # Should still detect as PII
    ),
]


def main():
    parser = argparse.ArgumentParser(description="Test typo robustness")
    parser.add_argument("--model-path", type=str, default="./multitask_bert_model",
                        help="Path to trained model")
    args = parser.parse_args()
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # For now, just print the test cases
    # Full implementation requires loading the MultitaskBertModel class
    print("\n" + "=" * 60)
    print("TYPO ROBUSTNESS TEST CASES")
    print("=" * 60)
    
    print("\n📚 CATEGORY CLASSIFICATION TESTS:")
    for clean, typo, expected in CATEGORY_TEST_CASES:
        print(f"\n  Clean: {clean[:50]}...")
        print(f"  Typo:  {typo[:50]}...")
        print(f"  Expected: {expected}")
    
    print("\n\n🔒 PII DETECTION TESTS:")
    for clean, typo, expected in PII_TEST_CASES:
        print(f"\n  Clean: {clean[:50]}...")
        print(f"  Typo:  {typo[:50]}...")
        print(f"  Expected: {expected}")
    
    print("\n" + "=" * 60)
    print("To run full tests, load the model and run classification")
    print("=" * 60)


if __name__ == "__main__":
    main()

