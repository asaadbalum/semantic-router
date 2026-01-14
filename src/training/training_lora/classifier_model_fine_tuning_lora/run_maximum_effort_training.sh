#!/bin/bash
# Maximum Effort Training - Target: 70%+ Typo Accuracy
# This script runs training with aggressive parameters while preserving snapshot1

set -e

echo "=========================================="
echo "Maximum Effort Training"
echo "Target: 70%+ Typo Accuracy"
echo "=========================================="
echo ""

# Check if snapshot1 exists
if [ ! -d "snapshot1_"* ] 2>/dev/null; then
    echo "⚠️  WARNING: No snapshot1 found!"
    echo "   Run ./create_snapshot1.sh first to save baseline"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Snapshot1 found (baseline preserved)"
fi

# Unique output directory to prevent overwriting
OUTPUT_DIR="consistency_classifier_v2_bert-base-uncased_r16"
echo "Output directory: $OUTPUT_DIR"
echo "   (This won't overwrite snapshot1 or existing models)"
echo ""

# Training parameters
EPOCHS=40
MAX_SAMPLES=40000
TYPO_PROB=0.40
CONSISTENCY_WEIGHT=2.5
LEARNING_RATE=2e-5
BATCH_SIZE=16

echo "Training Parameters:"
echo "  Epochs: $EPOCHS"
echo "  Max Samples: $MAX_SAMPLES"
echo "  Typo Probability: $TYPO_PROB"
echo "  Consistency Weight: $CONSISTENCY_WEIGHT"
echo "  Learning Rate: $LEARNING_RATE"
echo "  Batch Size: $BATCH_SIZE (4 GPUs = 64 effective)"
echo ""

# Estimate training time
echo "Estimated training time: ~2-3 hours on 4 GPUs"
echo ""

read -p "Start training? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Starting training..."
echo ""

# Run training with tmux to keep it alive
tmux new-session -d -s training_v2 "accelerate launch ft_linear_lora_consistency.py \
  --epochs $EPOCHS \
  --max-samples $MAX_SAMPLES \
  --typo-prob $TYPO_PROB \
  --consistency-weight $CONSISTENCY_WEIGHT \
  --learning-rate $LEARNING_RATE \
  --batch-size $BATCH_SIZE \
  --output-dir $OUTPUT_DIR 2>&1 | tee training_v2_output.txt"

echo "✅ Training started in tmux session 'training_v2'"
echo ""
echo "To monitor:"
echo "  tmux attach -t training_v2"
echo ""
echo "To detach (keep training running):"
echo "  Press Ctrl+B, then D"
echo ""
echo "Output is also being saved to: training_v2_output.txt"

