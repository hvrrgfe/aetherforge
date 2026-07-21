package com.aetherforge.model;

/**
 * 命令接口 — 撤销/重做模式
 * Scene 通过 executeCommand() 统一管理命令生命周期
 */
public interface Command {
    void execute();
    void undo();
    String getName();
}
