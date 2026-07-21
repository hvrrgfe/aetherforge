using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace AetherForgeStudio.ViewModels;

public class EntityNode
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public ObservableCollection<EntityNode> Children { get; set; } = new();
}

public class WorldViewModel : INotifyPropertyChanged
{
    public ObservableCollection<EntityNode> EntityTree { get; set; } = new();

    private int _entityCount = 0;
    private int _ruleCount = 0;
    private int _questCount = 0;
    private string _worldSummary = "";

    public int EntityCount { get => _entityCount; set { _entityCount = value; OnPropertyChanged(); } }
    public int RuleCount { get => _ruleCount; set { _ruleCount = value; OnPropertyChanged(); } }
    public int QuestCount { get => _questCount; set { _questCount = value; OnPropertyChanged(); } }
    public string WorldSummary { get => _worldSummary; set { _worldSummary = value; OnPropertyChanged(); } }

    public void RebuildTree(System.Collections.Generic.Dictionary<string, object> entities)
    {
        EntityTree.Clear();
        if (entities == null) return;
        foreach (var kvp in entities)
        {
            var e = kvp.Value as System.Collections.Generic.Dictionary<string, object>;
            var name = e?.ContainsKey("name") == true ? e["name"]?.ToString() ?? "" : kvp.Key;
            var type = e?.ContainsKey("semantic_type") == true ? e["semantic_type"]?.ToString() ?? "unknown" : "unknown";
            EntityTree.Add(new EntityNode { Id = kvp.Key, Name = name, Type = type });
        }
        OnPropertyChanged(nameof(EntityTree));
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    protected void OnPropertyChanged([CallerMemberName] string? name = null)
        => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}