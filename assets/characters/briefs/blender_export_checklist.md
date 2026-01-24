# Blender Export Checklist (FBX for Unity)

## Scene Setup
- Units: Metric, Unit Scale = 1.0
- Apply scale so 1 unit = 1 meter
- Forward: -Z, Up: Y

## Mesh
- Apply all transforms (Ctrl+A)
- Triangulate on export (or keep quads if engine allows)
- Check for flipped normals and non-manifold geometry
- UVs: no overlaps (unless intentional), consistent texel density

## Rig
- Armature in T-pose
- Root bone at hips
- No unapplied scale on armature
- Bone roll consistent

## Export (FBX)
- Selected Objects only
- Apply Transform: enabled
- Add Leaf Bones: disabled
- Bake Animation: off (unless needed)
- Smoothing: Face
- Path Mode: Copy (or Auto)

## Validation
- Re-import FBX into a clean Blender file to verify scale and rig
- Check a test import in Unity for Humanoid mapping
