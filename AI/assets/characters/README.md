# Stylized Humanoid Characters (Unity URP)

This folder defines the pipeline and placeholders for three stylized, game-ready humanoids
exported as FBX with PBR textures targeting Unity URP. No FBX meshes are included yet.

## Defaults
- Count: 3 characters (hero, scout, bruiser)
- Target: 15k-25k tris per LOD0
- Textures: 2K PBR per character (basecolor, normal, metallic/smoothness, occlusion, emission)
- Rig: Unity Humanoid compatible, T-pose
- Pipeline: Unity URP

## Directory Layout
- hero/, scout/, bruiser/
  - textures/: PBR texture placeholders
  - model/: reserved for FBX exports
- briefs/: art and modeling briefs for each character

## Naming
- FBX: <character>_lod0.fbx, <character>_lod1.fbx (optional)
- Textures: <character>_<map>.png
  - basecolor, normal, metallicsmoothness, occlusion, emission, mask

## Unity Import Notes (URP)
- Scale: 1 unit = 1 meter
- Axis: Forward = -Z, Up = Y
- Rig: Humanoid, root bone at hips
- Materials: URP/Lit
- Metallic/Smoothness: metallic in R, smoothness in A
- Normal map: marked as Normal Map in Unity import settings

## Placeholder Textures
Textures are 1x1 PNG placeholders so the structure is valid. Replace with authored 2K maps.

## Next Steps
1) Model and retopo in Blender or Maya per the briefs.
2) UV unwrap and texture (Substance, Blender, or equivalent).
3) Export FBX with correct scale, axes, and humanoid rig.
4) Import into Unity, assign URP/Lit materials, verify Humanoid rig.

## LOD Guidance
- LOD0: 15k-25k tris (per brief)
- LOD1: 50% of LOD0
- LOD2: 25% of LOD0 (optional)

## Tools
- Unity material assigner: `assets/characters/tools/unity/ApplyCharacterMaterials.cs`
- Blender export checklist: `assets/characters/briefs/blender_export_checklist.md`
- Shared palette: `assets/characters/briefs/palette.md`

## Model Folder Structure
Each character has LOD folders:
- model/lod0/<character>_lod0.fbx
- model/lod1/<character>_lod1.fbx
- model/lod2/<character>_lod2.fbx

## Unity Prefab Generation
- Run `Tools > Characters > Create LOD Prefabs` to build prefabs with LODGroup.
- Prefabs save to `Assets/characters/<id>/<id>.prefab`.
