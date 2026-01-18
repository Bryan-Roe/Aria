# GGUF Visualization Tools

Quick reference for GGUF file visualization tools.

## 🚀 Quick Start

### CLI Tool

```bash
# Basic inspection
python scripts/visualize_gguf_simple.py data_out/quantum_banknote_perfect_model.gguf

# Export to JSON and Markdown
python scripts/visualize_gguf_simple.py model.gguf --json analysis.json --md report.md
```

### Web Interface

```bash
# Start server
cd dashboard
python serve_gguf_viz.py

# Open in browser
# http://localhost:8080/gguf_visualizer.html
```

## 📊 What You Get

### CLI Output
- File overview (size, version, parameters)
- All metadata
- Architecture breakdown by layer
- Complete tensor listing
- Statistical analysis
- Export to JSON/Markdown

### Web Interface
- Interactive tabs (Overview, Metadata, Architecture, Tensors, Statistics)
- Search functionality
- Visual charts and progress bars
- Export capabilities
- Drag-and-drop file upload

## 📖 Documentation

- **Full Guide**: [docs/GGUF_VISUALIZATION.md](../docs/GGUF_VISUALIZATION.md)
- **Implementation**: [docs/GGUF_VISUALIZATION_SUMMARY.md](../docs/GGUF_VISUALIZATION_SUMMARY.md)

## 🔧 Example Usage

```bash
# Inspect quantum model
./scripts/visualize_gguf_simple.py data_out/quantum_banknote_perfect_model.gguf

# Batch export all models
for file in data_out/*.gguf; do
    base=$(basename "$file" .gguf")
    ./scripts/visualize_gguf_simple.py "$file" --md "docs/${base}_report.md"
done

# Compare parameter counts
for model in data_out/*.gguf; do
    echo "$(basename $model):"
    ./scripts/visualize_gguf_simple.py "$model" | grep "Parameters:"
done
```

## 🎯 Features

- ✅ No external dependencies
- ✅ Fast parsing (<1s for small models)
- ✅ Multiple export formats
- ✅ Clean, readable output
- ✅ Both CLI and web interfaces
- ✅ Comprehensive documentation

## 📝 Sample Output

```
📦 GGUF FILE OVERVIEW
======================================================================

📄 File: quantum_banknote_perfect_model.gguf
📏 Size: 0.01 MB (5,428 bytes)
🔢 Version: GGUF v3
🧱 Tensors: 28
📊 Parameters: 925 (0.00M)
🏷️  Metadata: 10 entries

🏗️  MODEL ARCHITECTURE
======================================================================

Layer Groups:
  decoder       :  16 tensors,  404 params (43.7%)
  encoder       :   9 tensors,  417 params (45.1%)
  quantum_layer :   1 tensors,   24 params ( 2.6%)
  residual_proj :   2 tensors,   80 params ( 8.6%)
```

## 🔗 Related Tools

- `export_quantum_to_gguf.py` - Create GGUF files from PyTorch models
- `autotrain.py` - Training pipeline
- `quantum_mcp_server.py` - Quantum MCP integration

---

**Created**: January 17, 2026  
**Status**: ✅ Production ready
