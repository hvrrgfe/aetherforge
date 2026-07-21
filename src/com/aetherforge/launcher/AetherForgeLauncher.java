package com.aetherforge.launcher;

import com.aetherforge.util.Theme;
import javax.swing.*;

/**
 * AetherForge 启动器 — 主入口
 * 管理所有组件启动/停止、AI 模型下载
 */
public class AetherForgeLauncher {

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(new com.formdev.flatlaf.FlatDarkLaf());
            } catch (Exception ignored) {}

            LauncherWindow window = new LauncherWindow();
            window.setVisible(true);
        });
    }
}
