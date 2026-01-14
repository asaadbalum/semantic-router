#!/bin/bash
# Restore snapshot1 model - use this if you need to go back to the baseline

set -e

# Find the most recent snapshot1
SNAPSHOT_DIR=$(ls -td snapshot1_* 2>/dev/null | head -1)

if [ -z "$SNAPSHOT_DIR" ]; then
    echo "❌ No snapshot1 found!"
    echo "   Available directories:"
    ls -d snapshot1_* 2>/dev/null || echo "   (none)"
    exit 1
fi

echo "=========================================="
echo "Restoring Snapshot1"
echo "=========================================="
echo "Snapshot: $SNAPSHOT_DIR"
echo ""

# Check if model exists in snapshot
if [ ! -d "$SNAPSHOT_DIR/model" ]; then
    echo "❌ Model not found in snapshot: $SNAPSHOT_DIR/model"
    exit 1
fi

# Show snapshot info
if [ -f "$SNAPSHOT_DIR/training_info.txt" ]; then
    echo "Snapshot Info:"
    cat "$SNAPSHOT_DIR/training_info.txt" | head -20
    echo ""
fi

# Ask for confirmation
read -p "Restore snapshot1 model? This will overwrite consistency_classifier_bert-base-uncased_r16_rust (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Backup current model if it exists
if [ -d "consistency_classifier_bert-base-uncased_r16_rust" ]; then
    BACKUP_DIR="consistency_classifier_bert-base-uncased_r16_rust.backup_$(date +%Y%m%d_%H%M%S)"
    echo "Backing up current model to: $BACKUP_DIR"
    mv consistency_classifier_bert-base-uncased_r16_rust "$BACKUP_DIR"
fi

# Restore snapshot1 model
echo "Restoring model..."
cp -r "$SNAPSHOT_DIR/model" consistency_classifier_bert-base-uncased_r16_rust

echo ""
echo "✅ Snapshot1 restored!"
echo "   Model: consistency_classifier_bert-base-uncased_r16_rust"
echo ""
echo "To verify, run:"
echo "  python comprehensive_test.py \\"
echo "    --old-model ~/semantic-router/models/mom-domain-classifier \\"
echo "    --new-model ./consistency_classifier_bert-base-uncased_r16_rust"

