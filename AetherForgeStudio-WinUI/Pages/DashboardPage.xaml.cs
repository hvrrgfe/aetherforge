using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using AetherForgeStudio.Services;
namespace AetherForgeStudio.Pages;
public sealed partial class DashboardPage : Page
{
    private readonly AetherForgeApiService _api = new();
    public DashboardPage() { this.InitializeComponent(); }
    private async void RefreshBtn_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            var json = await _api.GetWorldStateAsync();
            EntityCount.Text = "?...?";  // Parsed from JSON
        }
        catch { EntityCount.Text = "ERR"; }
    }
}