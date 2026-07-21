using System.Collections.Generic;
namespace AetherForgeStudio.Models;
public class WorldSnapshot
{
    public int EntityCount { get; set; }
    public int RuleCount { get; set; }
    public int QuestCount { get; set; }
    public int WorldRevision { get; set; }
    public string Weather { get; set; } = "clear";
    public List<string> EntityNames { get; set; } = new();
}