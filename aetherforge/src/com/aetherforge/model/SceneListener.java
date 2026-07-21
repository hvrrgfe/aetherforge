package com.aetherforge.model;

/**
 * 场景变更监听器 — 解耦 Viewport 和 MainWindow
 * Scene 持有 List<SceneListener>，各 UI 组件注册监听
 */
public interface SceneListener {
    default void sceneChanged() {}
    default void selectionChanged(Entity selected) {}
    default void logMessage(String msg) {}
}
