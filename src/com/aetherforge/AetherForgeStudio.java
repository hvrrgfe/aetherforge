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
            setupCJKFont();
            new MainWindow().setVisible(true);
        });
    }

    /**
     * 设置支持中文的全局字体（FlatLaf 默认 Inter/Segoe UI 缺少 CJK 字形）
     */
    public static void setupCJKFont() {
        try {
            String[] fallback = {"Microsoft YaHei UI", "Microsoft YaHei", "SimSun", "SimHei"};
            Font uiFont = null;
            GraphicsEnvironment ge = GraphicsEnvironment.getLocalGraphicsEnvironment();
            Font[] all = ge.getAllFonts();

            for (String name : fallback) {
                for (Font f : all) {
                    if (f.getFamily().equals(name) || f.getName().equals(name)) {
                        uiFont = f.deriveFont(Font.PLAIN, 13f);
                        break;
                    }
                }
                if (uiFont != null && uiFont.canDisplay('中')) break;
                // 直接尝试创建
                uiFont = new Font(name, Font.PLAIN, 13);
                if (uiFont.canDisplay('中') && uiFont.canDisplay('文')) break;
                uiFont = null;
            }
            if (uiFont == null) uiFont = new Font("Microsoft YaHei UI", Font.PLAIN, 13);

            javax.swing.plaf.FontUIResource fur = new javax.swing.plaf.FontUIResource(uiFont);
            UIManager.put("defaultFont", fur);
            UIManager.put("TextField.font", fur);
            UIManager.put("TextArea.font", fur);
            UIManager.put("Tree.font", fur);
            UIManager.put("Label.font", fur);
            UIManager.put("Button.font", fur);
            UIManager.put("ToggleButton.font", fur);
            UIManager.put("Menu.font", fur);
            UIManager.put("MenuItem.font", fur);
            UIManager.put("PopupMenu.font", fur);
            UIManager.put("ComboBox.font", fur);
            UIManager.put("CheckBox.font", fur);
            UIManager.put("RadioButton.font", fur);
            UIManager.put("Table.font", fur);
            UIManager.put("TableHeader.font", fur);
            UIManager.put("ToolTip.font", fur);
            UIManager.put("List.font", fur);
            UIManager.put("EditorPane.font", fur);
            UIManager.put("OptionPane.font", fur);
            UIManager.put("OptionPane.messageFont", fur);
            UIManager.put("OptionPane.buttonFont", fur);
            UIManager.put("ProgressBar.font", fur);
            UIManager.put("TabbedPane.font", fur);
            UIManager.put("ToolBar.font", fur);
            UIManager.put("Spinner.font", fur);
        } catch (Exception ignored) {}
    }
}
