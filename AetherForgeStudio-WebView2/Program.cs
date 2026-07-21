using System.Runtime.InteropServices;

namespace AetherForgeStudio_WebView2;

static class Program
{
    [STAThread]
    static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new MainForm());
    }
}