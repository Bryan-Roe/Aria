# Unity Tools

## Apply PBR Materials
Menu: Tools > Characters > Apply PBR Materials

Reads `Assets/characters/characters_manifest.json` and assigns URP/Lit materials
with basecolor, normal, metallicsmoothness, occlusion, and emission maps.

Notes:
- Import normal maps as Normal Map in Unity.
- Metallic/smoothness should use R for metallic and A for smoothness.
- Make sure FBX files exist at the paths specified in the manifest.

## Apply Import Settings
Menu: Tools > Characters > Apply Import Settings

Sets model and texture import settings for FBX and PBR textures based on the manifest.

## Create LOD Prefabs
Menu: Tools > Characters > Create LOD Prefabs

Creates a prefab per character with an LODGroup using lod0/lod1/lod2 FBX files
from the manifest. Prefabs are saved to `Assets/characters/<id>/<id>.prefab`.
