using System.IO;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

public static class CreateCharacterPrefabs
{
    [MenuItem("Tools/Characters/Create LOD Prefabs")]
    public static void CreatePrefabs()
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
            CreatePrefabForCharacter(character);
        }

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Created character prefabs with LODGroup.");
    }

    private static void CreatePrefabForCharacter(CharacterEntry character)
    {
        var lodModels = new List<GameObject>();
        var lodPaths = new List<string>();

        AddLodModel(character.lods.lod0, lodModels, lodPaths);
        AddLodModel(character.lods.lod1, lodModels, lodPaths);
        AddLodModel(character.lods.lod2, lodModels, lodPaths);

        if (lodModels.Count == 0)
        {
            Debug.LogWarning("No LOD models found for: " + character.id);
            return;
        }

        var root = new GameObject(character.id + "_prefab");
        var lodGroup = root.AddComponent<LODGroup>();

        var lods = new LOD[lodModels.Count];
        for (var i = 0; i < lodModels.Count; i++)
        {
            var modelInstance = PrefabUtility.InstantiatePrefab(lodModels[i]) as GameObject;
            if (modelInstance == null)
            {
                continue;
            }

            modelInstance.name = lodModels[i].name;
            modelInstance.transform.SetParent(root.transform, false);

            var renderers = modelInstance.GetComponentsInChildren<SkinnedMeshRenderer>(true);
            lods[i] = new LOD(GetScreenRelativeTransitionHeight(i), renderers);
        }

        lodGroup.SetLODs(lods);
        lodGroup.RecalculateBounds();

        var prefabPath = "Assets/characters/" + character.id + "/" + character.id + ".prefab";
        PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
        Object.DestroyImmediate(root);

        Debug.Log("Created prefab: " + prefabPath);
    }

    private static void AddLodModel(string path, List<GameObject> models, List<string> paths)
    {
        if (string.IsNullOrEmpty(path))
        {
            return;
        }

        var assetPath = NormalizeAssetPath(path);
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
        if (model == null)
        {
            return;
        }

        models.Add(model);
        paths.Add(assetPath);
    }

    private static float GetScreenRelativeTransitionHeight(int index)
    {
        if (index == 0)
        {
            return 0.6f;
        }
        if (index == 1)
        {
            return 0.3f;
        }
        return 0.1f;
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
        public LodSet lods;
    }

    [System.Serializable]
    private class LodSet
    {
        public string lod0;
        public string lod1;
        public string lod2;
    }
}
