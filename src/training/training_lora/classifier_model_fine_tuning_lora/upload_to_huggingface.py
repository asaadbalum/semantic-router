#!/usr/bin/env python3
"""
Upload snapshot1 (v1) model to HuggingFace

Requirements:
1. Install: pip install huggingface_hub
2. Login: huggingface-cli login (or set HF_TOKEN env var)
3. Have write access to LLM-Semantic-Router organization

Usage:
    python upload_to_huggingface.py --model-path ../../../../models/mom-domain-classifier-new --repo-id LLM-Semantic-Router/mom-domain-classifier-v1-typo-robust
"""

import argparse
import os
from pathlib import Path
from huggingface_hub import HfApi, create_repo
from huggingface_hub.utils import HfHubHTTPError


def upload_model(model_path: str, repo_id: str, private: bool = False):
    """Upload model to HuggingFace."""
    api = HfApi()
    model_path = Path(model_path).resolve()
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model path does not exist: {model_path}")
    
    print(f"Uploading model from: {model_path}")
    print(f"To HuggingFace: {repo_id}")
    print(f"Private: {private}")
    print()
    
    # Check required files
    required_files = [
        "config.json",
        "model.safetensors",
        "category_mapping.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.txt"
    ]
    
    missing = [f for f in required_files if not (model_path / f).exists()]
    if missing:
        print(f"⚠️  Warning: Missing files: {missing}")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Create repo if it doesn't exist
    try:
        repo_info = api.repo_info(repo_id, repo_type="model")
        print(f"✅ Repository exists: {repo_id}")
    except HfHubHTTPError as e:
        if e.response.status_code == 404:
            print(f"Creating repository: {repo_id}")
            create_repo(repo_id, repo_type="model", private=private, exist_ok=False)
            print(f"✅ Repository created")
        else:
            raise
    
    # Upload all files
    print("\nUploading files...")
    api.upload_folder(
        folder_path=str(model_path),
        repo_id=repo_id,
        repo_type="model",
        ignore_patterns=[".git*", "*.lock", "*.metadata"]
    )
    
    print(f"\n✅ Model uploaded successfully!")
    print(f"   View at: https://huggingface.co/{repo_id}")
    print(f"\nTo use in config.yaml:")
    print(f'   model_id: "{repo_id}"')
    print(f'   # Or use local path: "models/mom-domain-classifier-new"')


def main():
    parser = argparse.ArgumentParser(description="Upload model to HuggingFace")
    parser.add_argument(
        "--model-path",
        required=True,
        help="Path to model directory (e.g., ../../../../models/mom-domain-classifier-new)"
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="HuggingFace repo ID (e.g., LLM-Semantic-Router/mom-domain-classifier-v1-typo-robust)"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Make repository private"
    )
    
    args = parser.parse_args()
    
    # Check if logged in
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
    if not token:
        print("⚠️  No HF_TOKEN or HUGGINGFACE_HUB_TOKEN found")
        print("   Run: huggingface-cli login")
        print("   Or set: export HF_TOKEN=your_token")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    upload_model(args.model_path, args.repo_id, args.private)


if __name__ == "__main__":
    main()

