using Microsoft.UI.Xaml;
using System.Globalization;

namespace AetherForgeStudio;
public partial class App : Application
{
    public App()
    {
        // 设置默认语言为中文
        CultureInfo.CurrentUICulture = new CultureInfo("zh-CN");
        CultureInfo.CurrentCulture = new CultureInfo("zh-CN");
        
        InitializeComponent();
    }
    protected override void OnLaunched(Microsoft.UI.Xaml.LaunchActivatedEventArgs args)
    {
        m_window = new MainWindow();
        m_window.Activate();
    }
    private Window m_window = null!;
}
