#!/usr/bin/env python3
"""
GGUF File Visualizer

Interactive tool to inspect, analyze, and visualize GGUF model files.
Displays metadata, tensor structure, architecture, and generates visual reports.
"""

import struct
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import argparse


class GGUFReader:
    """Read and parse GGUF format files"""
    
    # GGUF format constants
    GGUF_MAGIC = 0x46554747  # "GGUF" in hex
    GGUF_VERSION_SUPPORTED = [2, 3]
    
    # GGML data types
    GGML_TYPE_NAMES = {
        0: "F32",
        1: "F16",
        2: "Q4_0",
        3: "Q4_1",
        4: "Q5_0",
        5: "Q5_1",
        6: "Q8_0",
        7: "Q8_1",
        8: "Q2_K",
        9: "Q3_K",
        10: "Q4_K",
        11: "Q5_K",
        12: "Q6_K",
        13: "Q8_K",
        14: "I8",
        15: "I16",
        16: "I32",
    }
    
    # Value type constants
    VALUE_TYPE_UINT8 = 0
    VALUE_TYPE_INT8 = 1
    VALUE_TYPE_UINT16 = 2
    VALUE_TYPE_INT16 = 3
    VALUE_TYPE_UINT32 = 4
    VALUE_TYPE_INT32 = 5
    VALUE_TYPE_FLOAT32 = 6
    VALUE_TYPE_BOOL = 7
    VALUE_TYPE_STRING = 8
    VALUE_TYPE_ARRAY = 9
    VALUE_TYPE_UINT64 = 10
    VALUE_TYPE_INT64 = 11
    VALUE_TYPE_FLOAT64 = 12
    
    def __init__(self, filename: str):
        self.filename = filename
        self.file = None
        self.metadata = {}
        self.tensors = []
        self.header = {}
        
    def read(self):
        """Read and parse GGUF file"""
        print(f"📖 Reading GGUF file: {self.filename}")
        
        with open(self.filename, 'rb') as f:
            self.file = f
            
            # Read header
            magic = struct.unpack('<I', f.read(4))[0]
            if magic != self.GGUF_MAGIC:
                raise ValueError(f"Invalid GGUF magic: 0x{magic:08X} (expected 0x{self.GGUF_MAGIC:08X})")
            
            version = struct.unpack('<I', f.read(4))[0]
            if version not in self.GGUF_VERSION_SUPPORTED:
                raise ValueError(f"Unsupported GGUF version: {version}")
            
            endian = struct.unpack('<I', f.read(4))[0]  # Read endianness
            
            metadata_kv_count = struct.unpack('<Q', f.read(8))[0]
            tensor_count = struct.unpack('<Q', f.read(8))[0]
            
            self.header = {
                'magic': magic,
                'version': version,
                'tensor_count': tensor_count,
                'metadata_kv_count': metadata_kv_count,
            }
            
            print(f"  ✓ GGUF v{version}")
            print(f"  ✓ {metadata_kv_count} metadata entries")
            print(f"  ✓ {tensor_count} tensors")
            
            # Read metadata
            print(f"\n📊 Reading metadata...")
            for _ in range(metadata_kv_count):
                key, value = self._read_metadata_kv(f)
                self.metadata[key] = value
            
            # Read tensor info
            print(f"\n🔢 Reading tensor information...")
            for _ in range(tensor_count):
                tensor_info = self._read_tensor_info(f)
                self.tensors.append(tensor_info)
        
        print(f"\n✅ Successfully read GGUF file")
        return self
    
    def _read_string(self, f) -> str:
        """Read a string from file"""
        length = struct.unpack('<I', f.read(4))[0]  # String length is 32-bit
        return f.read(length).decode('utf-8')
    
    def _read_metadata_kv(self, f) -> Tuple[str, Any]:
        """Read a metadata key-value pair"""
        key = self._read_string(f)
        value_type = struct.unpack('<I', f.read(4))[0]
        
        # Read value based on type
        if value_type == self.VALUE_TYPE_UINT8:
            value = struct.unpack('<B', f.read(1))[0]
        elif value_type == self.VALUE_TYPE_INT8:
            value = struct.unpack('<b', f.read(1))[0]
        elif value_type == self.VALUE_TYPE_UINT16:
            value = struct.unpack('<H', f.read(2))[0]
        elif value_type == self.VALUE_TYPE_INT16:
            value = struct.unpack('<h', f.read(2))[0]
        elif value_type == self.VALUE_TYPE_UINT32:
            value = struct.unpack('<I', f.read(4))[0]
        elif value_type == self.VALUE_TYPE_INT32:
            value = struct.unpack('<i', f.read(4))[0]
        elif value_type == self.VALUE_TYPE_FLOAT32:
            value = struct.unpack('<f', f.read(4))[0]
        elif value_type == self.VALUE_TYPE_UINT64:
            value = struct.unpack('<Q', f.read(8))[0]
        elif value_type == self.VALUE_TYPE_INT64:
            value = struct.unpack('<q', f.read(8))[0]
        elif value_type == self.VALUE_TYPE_FLOAT64:
            value = struct.unpack('<d', f.read(8))[0]
        elif value_type == self.VALUE_TYPE_BOOL:
            value = bool(struct.unpack('<B', f.read(1))[0])
        elif value_type == self.VALUE_TYPE_STRING:
            value = self._read_string(f)
        elif value_type == self.VALUE_TYPE_ARRAY:
            # Read array
            array_type = struct.unpack('<I', f.read(4))[0]
            array_length = struct.unpack('<Q', f.read(8))[0]
            value = f"[Array of {array_length} items, type={array_type}]"
        else:
            value = f"<Unknown type {value_type}>"
        
        return key, value
    
    def _read_tensor_info(self, f) -> Dict:
        """Read tensor metadata"""
        name = self._read_string(f)
        n_dims = struct.unpack('<I', f.read(4))[0]
        
        # Read dimensions (in GGUF format)
        dims = []
        for _ in range(n_dims):
            dim = struct.unpack('<Q', f.read(8))[0]
            dims.append(dim)
        # Dimensions are stored in reverse order in GGUF
        dims = list(reversed(dims))
        
        dtype = struct.unpack('<I', f.read(4))[0]
        offset = struct.unpack('<Q', f.read(8))[0]
        
        # Calculate size
        num_elements = 1
        for dim in dims:
            num_elements *= dim
        
        dtype_name = self.GGML_TYPE_NAMES.get(dtype, f"Unknown({dtype})")
        
        return {
            'name': name,
            'dims': dims,
            'shape': tuple(dims),
            'dtype': dtype_name,
            'dtype_code': dtype,
            'offset': offset,
            'num_elements': num_elements,
        }
    
    def get_summary(self) -> Dict:
        """Get a summary of the GGUF file"""
        total_params = sum(t['num_elements'] for t in self.tensors)
        
        # Group tensors by layer type
        tensor_groups = defaultdict(list)
        for tensor in self.tensors:
            # Extract layer type from name
            parts = tensor['name'].split('.')
            if len(parts) > 1:
                layer_type = parts[0]
            else:
                layer_type = 'other'
            tensor_groups[layer_type].append(tensor)
        
        # Calculate file size
        file_size = os.path.getsize(self.filename)
        
        return {
            'filename': self.filename,
            'file_size': file_size,
            'file_size_mb': file_size / (1024 * 1024),
            'version': self.header['version'],
            'tensor_count': len(self.tensors),
            'metadata_count': len(self.metadata),
            'total_parameters': total_params,
            'total_parameters_m': total_params / 1_000_000,
            'tensor_groups': dict(tensor_groups),
        }


class GGUFVisualizer:
    """Visualize GGUF file contents"""
    
    def __init__(self, reader: GGUFReader):
        self.reader = reader
        self.summary = reader.get_summary()
    
    def print_overview(self):
        """Print a high-level overview"""
        print("\n" + "=" * 70)
        print("📦 GGUF FILE OVERVIEW")
        print("=" * 70)
        
        print(f"\n📄 File: {os.path.basename(self.summary['filename'])}")
        print(f"📏 Size: {self.summary['file_size_mb']:.2f} MB ({self.summary['file_size']:,} bytes)")
        print(f"🔢 Version: GGUF v{self.summary['version']}")
        print(f"🧱 Tensors: {self.summary['tensor_count']}")
        print(f"📊 Parameters: {self.summary['total_parameters']:,} ({self.summary['total_parameters_m']:.2f}M)")
        print(f"🏷️  Metadata Entries: {self.summary['metadata_count']}")
    
    def print_metadata(self):
        """Print metadata information"""
        print("\n" + "=" * 70)
        print("🏷️  METADATA")
        print("=" * 70)
        
        if not self.reader.metadata:
            print("  (No metadata)")
            return
        
        # Group metadata by prefix
        grouped = defaultdict(dict)
        for key, value in sorted(self.reader.metadata.items()):
            if '.' in key:
                prefix, subkey = key.split('.', 1)
                grouped[prefix][subkey] = value
            else:
                grouped['general'][key] = value
        
        for prefix, items in sorted(grouped.items()):
            print(f"\n  [{prefix}]")
            for key, value in sorted(items.items()):
                # Format value for display
                if isinstance(value, float):
                    value_str = f"{value:.4f}"
                elif isinstance(value, str) and len(value) > 60:
                    value_str = value[:57] + "..."
                else:
                    value_str = str(value)
                print(f"    {key:30s} = {value_str}")
    
    def print_architecture(self):
        """Print model architecture"""
        print("\n" + "=" * 70)
        print("🏗️  MODEL ARCHITECTURE")
        print("=" * 70)
        
        # Get architecture from metadata
        arch = self.reader.metadata.get('general.architecture', 'Unknown')
        model_type = self.reader.metadata.get('general.type', 'Unknown')
        
        print(f"\n  Architecture: {arch}")
        print(f"  Type: {model_type}")
        
        # Analyze tensor structure
        tensor_groups = self.summary['tensor_groups']
        
        print(f"\n  Layer Groups:")
        for group_name, tensors in sorted(tensor_groups.items()):
            group_params = sum(t['num_elements'] for t in tensors)
            print(f"    {group_name:20s} : {len(tensors):3d} tensors, {group_params:12,} params")
    
    def print_tensors(self, detailed=False, limit=None):
        """Print tensor information"""
        print("\n" + "=" * 70)
        print("🔢 TENSORS")
        print("=" * 70)
        
        # Header
        print(f"\n  {'Name':<40} {'Shape':<20} {'Type':<8} {'Elements':>12}")
        print("  " + "-" * 80)
        
        tensors_to_show = self.reader.tensors[:limit] if limit else self.reader.tensors
        
        for tensor in tensors_to_show:
            shape_str = str(tensor['shape'])
            name = tensor['name']
            if len(name) > 38:
                name = name[:35] + "..."
            
            print(f"  {name:<40} {shape_str:<20} {tensor['dtype']:<8} {tensor['num_elements']:>12,}")
            
            if detailed:
                print(f"    Offset: {tensor['offset']}, Dims: {tensor['dims']}")
        
        if limit and len(self.reader.tensors) > limit:
            remaining = len(self.reader.tensors) - limit
            print(f"\n  ... and {remaining} more tensors")
    
    def print_statistics(self):
        """Print statistical analysis"""
        print("\n" + "=" * 70)
        print("📊 STATISTICS")
        print("=" * 70)
        
        # Data type distribution
        dtype_counts = defaultdict(int)
        dtype_params = defaultdict(int)
        for tensor in self.reader.tensors:
            dtype_counts[tensor['dtype']] += 1
            dtype_params[tensor['dtype']] += tensor['num_elements']
        
        print("\n  Data Type Distribution:")
        print(f"  {'Type':<10} {'Tensors':>10} {'Parameters':>15} {'Percent':>10}")
        print("  " + "-" * 50)
        total_params = self.summary['total_parameters']
        for dtype in sorted(dtype_counts.keys()):
            count = dtype_counts[dtype]
            params = dtype_params[dtype]
            percent = (params / total_params * 100) if total_params > 0 else 0
            print(f"  {dtype:<10} {count:>10} {params:>15,} {percent:>9.1f}%")
        
        # Shape analysis
        print("\n  Tensor Shape Analysis:")
        shapes = [t['shape'] for t in self.reader.tensors]
        dims_count = defaultdict(int)
        for shape in shapes:
            dims_count[len(shape)] += 1
        
        for n_dims in sorted(dims_count.keys()):
            count = dims_count[n_dims]
            print(f"    {n_dims}D tensors: {count}")
        
        # Size analysis
        sizes = [t['num_elements'] for t in self.reader.tensors]
        if sizes:
            print(f"\n  Parameter Distribution:")
            print(f"    Smallest tensor: {min(sizes):,} elements")
            print(f"    Largest tensor:  {max(sizes):,} elements")
            print(f"    Average tensor:  {sum(sizes)//len(sizes):,} elements")
    
    def export_json(self, output_file: str):
        """Export analysis to JSON"""
        data = {
            'summary': self.summary,
            'metadata': self.reader.metadata,
            'tensors': [
                {
                    'name': t['name'],
                    'shape': t['shape'],
                    'dtype': t['dtype'],
                    'num_elements': t['num_elements'],
                }
                for t in self.reader.tensors
            ],
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✅ Exported analysis to: {output_file}")
    
    def export_markdown(self, output_file: str):
        """Export analysis to Markdown"""
        with open(output_file, 'w') as f:
            f.write(f"# GGUF Model Analysis\n\n")
            f.write(f"**File:** `{os.path.basename(self.summary['filename'])}`\n\n")
            f.write(f"**Size:** {self.summary['file_size_mb']:.2f} MB\n\n")
            f.write(f"**Version:** GGUF v{self.summary['version']}\n\n")
            
            f.write(f"## Summary\n\n")
            f.write(f"- **Tensors:** {self.summary['tensor_count']}\n")
            f.write(f"- **Parameters:** {self.summary['total_parameters']:,} ({self.summary['total_parameters_m']:.2f}M)\n")
            f.write(f"- **Metadata Entries:** {self.summary['metadata_count']}\n\n")
            
            f.write(f"## Metadata\n\n")
            for key, value in sorted(self.reader.metadata.items()):
                f.write(f"- **{key}:** {value}\n")
            
            f.write(f"\n## Architecture\n\n")
            tensor_groups = self.summary['tensor_groups']
            f.write(f"| Layer Group | Tensors | Parameters |\n")
            f.write(f"|-------------|---------|------------|\n")
            for group_name, tensors in sorted(tensor_groups.items()):
                group_params = sum(t['num_elements'] for t in tensors)
                f.write(f"| {group_name} | {len(tensors)} | {group_params:,} |\n")
            
            f.write(f"\n## Tensors\n\n")
            f.write(f"| Name | Shape | Type | Elements |\n")
            f.write(f"|------|-------|------|----------|\n")
            for tensor in self.reader.tensors:
                f.write(f"| {tensor['name']} | {tensor['shape']} | {tensor['dtype']} | {tensor['num_elements']:,} |\n")
        
        print(f"\n✅ Exported analysis to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Visualize GGUF model files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic overview
  python visualize_gguf.py model.gguf
  
  # Detailed view with all tensors
  python visualize_gguf.py model.gguf --detailed
  
  # Export to JSON and Markdown
  python visualize_gguf.py model.gguf --export-json analysis.json --export-md report.md
  
  # Show only metadata
  python visualize_gguf.py model.gguf --metadata-only
        """
    )
    
    parser.add_argument('file', help='GGUF file to visualize')
    parser.add_argument('--detailed', action='store_true', help='Show detailed tensor information')
    parser.add_argument('--limit', type=int, help='Limit number of tensors to display')
    parser.add_argument('--metadata-only', action='store_true', help='Show only metadata')
    parser.add_argument('--tensors-only', action='store_true', help='Show only tensors')
    parser.add_argument('--export-json', metavar='FILE', help='Export analysis to JSON')
    parser.add_argument('--export-md', metavar='FILE', help='Export analysis to Markdown')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    # Check file exists
    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        sys.exit(1)
    
    try:
        # Read GGUF file
        reader = GGUFReader(args.file)
        reader.read()
        
        # Create visualizer
        viz = GGUFVisualizer(reader)
        
        # Display information
        if not args.quiet:
            if not args.tensors_only:
                viz.print_overview()
                viz.print_metadata()
                viz.print_architecture()
            
            if not args.metadata_only:
                viz.print_tensors(detailed=args.detailed, limit=args.limit)
                viz.print_statistics()
        
        # Export if requested
        if args.export_json:
            viz.export_json(args.export_json)
        
        if args.export_md:
            viz.export_markdown(args.export_md)
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
