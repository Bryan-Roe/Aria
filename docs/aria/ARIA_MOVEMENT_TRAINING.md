# Aria Movement AI Training - Quick Reference

## Overview
This document provides a complete guide for training AI models to automatically generate Aria character movement commands.

## What Was Created

### 1. Training Dataset
**Location**: `datasets/chat/aria_movement/`

**Files**:
- `train.json` - 40 training examples
- `test.json` - 10 test examples

**Command Distribution**:
- Move commands (left/right/up/down): 14 examples
- Walk commands (left/right/up/down): 13 examples
- Center commands: 4 examples
- Wave commands: 5 examples
- Jump commands: 4 examples
- Dance commands: 4 examples

**Format**: Each example teaches the AI to recognize natural language movement requests and respond with appropriate `[aria:action:direction]` tags.

Example:
```json
{
  "messages": [
    {"role": "user", "content": "Move Aria to the left"},
    {"role": "assistant", "content": "I'll move Aria to the left. [aria:move:left]"}
  ]
}
```

### 2. Training Configuration
**Location**: `autotrain_aria.yaml`

**Jobs Defined**:
- `aria_movement_quick` - Quick testing (40 samples, 2 epochs)
- `aria_movement_full` - Full training (all samples, 3 epochs)
- `aria_movement_qwen` - Qwen 2.5-3B variant

**Optimized Parameters**:
- Learning rate: 0.0003 (higher for specialized task)
- LoRA dropout: 0.05 (lower for small dataset)
- Epochs: 2-3 (sufficient for command syntax)

### 3. Automation Script
**Location**: `scripts/automate_aria_movement.py`

**Features**:
- Dataset validation with command distribution analysis
- Automated training pipeline
- Model evaluation with metrics
- Auto-deployment to active adapter location
- Full pipeline orchestration

## How It Works

### Movement Command System
The Azure Function app (`function_app.py`, lines 515-565) contains a parser that extracts movement commands from AI responses:

**Supported Commands**:
- `[aria:move:direction]` - Move character (100px distance)
- `[aria:walk:direction]` - Walk character (200px distance)
- `[aria:center]` - Center character on screen
- `[aria:wave]` - Wave animation
- `[aria:jump]` - Jump animation
- `[aria:dance]` - Dance animation

**Directions**: left, right, up, down

**Integration**:
1. User asks AI to move Aria
2. AI generates response with `[aria:...]` tags
3. Parser in `function_app.py` extracts commands
4. SSE endpoint emits "movement" events (lines 640-690)
5. Frontend receives events and animates character

## Training Commands

### Quick Training (Testing)
```powershell
python .\scripts\autotrain.py --config autotrain_aria.yaml --job aria_movement_quick
```
- 40 samples
- 2 epochs
- ~5-10 minutes on GPU

### Full Training (Production)
```powershell
python .\scripts\autotrain.py --config autotrain_aria.yaml --job aria_movement_full
```
- All samples
- 3 epochs
- ~10-15 minutes on GPU

### Automated Pipeline
```powershell
# Validate dataset only
python .\scripts\automate_aria_movement.py --validate-only

# Quick train with auto-deploy
python .\scripts\automate_aria_movement.py --quick --deploy

# Full train with auto-deploy
python .\scripts\automate_aria_movement.py --full --deploy
```

## Checking Training Status

### View autotrain status
```powershell
Get-Content .\data_out\autotrain\status.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Monitor training log
```powershell
# Find latest log directory
$logDir = Get-ChildItem .\data_out\autotrain\aria_movement_quick | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content "$($logDir.FullName)\stdout.log" -Tail 20
```

### Watch log in real-time
```powershell
$logDir = Get-ChildItem .\data_out\autotrain\aria_movement_quick | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content "$($logDir.FullName)\stdout.log" -Wait
```

## Testing the Trained Model

### Using the chat CLI
```powershell
# Load the trained adapter
python .\talk-to-ai\src\chat_cli.py --provider lora --model data_out\aria_models\aria_quick

# Test with movement commands
> Move Aria left
> Make her wave
> Walk right then jump
```

### Expected Output
The AI should generate responses with proper `[aria:...]` tags:
- "I'll move Aria left! [aria:move:left]"
- "Aria is waving! [aria:wave]"
- "Moving right and jumping! [aria:walk:right] [aria:jump]"

### Via Azure Function endpoint
```powershell
# Start the function app
func host start

# Test the streaming endpoint
# (Use the chat-web interface or curl to /api/chat-stream)
```

## Deploying the Model

### Manual Deployment
```powershell
# Copy trained model to active adapter location
Remove-Item -Recurse -Force .\data_out\lora_training\lora_adapter
Copy-Item -Recurse .\data_out\aria_models\aria_quick .\data_out\lora_training\lora_adapter

# Restart Azure Function to load new adapter
```

### Automated Deployment
The automation script can deploy automatically:
```powershell
python .\scripts\automate_aria_movement.py --quick --deploy
```

## Evaluation Metrics

After training completes, check these metrics:

**Perplexity**: Should be low (< 3.0 for good command learning)
- Measures how well model predicts command syntax

**Diversity**: Should be moderate (0.3-0.5)
- Distinct-1: Unique unigrams in responses
- Distinct-2: Unique bigrams in responses

**Command Accuracy**: Manual testing required
- Generate 10 test responses
- Count correct command tags
- Target: 90%+ accuracy

## Troubleshooting

### Training fails with CUDA errors
```powershell
# Check CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Fall back to CPU
# Edit autotrain_aria.yaml: change "device: auto" to "device: cpu"
```

### Model doesn't generate command tags
- Check training loss - should decrease below 1.0
- Verify dataset has correct format (use --validate-only)
- Try increasing epochs to 3-4
- Check learning rate not too low

### Commands not parsed in function app
- Verify exact syntax matches parser expectations
- Check case sensitivity (parser converts to lowercase)
- Ensure spaces in tags: `[aria:move:left]` not `[aria:moveleft]`

## Integration with Frontend

The frontend needs to:
1. Connect to SSE endpoint: `GET /api/chat-stream`
2. Listen for "movement" events
3. Parse JSON command payload
4. Execute animation based on action/direction

**Example JavaScript**:
```javascript
const eventSource = new EventSource('/api/chat-stream');
eventSource.addEventListener('movement', (event) => {
  const commands = JSON.parse(event.data);
  commands.forEach(cmd => {
    moveAria(cmd.action, cmd.direction, cmd.distance);
  });
});
```

## Next Steps

1. ✅ **Dataset created** - 40 training + 10 test examples
2. ✅ **Training configuration ready** - autotrain_aria.yaml
3. ✅ **Automation script** - automate_aria_movement.py
4. 🔄 **Training in progress** - aria_movement_quick job
5. ⏳ **Evaluation pending** - Test command generation accuracy
6. ⏳ **Deployment pending** - Copy to active adapter
7. ⏳ **Integration testing** - Verify end-to-end flow
8. ⏳ **Frontend implementation** - Connect SSE movement events

## Advanced: Continuous Improvement

To continuously improve aria movement AI:

1. **Monitor usage**: Log all movement requests and responses
2. **Collect failures**: Track when commands aren't generated correctly
3. **Augment dataset**: Add failed examples to training data
4. **Retrain periodically**: Weekly/monthly retraining with updated dataset
5. **A/B testing**: Compare old vs new adapters on held-out test set

## Files Reference

**Training**:
- `datasets/chat/aria_movement/train.json` - Training data
- `datasets/chat/aria_movement/test.json` - Test data
- `autotrain_aria.yaml` - Training configuration
- `scripts/training/autotrain.py` - Training orchestrator
- `scripts/automate_aria_movement.py` - Full automation

**Integration**:
- `function_app.py` (lines 515-565) - Command parser
- `function_app.py` (lines 640-690) - SSE streaming integration
- `data_out/lora_training/lora_adapter/` - Active model location

**Outputs**:
- `data_out/aria_models/aria_quick/` - Trained adapter
- `data_out/autotrain/aria_movement_quick/` - Training logs
- `data_out/autotrain/status.json` - Job status

---

Last updated: 2025-11-27
