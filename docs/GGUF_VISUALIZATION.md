# GGUF File Visualization Tools

Tools for inspecting, analyzing, and visualizing GGUF (GPT-Generated Unified Format) model files.

## 🎯 Overview

This repository provides two complementary tools for GGUF file visualization:

1. **CLI Visualizer** (`visualize_gguf_simple.py`) - Command-line tool for quick inspection
2. **Web Visualizer** (`dashboard/gguf_visualizer.html`) - Interactive browser-based analysis

## 🚀 Quick Start

### CLI Visualizer

```bash
# Basic inspection
python scripts/visualize_gguf_simple.py data_out/quantum_banknote_perfect_model.gguf

# Export analysis to JSON
python scripts/visualize_gguf_simple.py model.gguf --json analysis.json

# Export analysis to Markdown
python scripts/visualize_gguf_simple.py model.gguf --md report.md

# Export both formats
python scripts/visualize_gguf_simple.py model.gguf --json analysis.json --md report.md
```

### Web Visualizer

```bash
# Start a local web server
cd dashboard
python -m http.server 8000

# Open in browser
# http://localhost:8000/gguf_visualizer.html
```

Or use VS Code's Live Server extension to open `dashboard/gguf_visualizer.html` directly.

## 📊 Features

### CLI Visualizer Features

- **File Overview**: Size, version, tensor count, parameter count
- **Metadata Display**: All model metadata in organized format
- **Architecture Analysis**: Layer grouping with parameter distribution
- **Tensor Inspection**: Detailed tensor shapes, types, and sizes
- **Statistics**: Data type distribution, parameter analysis
- **Export Options**: JSON and Markdown formats

### Web Visualizer Features

- **Interactive Interface**: Tabbed navigation with smooth animations
- **Drag & Drop**: Upload GGUF files directly from desktop
- **Real-time Parsing**: In-browser GGUF file parsing
- **Visual Statistics**: Color-coded parameter distribution charts
- **Search & Filter**: Search through metadata and tensors
- **Architecture Visualization**: Layer groups with progress bars
- **Export Capabilities**: Export analysis as JSON or Markdown

## 📖 Understanding the Output

### Overview Section

```
📄 File: quantum_banknote_perfect_model.gguf
📏 Size: 0.01 MB (5,428 bytes)
🔢 Version: GGUF v3
🧱 Tensors: 28
📊 Parameters: 925 (0.00M)
🏷️  Metadata: 10 entries
```

- **File**: Filename being analyzed
- **Size**: File size in MB and bytes
- **Version**: GGUF format version
- **Tensors**: Number of weight tensors in the model
- **Parameters**: Total trainable parameters
- **Metadata**: Number of metadata key-value pairs

### Metadata Section

Shows all model metadata:

```
accuracy        = 100.00%
dataset         = Banknote Authentication (UCI)
features        = 4
framework       = PennyLane + PyTorch
architecture    = hybrid-qnn
```

Common metadata keys:
- `task`: Model's primary task
- `accuracy`: Model performance metric
- `dataset`: Training dataset name
- `framework`: ML framework used
- `general.architecture`: Model architecture type
- `qubits`: Number of qubits (for quantum models)

### Architecture Section

Groups tensors by layer and shows parameter distribution:

```
Layer Groups:
  decoder          :  16 tensors,  404 params (43.7%)
  encoder          :   9 tensors,  417 params (45.1%)
  quantum_layer    :   1 tensors,   24 params ( 2.6%)
  residual_proj    :   2 tensors,   80 params ( 8.6%)
```

Each layer group shows:
- Number of tensors in the group
- Total parameters
- Percentage of model parameters

### Tensors Section

Detailed list of all tensors:

```
Name                        Shape      Type    Elements
--------------------------------------------------------
encoder.0.weight            (4, 16)    F32     64
encoder.0.bias              (16,)      F32     16
quantum_layer.qlayer.weights (24,)     F32     24
```

- **Name**: Tensor identifier (layer.sublayer.type)
- **Shape**: Dimensional shape tuple
- **Type**: Data type (F32=32-bit float, F16=16-bit float, Q4_0=4-bit quantized)
- **Elements**: Total number of values

### Statistics Section

Analyzes model composition:

```
Data Type Distribution:
Type     Tensors    Parameters    Percent
------------------------------------------
F32      28         925           100.0%

Parameter Distribution:
  Smallest tensor: 1 elements
  Largest tensor:  256 elements
  Average tensor:  33 elements
```

## 🔧 Advanced Usage

### Analyzing Custom GGUF Files

```bash
# Analyze any GGUF file
python scripts/visualize_gguf_simple.py /path/to/model.gguf

# Compare multiple models
for model in data_out/*.gguf; do
    echo "=== $model ==="
    python scripts/visualize_gguf_simple.py "$model" | grep "Parameters:"
done
```

### Batch Processing

```bash
# Generate reports for all GGUF files
for file in data_out/*.gguf; do
    base=$(basename "$file" .gguf)
    python scripts/visualize_gguf_simple.py "$file" \
        --json "data_out/${base}_analysis.json" \
        --md "data_out/${base}_report.md"
done
```

### Integration with Scripts

```python
import subprocess
import json

# Run visualizer and capture output
result = subprocess.run(
    ['python', 'scripts/visualize_gguf_simple.py', 'model.gguf', '--json', '/tmp/out.json'],
    capture_output=True, text=True
)

# Load analysis
with open('/tmp/out.json') as f:
    analysis = json.load(f)

# Use the data
print(f"Model has {len(analysis['tensors'])} tensors")
print(f"Total parameters: {sum(t['num_elements'] for t in analysis['tensors'])}")
```

## 📁 GGUF Format Reference

### File Structure

```
┌─────────────────────────────────────┐
│ Header                              │
│  - Magic number (0x46554747)       │
│  - Version (3)                      │
│  - Endianness (1 = little)          │
│  - Metadata count                   │
├─────────────────────────────────────┤
│ Metadata Section                    │
│  - Key-value pairs                  │
│  - Supports strings, numbers, arrays│
├─────────────────────────────────────┤
│ Tensor Info Section                 │
│  - Tensor count                     │
│  - Tensor metadata (name, shape, etc)│
├─────────────────────────────────────┤
│ Tensor Data Section                 │
│  - Raw tensor bytes                 │
└─────────────────────────────────────┘
```

### Supported Data Types

| Type | Code | Description |
|------|------|-------------|
| F32 | 0 | 32-bit floating point |
| F16 | 1 | 16-bit floating point |
| Q4_0 | 2 | 4-bit quantized (block-wise) |
| Q4_1 | 3 | 4-bit quantized (block-wise with scale) |
| Q8_0 | 6 | 8-bit quantized |

## 🎨 Web Visualizer Features

### Upload Methods

1. **File Picker**: Click "Choose GGUF File" button
2. **Drag & Drop**: Drag GGUF file onto the page (future feature)
3. **Sample Models**: Click sample model buttons to load pre-configured examples

### Navigation

- **Overview Tab**: High-level statistics and export options
- **Metadata Tab**: Searchable key-value pairs
- **Architecture Tab**: Visual layer grouping with percentage bars
- **Tensors Tab**: Searchable tensor list with details
- **Statistics Tab**: Data type distribution and size analysis

### Export Options

- **Export JSON**: Download complete analysis as JSON
- **Export Markdown**: Download formatted report as Markdown

## 🔍 Troubleshooting

### Common Issues

**"Invalid magic" error**
```
❌ Error: Invalid magic: 0x...
```
- File is not a valid GGUF file
- File may be corrupted
- Check that you're using the correct file

**"Unsupported version" error**
```
❌ Error: Unsupported GGUF version: X
```
- File uses a newer GGUF version
- Update visualizer to support the version

**Unicode decode errors**
- File may be corrupted
- Try re-exporting the model

### Getting Help

1. Check that the GGUF file was created by `export_quantum_to_gguf.py`
2. Verify file integrity: `file model.gguf` should show data file
3. Check file size: Very small files (<1KB) may be invalid
4. Try opening in a hex editor to verify magic bytes: `47 47 55 46`

## 📚 Examples

### Example 1: Quick Inspection

```bash
python scripts/visualize_gguf_simple.py data_out/quantum_banknote_perfect_model.gguf
```

Output shows:
- 28 tensors
- 925 parameters
- 100% accuracy
- Hybrid quantum-classical architecture

### Example 2: Export for Documentation

```bash
python scripts/visualize_gguf_simple.py model.gguf --md MODEL_ANALYSIS.md
```

Creates a Markdown document with:
- Complete metadata table
- Full tensor listing
- Formatted statistics

### Example 3: JSON for Automation

```bash
python scripts/visualize_gguf_simple.py model.gguf --json analysis.json

# Use in other tools
jq '.metadata.accuracy' analysis.json
jq '.tensors | length' analysis.json
```

## 🛠️ Development

### Creating GGUF Files

Use the export script to create GGUF files:

```bash
python scripts/export_quantum_to_gguf.py
```

Or programmatically:

```python
from scripts.export_quantum_to_gguf import export_quantum_model_to_gguf

metadata = {
    "task": "Classification",
    "accuracy": 95.5,
    "framework": "PyTorch"
}

export_quantum_model_to_gguf(
    model_path="model.pt",
    output_gguf="model.gguf",
    metadata=metadata
)
```

### Extending the Visualizer

To add new visualization features:

1. **CLI**: Edit `scripts/visualize_gguf_simple.py`
2. **Web**: Edit `dashboard/gguf_visualizer.html`

Both tools share the same GGUF parsing logic, so format changes only need to be updated once.

## 📝 Related Tools

- **Export Script**: `scripts/export_quantum_to_gguf.py` - Creates GGUF files
- **Model Guide**: `data_out/GGUF_MODEL_GUIDE.md` - Usage documentation
- **Training Scripts**: `scripts/autotrain.py` - Model training workflows

## 🤝 Contributing

To improve GGUF visualization:

1. Test with various model sizes and architectures
2. Add support for additional data types
3. Enhance web visualizer with charts and graphs
4. Implement comparison tools for multiple models
5. Add model diff visualization

## 📄 License

Part of the Aria AI project. See main project README for license details.
