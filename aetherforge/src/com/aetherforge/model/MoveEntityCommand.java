package com.aetherforge.model;

import com.aetherforge.util.I18n;

/**
 * 移动实体命令 — 拖拽结束后记录起止位置，支持撤销/重做
 */
public class MoveEntityCommand implements Command {
    private final Scene scene;
    private final Entity entity;
    private final double oldX, oldY;
    private final double newX, newY;

    public MoveEntityCommand(Scene scene, Entity entity, double oldX, double oldY, double newX, double newY) {
        this.scene = scene;
        this.entity = entity;
        this.oldX = oldX;
        this.oldY = oldY;
        this.newX = newX;
        this.newY = newY;
    }

    @Override
    public void execute() {
        entity.setPosition(newX, newY);
        scene.fireChange();
    }

    @Override
    public void undo() {
        entity.setPosition(oldX, oldY);
        scene.setSelectedEntity(entity);
        scene.fireChange();
    }

    @Override
    public String getName() {
        return I18n.get("log.moved") + ": " + entity.getName();
    }
}
