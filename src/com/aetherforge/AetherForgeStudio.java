package com.aetherforge;

import com.aetherforge.ui.MainWindow;
import com.aetherforge.util.Colors;
import com.aetherforge.util.Theme;
import javax.swing.*;

/**
 * AetherForge Studio entry point.
 * Uses FlatLaf for professional dark/light theme.
 */
public class AetherForgeStudio {
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                // use FlatLaf Dark as default
                com.formdev.flatlaf.FlatDarkLaf.setup();
                Colors.updateTheme();
            } catch (Exception e) {
                try { UIManager.setLookAndFeel(UIManager.getCrossPlatformLookAndFeelClassName()); }
                catch (Exception ignored) {}
            }
            new MainWindow().setVisible(true);
        });
    }
}