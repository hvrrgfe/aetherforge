using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
namespace AetherForgeStudio.Pages;
public sealed partial class DashboardPage : Page
{
    public DashboardPage() { this.InitializeComponent(); }
    private void RefreshBtn_Click(object sender, RoutedEventArgs e)
    {
        EntityCount.Text = "已刷新";
    }
}
