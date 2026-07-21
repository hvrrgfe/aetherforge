package com.aetherforge;

import com.aetherforge.ui.MainWindow;
import com.aetherforge.util.Colors;
import com.aetherforge.util.Theme;
import javax.swing.*;
import java.awt.*;

/**
 * AetherForge Studio 入口
 * 使用 FlatLaf 专业暗色主题，默认中文支持
 */
public class AetherForgeStudio {
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                com.formdev.flatlaf.FlatDarkLaf.setup();
                setupCJKFont();
                Colors.updateTheme();
            } catch (Exception e) {
                try { UIManager.setLookAndFeel(UIManager.getCrossPlatformLookAndFeelClassName()); }
                catch (Exception ignored) {}
            }
            new MainWindow().setVisible(true);
        });
    }

    /**
     * 设置支持中文的全局字体（FlatLaf 默认 Inter/Segoe UI 缺少 CJK 字形）
     */
    private static javax.swing.plaf.FontUIResource cjkFont;

    public static void setupCJKFont() {
        try {
            if (cjkFont == null) {
                String[] fallback = {"Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "SimSun"};
                Font uiFont = null;
                for (String name : fallback) {
                    uiFont = new Font(name, Font.PLAIN, 13);
                    if (uiFont.canDisplay('中') && uiFont.canDisplay('文')) break;
                    uiFont = null;
                }
                if (uiFont == null) uiFont = new Font("Microsoft YaHei UI", Font.PLAIN, 13);
                cjkFont = new javax.swing.plaf.FontUIResource(uiFont);
            }
            // 每次全量设置，确保 FlatLaf 重置后所有组件都有 CJK 字体
            for (String key : new String[]{"defaultFont","TextField.font","TextArea.font","Tree.font",
                "Label.font","Button.font","ToggleButton.font","Menu.font","MenuItem.font",
                "PopupMenu.font","ComboBox.font","CheckBox.font","RadioButton.font","Table.font",
                "TableHeader.font","ToolTip.font","List.font","EditorPane.font","OptionPane.font",
                "OptionPane.messageFont","OptionPane.buttonFont","ProgressBar.font","TabbedPane.font",
                "ToolBar.font","Spinner.font"}) {
                UIManager.put(key, cjkFont);
            }
        } catch (Exception e) {
            System.err.println("[Font] CJK setup failed: " + e.getMessage());
        }
    }
}
