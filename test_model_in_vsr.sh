#!/bin/bash
# Test the new model in actual VSR environment
# This verifies the model works correctly with the Rust candle-binding

set -e

MODEL_PATH="${1:-src/training/training_lora/classifier_model_fine_tuning_lora/consistency_classifier_bert-base-uncased_r16_rust}"

echo "=========================================="
echo "VSR Model Integration Test"
echo "=========================================="
echo "Model: $MODEL_PATH"
echo ""

# Check if model exists
if [ ! -d "$MODEL_PATH" ]; then
    echo "❌ Model not found: $MODEL_PATH"
    exit 1
fi

# Check required files
echo "Checking model files..."
REQUIRED_FILES=("config.json" "model.safetensors" "category_mapping.json" "tokenizer.json")
MISSING=0

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$MODEL_PATH/$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo "❌ Model is incomplete"
    exit 1
fi

echo ""
echo "=========================================="
echo "Model Structure Check"
echo "=========================================="

# Check category count
if [ -f "$MODEL_PATH/category_mapping.json" ]; then
    CATEGORY_COUNT=$(python3 << EOF
import json
with open("$MODEL_PATH/category_mapping.json") as f:
    data = json.load(f)
    if "idx_to_category" in data:
        print(len(data["idx_to_category"]))
    else:
        print("unknown")
EOF
)
    echo "Categories: $CATEGORY_COUNT (expected: 14)"
fi

# Check model size
if [ -f "$MODEL_PATH/model.safetensors" ]; then
    SIZE=$(du -h "$MODEL_PATH/model.safetensors" | cut -f1)
    echo "Model size: $SIZE"
fi

echo ""
echo "=========================================="
echo "Next Steps for VSR Integration"
echo "=========================================="
echo "1. Copy model to VSR models directory:"
echo "   cp -r $MODEL_PATH models/mom-domain-classifier-new"
echo ""
echo "2. Update config/config.yaml:"
echo "   classifier:"
echo "     category_model:"
echo "       model_path: models/mom-domain-classifier-new"
echo ""
echo "3. Test with curl:"
echo "   curl http://localhost:8080/api/v1/classify/intent \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"text\": \"Please solve this math problem\"}'"
echo ""
echo "4. Test with typo:"
echo "   curl http://localhost:8080/api/v1/classify/intent \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"text\": \"Plese slove this math prblem\"}'"
echo ""

