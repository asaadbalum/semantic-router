# Maximum Effort Training - Target: 70%+ Typo Accuracy

## Goal
- **Typo Accuracy: 70%+** (current: 45%)
- **Clean Accuracy: Maintain 73%+** (no regression)

## Why 70%+ is Achievable

1. **Consistency Loss Protection**: Prevents clean accuracy regression, allowing aggressive augmentation
2. **More Training**: 40 epochs gives model more time to learn robustness
3. **More Data**: 40,000 samples = more diverse typo patterns
4. **Higher Typo Exposure**: 40% typo probability = model sees more typos
5. **Stronger Consistency Signal**: 2.5x consistency weight = model learns better that typos are noise

## Maximum Effort Parameters

```bash
accelerate launch ft_linear_lora_consistency.py \
  --epochs 40 \
  --max-samples 40000 \
  --typo-prob 0.40 \
  --consistency-weight 2.5 \
  --learning-rate 2e-5 \
  --batch-size 16 \
  --output-dir consistency_classifier_v2_bert-base-uncased_r16
```

**Why these parameters:**
- **40 epochs**: More training = better convergence (eval loss was still decreasing at epoch 20)
- **40,000 samples**: Maximum data for better generalization
- **40% typo-prob**: Aggressive augmentation, but consistency loss protects clean accuracy
- **2.5 consistency-weight**: Strong signal that typos shouldn't change predictions
- **Unique output-dir**: Prevents overwriting snapshot1 model

## Can More Epochs Harm?

**No, because:**
1. **Early stopping**: Script uses `load_best_model_at_end=True` - saves best model based on eval_loss
2. **Consistency loss**: Prevents overfitting by forcing consistent predictions
3. **Validation monitoring**: Eval runs every epoch, we can stop early if needed
4. **LoRA**: Only 2.4% of parameters are trainable, reduces overfitting risk

**If eval_loss starts increasing**: That's overfitting, but with consistency loss it's unlikely.

## Expected Results

- **Typo Accuracy**: 45% → 65-70% (aggressive augmentation + strong consistency)
- **Clean Accuracy**: 73%+ (consistency loss prevents regression)
- **Training Time**: ~2-3 hours on 4 GPUs

## Safety Measures

1. ✅ **Unique output directory**: Won't overwrite snapshot1
2. ✅ **Snapshot1 saved first**: Baseline preserved
3. ✅ **Best model selection**: Uses best eval_loss model
4. ✅ **Can restore**: Script to restore snapshot1 if needed

