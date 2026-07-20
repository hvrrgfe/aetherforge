package com.aetherforge.model;

import com.aetherforge.util.I18n;

/**
 * 删除实体命令
 */
public class DeleteEntityCommand implements Command {
    private final Scene scene;
    private final Entity entity;
    private final int index;

    public DeleteEntityCommand(Scene scene, Entity entity) {
        this.scene = scene;
        this.entity = entity;
        this.index = scene.getEntities().indexOf(entity);
    }

    @Override
    public void execute() {
        scene.removeEntity(entity);
    }

    @Override
    public void undo() {
        if (index >= 0 && index <= scene.getEntities().size()) {
            scene.getEntities().add(index, entity);
        } else {
            scene.addEntity(entity);
        }
        scene.setSelectedEntity(entity);
        scene.fireChange();
    }

    @Override
    public String getName() {
        return I18n.get("log.deleted") + ": " + entity.getName();
    }
}
