using System.IO;
using UnityEditor;
using UnityEngine;

public static class ApplyCharacterMaterials
{
    [MenuItem("Tools/Characters/Apply PBR Materials")]
    public static void Apply()
    {
        var manifestPath = "Assets/characters/characters_manifest.json";
        if (!File.Exists(manifestPath))
        {
            Debug.LogError("Manifest not found: " + manifestPath);
            return;
        }

        var json = File.ReadAllText(manifestPath);
        var data = JsonUtility.FromJson<CharacterManifest>(json);
        if (data == null || data.characters == null)
        {
            Debug.LogError("Invalid manifest.");
            return;
        }

        foreach (var character in data.characters)
        {
            var fbxPath = NormalizeAssetPath(character.fbx);
            var basecolor = LoadTexture(character.textures.basecolor);
            var normal = LoadTexture(character.textures.normal);
            var metallicsmoothness = LoadTexture(character.textures.metallicsmoothness);
            var occlusion = LoadTexture(character.textures.occlusion);
            var emission = LoadTexture(character.textures.emission);

            var materialPath = "Assets/characters/" + character.id + "/" + character.id + "_mat.mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
            if (material == null)
            {
                material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                AssetDatabase.CreateAsset(material, materialPath);
            }

            material.SetTexture("_BaseMap", basecolor);
            material.SetTexture("_BumpMap", normal);
            material.SetTexture("_MetallicGlossMap", metallicsmoothness);
            material.SetTexture("_OcclusionMap", occlusion);
            material.SetTexture("_EmissionMap", emission);
            material.EnableKeyword("_NORMALMAP");
            material.EnableKeyword("_METALLICSPECGLOSSMAP");
            material.EnableKeyword("_OCCLUSIONMAP");
            material.EnableKeyword("_EMISSION");

            AssignMaterialToModel(fbxPath, material);
        }

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Applied character materials.");
    }

    private static Texture2D LoadTexture(string path)
    {
        return AssetDatabase.LoadAssetAtPath<Texture2D>(NormalizeAssetPath(path));
    }

    private static string NormalizeAssetPath(string path)
    {
        if (path.StartsWith("Assets/"))
        {
            return path;
        }

        return path.Replace("/workspaces/AI/", "Assets/").Replace("assets/", "Assets/");
    }

    private static void AssignMaterialToModel(string fbxPath, Material material)
    {
        var importer = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
        if (importer == null)
        {
            Debug.LogWarning("Model importer not found for: " + fbxPath);
            return;
        }

        importer.materialImportMode = ModelImporterMaterialImportMode.None;
        importer.SaveAndReimport();

        var model = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
        if (model == null)
        {
            Debug.LogWarning("Model not found at: " + fbxPath);
            return;
        }

        var renderer = model.GetComponentInChildren<SkinnedMeshRenderer>();
        if (renderer == null)
        {
            Debug.LogWarning("SkinnedMeshRenderer not found for: " + fbxPath);
            return;
        }

        var mats = new Material[renderer.sharedMaterials.Length];
        for (var i = 0; i < mats.Length; i++)
        {
            mats[i] = material;
        }
        renderer.sharedMaterials = mats;
        EditorUtility.SetDirty(renderer);
    }

    [System.Serializable]
    private class CharacterManifest
    {
        public CharacterEntry[] characters;
    }

    [System.Serializable]
    private class CharacterEntry
    {
        public string id;
        public string fbx;
        public TextureSet textures;
    }

    [System.Serializable]
    private class TextureSet
    {
        public string basecolor;
        public string normal;
        public string metallicsmoothness;
        public string occlusion;
        public string emission;
    }
}
