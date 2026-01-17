#!/usr/bin/env python3
"""
Simplified GGUF File Visualizer - Working Version

Quick visualizer for the custom GGUF format used by the quantum AI models.
Matches the exact format from export_quantum_to_gguf.py
"""

import struct
import json
import os
import sys
from collections import defaultdict


def read_string(f):
    """Read a string (u32 length + bytes)"""
    length = struct.unpack('<I', f.read(4))[0]
    return f.read(length).decode('utf-8')


def read_metadata_value(f, value_type):
    """Read a metadata value based on type"""
    if value_type == 3:  # string
        length = struct.unpack('<Q', f.read(8))[0]
        return f.read(length).decode('utf-8')
    elif value_type == 4:  # f32
        return struct.unpack('<f', f.read(4))[0]
    elif value_type == 7:  # i64
        return struct.unpack('<q', f.read(8))[0]
    else:
        return f"<Unknown type {value_type}>"


def parse_gguf(filename):
    """Parse GGUF file"""
    with open(filename, 'rb') as f:
        # Read header
        magic = struct.unpack('<I', f.read(4))[0]
        if magic != 0x46554747:
            raise ValueError(f"Invalid magic: 0x{magic:08X}")
        
        version = struct.unpack('<I', f.read(4))[0]
        endian = struct.unpack('<I', f.read(4))[0]
        metadata_count = struct.unpack('<Q', f.read(8))[0]
        
        print(f"📖 GGUF v{version} (endian={endian})")
        print(f"📊 Metadata entries: {metadata_count}")
        
        # Read metadata
        metadata = {}
        for i in range(metadata_count):
            key = read_string(f)
            value_type = struct.unpack('<I', f.read(4))[0]
            value = read_metadata_value(f, value_type)
            metadata[key] = value
        
        # Read tensor count
        tensor_count = struct.unpack('<Q', f.read(8))[0]
        print(f"🔢 Tensors: {tensor_count}")
        
        # Read tensors
        tensors = []
        for i in range(tensor_count):
            name = read_string(f)
            n_dims = struct.unpack('<I', f.read(4))[0]
            
            dims = []
            for _ in range(n_dims):
                dims.append(struct.unpack('<Q', f.read(8))[0])
            
            dtype = struct.unpack('<I', f.read(4))[0]
            offset = struct.unpack('<Q', f.read(8))[0]
            
            num_elements = 1
            for dim in dims:
                num_elements *= dim
            
            tensors.append({
                'name': name,
                'dims': dims,
                'dtype': dtype,
                'offset': offset,
                'num_elements': num_elements
            })
        
        return {
            'filename': filename,
            'file_size': os.path.getsize(filename),
            'version': version,
            'metadata': metadata,
            'tensors': tensors
        }


def print_overview(data):
    """Print overview"""
    print("\n" + "=" * 70)
    print("📦 GGUF FILE OVERVIEW")
    print("=" * 70)
    
    total_params = sum(t['num_elements'] for t in data['tensors'])
    file_size_mb = data['file_size'] / (1024 * 1024)
    
    print(f"\n📄 File: {os.path.basename(data['filename'])}")
    print(f"📏 Size: {file_size_mb:.2f} MB ({data['file_size']:,} bytes)")
    print(f"🔢 Version: GGUF v{data['version']}")
    print(f"🧱 Tensors: {len(data['tensors'])}")
    print(f"📊 Parameters: {total_params:,} ({total_params/1_000_000:.2f}M)")
    print(f"🏷️  Metadata: {len(data['metadata'])} entries")


def print_metadata(data):
    """Print metadata"""
    print("\n" + "=" * 70)
    print("🏷️  METADATA")
    print("=" * 70)
    
    for key, value in sorted(data['metadata'].items()):
        # Format value
        if isinstance(value, float):
            value_str = f"{value:.4f}"
        elif isinstance(value, str) and len(value) > 50:
            value_str = value[:47] + "..."
        else:
            value_str = str(value)
        
        print(f"  {key:30s} = {value_str}")


def print_architecture(data):
    """Print architecture"""
    print("\n" + "=" * 70)
    print("🏗️  MODEL ARCHITECTURE")
    print("=" * 70)
    
    # Group tensors by layer
    groups = defaultdict(list)
    for tensor in data['tensors']:
        parts = tensor['name'].split('.')
        group = parts[0] if len(parts) > 1 else 'other'
        groups[group].append(tensor)
    
    total_params = sum(t['num_elements'] for t in data['tensors'])
    
    print(f"\n  Layer Groups:")
    for group, tensors in sorted(groups.items()):
        group_params = sum(t['num_elements'] for t in tensors)
        percent = (group_params / total_params * 100) if total_params > 0 else 0
        print(f"    {group:20s} : {len(tensors):3d} tensors, {group_params:12,} params ({percent:5.1f}%)")


def print_tensors(data, limit=None):
    """Print tensor list"""
    print("\n" + "=" * 70)
    print("🔢 TENSORS")
    print("=" * 70)
    
    dtype_names = {0: 'F32', 1: 'F16', 2: 'Q4_0'}
    
    print(f"\n  {'Name':<40} {'Shape':<20} {'Type':<8} {'Elements':>12}")
    print("  " + "-" * 80)
    
    tensors_to_show = data['tensors'][:limit] if limit else data['tensors']
    
    for tensor in tensors_to_show:
        name = tensor['name']
        if len(name) > 38:
            name = name[:35] + "..."
        
        shape_str = str(tuple(tensor['dims']))
        dtype_str = dtype_names.get(tensor['dtype'], f"Type{tensor['dtype']}")
        
        print(f"  {name:<40} {shape_str:<20} {dtype_str:<8} {tensor['num_elements']:>12,}")
    
    if limit and len(data['tensors']) > limit:
        print(f"\n  ... and {len(data['tensors']) - limit} more tensors")


def print_statistics(data):
    """Print statistics"""
    print("\n" + "=" * 70)
    print("📊 STATISTICS")
    print("=" * 70)
    
    # Data type distribution
    dtype_names = {0: 'F32', 1: 'F16', 2: 'Q4_0'}
    dtype_count = defaultdict(int)
    dtype_params = defaultdict(int)
    
    for tensor in data['tensors']:
        dtype_name = dtype_names.get(tensor['dtype'], f"Type{tensor['dtype']}")
        dtype_count[dtype_name] += 1
        dtype_params[dtype_name] += tensor['num_elements']
    
    total_params = sum(t['num_elements'] for t in data['tensors'])
    
    print("\n  Data Type Distribution:")
    print(f"  {'Type':<10} {'Tensors':>10} {'Parameters':>15} {'Percent':>10}")
    print("  " + "-" * 50)
    
    for dtype in sorted(dtype_count.keys()):
        count = dtype_count[dtype]
        params = dtype_params[dtype]
        percent = (params / total_params * 100) if total_params > 0 else 0
        print(f"  {dtype:<10} {count:>10} {params:>15,} {percent:>9.1f}%")
    
    # Size stats
    sizes = [t['num_elements'] for t in data['tensors']]
    if sizes:
        print(f"\n  Parameter Distribution:")
        print(f"    Smallest tensor: {min(sizes):,} elements")
        print(f"    Largest tensor:  {max(sizes):,} elements")
        print(f"    Average tensor:  {sum(sizes)//len(sizes):,} elements")


def export_json(data, output_file):
    """Export to JSON"""
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n✅ Exported to: {output_file}")


def export_markdown(data, output_file):
    """Export to Markdown"""
    total_params = sum(t['num_elements'] for t in data['tensors'])
    file_size_mb = data['file_size'] / (1024 * 1024)
    
    with open(output_file, 'w') as f:
        f.write(f"# GGUF Model Analysis\n\n")
        f.write(f"**File:** `{os.path.basename(data['filename'])}`\n\n")
        f.write(f"**Size:** {file_size_mb:.2f} MB\n\n")
        f.write(f"**Parameters:** {total_params:,}\n\n")
        
        f.write(f"## Metadata\n\n")
        for key, value in sorted(data['metadata'].items()):
            f.write(f"- **{key}:** {value}\n")
        
        f.write(f"\n## Tensors\n\n")
        f.write(f"| Name | Shape | Type | Elements |\n")
        f.write(f"|------|-------|------|----------|\n")
        
        dtype_names = {0: 'F32', 1: 'F16', 2: 'Q4_0'}
        for tensor in data['tensors']:
            dtype_str = dtype_names.get(tensor['dtype'], f"Type{tensor['dtype']}")
            f.write(f"| {tensor['name']} | {tuple(tensor['dims'])} | {dtype_str} | {tensor['num_elements']:,} |\n")
    
    print(f"\n✅ Exported to: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_gguf_simple.py <file.gguf> [--json output.json] [--md output.md]")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        sys.exit(1)
    
    try:
        # Parse file
        data = parse_gguf(filename)
        
        # Display
        print_overview(data)
        print_metadata(data)
        print_architecture(data)
        print_tensors(data, limit=20)
        print_statistics(data)
        
        # Export if requested
        if '--json' in sys.argv:
            idx = sys.argv.index('--json')
            if idx + 1 < len(sys.argv):
                export_json(data, sys.argv[idx + 1])
        
        if '--md' in sys.argv:
            idx = sys.argv.index('--md')
            if idx + 1 < len(sys.argv):
                export_markdown(data, sys.argv[idx + 1])
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
