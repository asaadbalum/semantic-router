# Optimized Training Parameters - Maximum Effort

## Analysis: What Made It Work

### Key Success Factor: Consistency Loss
The consistency loss mechanism is what prevents clean accuracy regression while improving typo accuracy. This means we can be **more aggressive** with augmentation because the consistency loss will protect clean accuracy.

### Current Successful Parameters (Snapshot1)
- `epochs: 20`
- `max-samples: 25000`
- `typo-prob: 0.25` (25% of samples get typos)
- `consistency-weight: 1.0`
- `learning-rate: 2e-5`
- `batch-size: 16` (4 GPUs = 64 effective)

### Results
- Clean: 70% → 73% (+3%)
- Typo: 34% → 45% (+11%)

## Optimized Parameters (Maximum Effort)

Since consistency loss prevents regression, we can push harder:

### Recommended: Aggressive but Safe
```bash
accelerate launch ft_linear_lora_consistency.py \
  --epochs 30 \
  --max-samples 35000 \
  --typo-prob 0.35 \
  --consistency-weight 2.0 \
  --learning-rate 2e-5 \
  --batch-size 16
```

**Rationale:**
1. **More epochs (30)**: Eval loss was still decreasing at epoch 20 (1.52), more training = better convergence
2. **More data (35000)**: More diverse examples = better generalization, we have the resources
3. **Higher typo-prob (0.35)**: More typos = better robustness learning, consistency loss protects clean accuracy
4. **Higher consistency-weight (2.0)**: Stronger consistency signal = model learns better that typos shouldn't change predictions
5. **Same learning-rate**: 2e-5 worked well, no need to change

**Expected improvements:**
- Typo accuracy: 45% → 55-60% (more aggressive augmentation + stronger consistency)
- Clean accuracy: Maintain 73%+ (consistency loss prevents regression)

### Alternative: Conservative Increase
If you want to be more cautious:
```bash
accelerate launch ft_linear_lora_consistency.py \
  --epochs 25 \
  --max-samples 30000 \
  --typo-prob 0.30 \
  --consistency-weight 1.5 \
  --learning-rate 2e-5 \
  --batch-size 16
```

## Why This Will Work Better

1. **Consistency Loss Protection**: The KL divergence loss ensures that even with 35% typos, the model must give the same prediction for clean/typo pairs. This prevents clean accuracy regression.

2. **More Training Signal**: 
   - 30 epochs = 50% more training time
   - 35,000 samples = 40% more data
   - 2.0 consistency weight = 2x stronger consistency signal

3. **Better Robustness Learning**: 
   - 35% typo probability = model sees more typos during training
   - Stronger consistency weight = model learns better that typos are noise, not signal

## Recommendation

**Use the aggressive parameters** - we have:
- ✅ 4 GPUs (plenty of compute)
- ✅ Time available
- ✅ Consistency loss protection (prevents regression)
- ✅ Proven approach (snapshot1 already worked)

The aggressive parameters should push typo accuracy to 55-60% while maintaining clean accuracy at 73%+.

