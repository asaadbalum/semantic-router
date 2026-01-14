# PR Model Upload Guide - Snapshot1 (v1)

## Model Status
- ✅ **Model verified**: v1 (snapshot1) - 14 categories, 437MB
- ✅ **Location**: `models/mom-domain-classifier-new/` (local)
- ✅ **Results**: +3% clean accuracy, +11% typo accuracy

## Upload Options

### Option A: Upload to HuggingFace (Recommended)

**Requirements:**
1. Access to `LLM-Semantic-Router` organization on HuggingFace
2. HuggingFace CLI installed: `pip install huggingface_hub`
3. Login: `huggingface-cli login` (or set `HF_TOKEN` env var)

**Steps:**
```bash
cd ~/Projects/semantic-router/src/training/training_lora/classifier_model_fine_tuning_lora

python upload_to_huggingface.py \
  --model-path ../../../../models/mom-domain-classifier-new \
  --repo-id LLM-Semantic-Router/mom-domain-classifier-v1-typo-robust
```

**After upload:**
- Update `config/config.yaml` to reference the new model
- Or keep local path: `models/mom-domain-classifier-new`

### Option B: Keep Local (For Testing/Development)

**Steps:**
1. Model is already at: `models/mom-domain-classifier-new/`
2. Update `config/config.yaml`:
   ```yaml
   classifier:
     category_model:
       model_id: "models/mom-domain-classifier-new"
   ```
3. Test in VSR
4. For PR: Document that users need to download/place the model

### Option C: Replace Existing Model

**Steps:**
1. Backup current: `mv models/mom-domain-classifier models/mom-domain-classifier-backup`
2. Copy new: `cp -r models/mom-domain-classifier-new models/mom-domain-classifier`
3. Test in VSR
4. For PR: Include model files (if repo allows large files)

## Recommendation

**For PR**: Option A (HuggingFace)
- Keeps repo clean (no large files)
- Standard practice for this project
- Easy for users to download
- Matches existing model storage pattern

**For Testing**: Option B (Local)
- Quick to test
- No upload needed
- Can switch to HuggingFace later

## Next Steps

1. **Test model in VSR** (recommended before upload)
2. **Upload to HuggingFace** (if you have access)
3. **Update config/docs** to reference new model
4. **Create PR** with:
   - Model reference (HuggingFace or local)
   - Code changes (entropy fix)
   - Results documentation

