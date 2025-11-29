# Vision API Guide

## Overview

The Vision API provides endpoints for analyzing images using the trained TinyConvNet expression/emotion classifier. This guide covers both single and batch inference endpoints.

## Endpoints

### 1. Single Image Inference

**Endpoint**: `POST /api/vision/infer`

**Request Body**:
```json
{
  "image": "<base64-encoded-image>"
}
```

**Response**:
```json
{
  "label": "happy",
  "confidence": 0.87,
  "scores": {
    "happy": 0.87,
    "neutral": 0.08,
    "sad": 0.03,
    "angry": 0.02
  },
  "model_info": {
    "checkpoint": "data_out/vision_training/checkpoints/best_model.pt",
    "device": "cuda"
  }
}
```

**Example (curl)**:
```bash
# Encode image to base64
$base64Image = [Convert]::ToBase64String([IO.File]::ReadAllBytes("test.jpg"))

# Call API
curl -X POST http://localhost:7071/api/vision/infer `
  -H "Content-Type: application/json" `
  -d "{\"image\": \"$base64Image\"}"
```

### 2. Batch Image Inference

**Endpoint**: `POST /api/vision/batch-infer`

**Request Body**:
```json
{
  "images": [
    "<base64-encoded-image-1>",
    "<base64-encoded-image-2>"
  ]
}
```

**Response**:
```json
{
  "results": [
    {
      "label": "happy",
      "confidence": 0.87,
      "scores": { "happy": 0.87, "neutral": 0.08, "sad": 0.03, "angry": 0.02 }
    },
    {
      "label": "sad",
      "confidence": 0.92,
      "scores": { "sad": 0.92, "neutral": 0.05, "happy": 0.02, "angry": 0.01 }
    }
  ],
  "count": 2
}
```

**Limits**: Maximum 50 images per batch request

## Frontend Integration

### HTML Elements

```html
<!-- Upload button -->
<button id="visionUploadButton">🖼️ Upload Image</button>

<!-- Hidden file input -->
<input type="file" id="visionImageInput" accept="image/*" style="display: none;">

<!-- Preview container -->
<div id="visionPreview" style="display: none;"></div>
```

### JavaScript Implementation

```javascript
// Constants
const VISION_INFER_API = '/api/vision/infer';

// State
let uploadedImageBase64 = null;

// Event handlers
document.getElementById('visionUploadButton').addEventListener('click', () => {
    document.getElementById('visionImageInput').click();
});

document.getElementById('visionImageInput').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (!file || !file.type.startsWith('image/')) return;

    // Read file as base64
    const reader = new FileReader();
    reader.onload = async (e) => {
        uploadedImageBase64 = e.target.result.split(',')[1]; // Remove prefix

        // Call Vision API
        const response = await fetch(VISION_INFER_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: uploadedImageBase64 })
        });

        const result = await response.json();
        console.log('Vision result:', result);
        
        // Display result in UI
        displayVisionResult(result, file.name);
    };
    
    reader.readAsDataURL(file);
});

function displayVisionResult(result, filename) {
    const message = `🖼️ Image Analysis: ${filename}\n` +
        `Expression: ${result.label} (${(result.confidence * 100).toFixed(1)}% confidence)\n\n` +
        `All Scores:\n${Object.entries(result.scores)
            .sort((a, b) => b[1] - a[1])
            .map(([label, score]) => `- ${label}: ${(score * 100).toFixed(1)}%`)
            .join('\n')}`;
    
    // Add to chat or display elsewhere
    addChatMessage('assistant', message);
}
```

## Python Client Example

```python
import base64
import requests

# Load and encode image
with open('test.jpg', 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# Single inference
response = requests.post(
    'http://localhost:7071/api/vision/infer',
    json={'image': image_base64}
)
result = response.json()
print(f"Predicted: {result['label']} ({result['confidence']:.2%})")

# Batch inference
with open('test2.jpg', 'rb') as f:
    image2_base64 = base64.b64encode(f.read()).decode('utf-8')

response = requests.post(
    'http://localhost:7071/api/vision/batch-infer',
    json={'images': [image_base64, image2_base64]}
)
results = response.json()
print(f"Analyzed {results['count']} images")
for i, r in enumerate(results['results']):
    print(f"  Image {i+1}: {r['label']} ({r['confidence']:.2%})")
```

## CLI Testing

Use the vision inference module directly:

```powershell
# Single image prediction
python .\scripts\vision_inference.py --image test.jpg

# Batch prediction
python .\scripts\vision_inference.py --image test1.jpg test2.jpg test3.jpg

# Custom checkpoint
python .\scripts\vision_inference.py --image test.jpg --checkpoint path/to/model.pt
```

## Model Information

**Architecture**: TinyConvNet
- Input: 64×64 RGB images (3 channels)
- Conv layers: 32 → 64 → 128 filters
- Fully connected: 128 → 64 → num_classes

**Training**: See `scripts/train_vision.py` and `VISION_TRAINING_GUIDE.md`

**Checkpoints**: Auto-detected from:
1. `data_out/vision_training/checkpoints/best_model.pt` (recommended)
2. `data_out/vision_training/checkpoints/latest_model.pt` (fallback)
3. Custom path via `--checkpoint` argument

## Error Handling

**Common Errors**:

1. **Model not found** (`500`):
   - Checkpoint file missing
   - Solution: Train model first with `train_vision.py`

2. **Invalid base64** (`400`):
   - Malformed base64 string
   - Solution: Ensure proper base64 encoding without data URI prefix

3. **Unsupported image format** (`400`):
   - PIL cannot decode image
   - Solution: Use JPEG, PNG, BMP, or other PIL-supported formats

4. **Image too large** (`413`):
   - Request body exceeds Azure Functions limit (100 MB default)
   - Solution: Resize images before upload, or use batch API with smaller images

**Example Error Response**:
```json
{
  "error": "Failed to load checkpoint: [Errno 2] No such file or directory: 'best_model.pt'",
  "details": "Model checkpoint not found. Train model first."
}
```

## Performance Tips

1. **Batch Processing**: Use `/api/vision/batch-infer` for multiple images to reduce HTTP overhead
2. **Image Resizing**: Pre-resize images to 64×64 client-side to reduce upload size
3. **Model Caching**: Model is cached after first request (singleton pattern)
4. **Device Auto-Detection**: Uses CUDA if available, falls back to CPU
5. **Base64 Overhead**: ~33% size increase vs raw bytes; consider compression for large batches

## Integration with Aria Chat

The vision API is integrated into the Aria chat interface (`chat-web/`):

1. **Upload Button**: Click 🖼️ icon to upload image
2. **Auto-Analysis**: Image analyzed immediately on upload
3. **Chat Display**: Results shown as formatted markdown message
4. **Preview**: Thumbnail preview with clear button
5. **Status Updates**: Real-time status in chat footer

**User Flow**:
1. User clicks "🖼️ Upload Image" button
2. File picker opens (accepts image/*)
3. Image loads and preview displays
4. Vision API analyzes image automatically
5. Results appear as Aria's response in chat
6. User can clear and upload another image

## Security & Validation

- **Input Validation**: Base64 format checked, PIL decoding verified
- **File Size**: Implicit limit from Azure Functions (100 MB)
- **CORS**: Enabled for web frontend access
- **Error Sanitization**: Stack traces not exposed to clients
- **Rate Limiting**: None by default; add via Azure APIM if needed

## Monitoring

Check endpoint health:
```bash
curl http://localhost:7071/api/ai/status
```

Response includes vision endpoints:
```json
{
  "endpoints": {
    "vision": ["/api/vision/infer", "/api/vision/batch-infer"],
    ...
  }
}
```

## Next Steps

1. **Test Endpoints**: Run `pytest tests/test_vision_inference.py`
2. **Deploy**: `func azure functionapp publish <app-name>`
3. **Monitor**: Enable Application Insights for latency/error tracking
4. **Scale**: Configure Azure Functions scaling rules for vision workloads
5. **Enhance**: Add multi-model support, face detection, or custom labels

## References

- **Training Guide**: `VISION_TRAINING_GUIDE.md`
- **Inference Module**: `scripts/vision_inference.py`
- **Tests**: `tests/test_vision_inference.py`
- **Frontend**: `chat-web/index.html` and `chat-web/chat.js`
- **Azure Functions**: `function_app.py`
