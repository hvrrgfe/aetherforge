using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using AetherForgeStudio.ViewModels;

namespace AetherForgeStudio.Pages;

public sealed partial class WorldPage : Page
{
    public WorldViewModel ViewModel { get; } = new();

    public WorldPage()
    {
        this.InitializeComponent();
    }
}