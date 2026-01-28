using System.IO;
using UnityEditor;
using UnityEngine;

public static class ApplyCharacterImportSettings
{
    [MenuItem("Tools/Characters/Apply Import Settings")]
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
            ApplyModelSettings(NormalizeAssetPath(character.fbx));
            ApplyTextureSettings(character.textures);
        }

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Applied character import settings.");
    }

    private static void ApplyModelSettings(string fbxPath)
    {
        var importer = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
        if (importer == null)
        {
            Debug.LogWarning("Model importer not found for: " + fbxPath);
            return;
        }

        importer.globalScale = 1.0f;
        importer.useFileScale = true;
        importer.animationType = ModelImporterAnimationType.None;
        importer.isReadable = false;
        importer.importBlendShapes = false;
        importer.importCameras = false;
        importer.importLights = false;
        importer.importVisibility = false;
        importer.importBlendShapeNormals = ModelImporterNormals.Import;
        importer.meshCompression = ModelImporterMeshCompression.Medium;
        importer.importTangents = ModelImporterTangents.CalculateMikk;
        importer.SaveAndReimport();
    }

    private static void ApplyTextureSettings(TextureSet textures)
    {
        SetTextureType(textures.basecolor, TextureImporterType.Default, false, false);
        SetTextureType(textures.normal, TextureImporterType.NormalMap, false, false);
        SetTextureType(textures.metallicsmoothness, TextureImporterType.Default, true, false);
        SetTextureType(textures.occlusion, TextureImporterType.Default, true, false);
        SetTextureType(textures.emission, TextureImporterType.Default, false, true);
    }

    private static void SetTextureType(string path, TextureImporterType type, bool sRGBOff, bool enableAlpha)
    {
        var assetPath = NormalizeAssetPath(path);
        var importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
        if (importer == null)
        {
            Debug.LogWarning("Texture importer not found for: " + assetPath);
            return;
        }

        importer.textureType = type;
        importer.sRGBTexture = !sRGBOff;
        importer.alphaSource = enableAlpha ? TextureImporterAlphaSource.FromInput : TextureImporterAlphaSource.None;
        importer.alphaIsTransparency = false;
        importer.mipmapEnabled = true;
        importer.SaveAndReimport();
    }

    private static string NormalizeAssetPath(string path)
    {
        if (path.StartsWith("Assets/"))
        {
            return path;
        }

        return path.Replace("/workspaces/AI/", "Assets/").Replace("assets/", "Assets/");
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
