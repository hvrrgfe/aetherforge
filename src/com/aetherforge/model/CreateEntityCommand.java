package com.aetherforge.model;

import com.aetherforge.util.I18n;

/**
 * 创建实体命令
 */
public class CreateEntityCommand implements Command {
    private final Scene scene;
    private Entity entity;
    private final String entityType;
    private final String entityName;

    public CreateEntityCommand(Scene scene, String type, String name) {
        this.scene = scene;
        this.entityType = type;
        this.entityName = name;
    }

    @Override
    public void execute() {
        if (entity == null) {
            entity = new Entity(entityType, entityName);
        }
        scene.addEntity(entity);
        scene.setSelectedEntity(entity);
    }

    @Override
    public void undo() {
        if (entity != null) {
            scene.removeEntity(entity);
        }
    }

    @Override
    public String getName() {
        return I18n.get("log.created") + ": " + (entity != null ? entity.getId() : "");
    }
}
