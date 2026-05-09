# Vision Endpoint Quick Test

## Test the Vision API

### 1. Start Azure Functions
```powershell
func host start
```

### 2. Test with Python
```python
import base64
import requests

# Test with any image
with open('test_image.jpg', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

response = requests.post(
    'http://localhost:7071/api/vision/infer',
    json={'image': img_b64}
)

print(response.json())
```

### 3. Test via Web UI
1. Open: http://localhost:7071/chat-web/
2. Click "🖼️ Upload Image" button
3. Select any image file
4. See instant analysis in chat

### 4. Test with CLI
```powershell
# Direct inference (no Functions needed)
python .\scripts\vision_inference.py --image test.jpg

# Batch processing
python .\scripts\vision_inference.py --image img1.jpg img2.jpg img3.jpg
```

## Expected Output

```json
{
  "label": "happy",
  "confidence": 0.873,
  "scores": {
    "happy": 0.873,
    "neutral": 0.081,
    "sad": 0.029,
    "angry": 0.017
  },
  "model_info": {
    "checkpoint": "data_out/vision_training/checkpoints/best_model.pt",
    "device": "cuda"
  }
}
```

## Troubleshooting

**Model not found**:
```powershell
# Train vision model first
python .\scripts\train_vision.py --quick
```

**Tests failing**:
```powershell
pytest tests/test_vision_inference.py -v
```

**Frontend issues**:
- Check browser console for errors
- Verify CORS in function_app.py
- Test endpoint directly with curl/Postman first
