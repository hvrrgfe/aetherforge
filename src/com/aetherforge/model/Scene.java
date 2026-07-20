package com.aetherforge.model;

import com.aetherforge.util.I18n;
import java.util.*;

/**
 * 场景数据模型 — 实体管理 + 事件监听 + 撤销/重做栈
 * Viewport 和 MainWindow 都依赖此模型而非互相依赖
 */
public class Scene {

    // ─── 数据 ───
    private final List<Entity> entities = new ArrayList<>();
    private Entity selectedEntity;
    private final Set<Entity> multiSelected = new HashSet<>();
    private double cameraX, cameraY, cameraZoom = 1.0;

    // ─── 事件监听 ───
    private final List<SceneListener> listeners = new ArrayList<>();

    // ─── 撤销/重做 ───
    private final Deque<Command> undoStack = new ArrayDeque<>();
    private final Deque<Command> redoStack = new ArrayDeque<>();
    private static final int MAX_UNDO = 100;

    // ═══════════════════════════════════════════════════════════
    //  监听器
    // ═══════════════════════════════════════════════════════════

    public void addListener(SceneListener l) { listeners.add(l); }
    public void removeListener(SceneListener l) { listeners.remove(l); }

    public void fireChange() {
        for (SceneListener l : listeners) l.sceneChanged();
    }
    public void fireSelection() {
        for (SceneListener l : listeners) l.selectionChanged(selectedEntity);
    }
    public void fireLog(String msg) {
        for (SceneListener l : listeners) l.logMessage(msg);
    }

    // ═══════════════════════════════════════════════════════════
    //  实体 CRUD
    // ═══════════════════════════════════════════════════════════

    public List<Entity> getEntities() { return entities; }

    public void addEntity(Entity e) {
        entities.add(e);
        fireChange();
    }

    public void removeEntity(Entity e) {
        entities.remove(e);
        if (selectedEntity == e) selectedEntity = null;
        multiSelected.remove(e);
        fireChange();
        fireSelection();
    }

    public Entity getSelectedEntity() { return selectedEntity; }

    public void setSelectedEntity(Entity e) {
        selectedEntity = e;
        multiSelected.clear();
        if (e != null) multiSelected.add(e);
        fireSelection();
    }

    public void addToSelection(Entity e) {
        if (e == null) return;
        if (multiSelected.contains(e)) {
            multiSelected.remove(e);
            if (multiSelected.isEmpty()) selectedEntity = null;
        } else {
            multiSelected.add(e);
            selectedEntity = e;
        }
        fireSelection();
    }

    public Set<Entity> getMultiSelected() { return Collections.unmodifiableSet(multiSelected); }

    public boolean isSelected(Entity e) { return multiSelected.contains(e); }

    public void clearSelection() {
        selectedEntity = null;
        multiSelected.clear();
        fireSelection();
    }

    // ═══════════════════════════════════════════════════════════
    //  相机
    // ═══════════════════════════════════════════════════════════

    public double getCameraX() { return cameraX; }
    public double getCameraY() { return cameraY; }
    public double getCameraZoom() { return cameraZoom; }

    public void moveCamera(double dx, double dy) {
        cameraX += dx;
        cameraY += dy;
        fireChange();
    }

    public void zoomCamera(double factor) {
        cameraZoom = Math.max(0.05, Math.min(20, cameraZoom * factor));
        fireChange();
    }

    public void resetCamera() {
        cameraX = 0;
        cameraY = 0;
        cameraZoom = 1.0;
        fireChange();
    }

    // ═══════════════════════════════════════════════════════════
    //  撤销/重做
    // ═══════════════════════════════════════════════════════════

    public void executeCommand(Command cmd) {
        cmd.execute();
        undoStack.addLast(cmd);
        if (undoStack.size() > MAX_UNDO) undoStack.removeFirst();
        redoStack.clear();
        fireChange();
        fireLog(cmd.getName());
    }

    public void undo() {
        if (undoStack.isEmpty()) return;
        Command cmd = undoStack.removeLast();
        cmd.undo();
        redoStack.addLast(cmd);
        fireChange();
        fireSelection();
        fireLog(I18n.get("log.undo") + ": " + cmd.getName());
    }

    public void redo() {
        if (redoStack.isEmpty()) return;
        Command cmd = redoStack.removeLast();
        cmd.execute();
        undoStack.addLast(cmd);
        fireChange();
        fireSelection();
        fireLog(I18n.get("log.redo") + ": " + cmd.getName());
    }

    public boolean canUndo() { return !undoStack.isEmpty(); }
    public boolean canRedo() { return !redoStack.isEmpty(); }
    public String getUndoName() { return undoStack.isEmpty() ? "" : undoStack.getLast().getName(); }
    public String getRedoName() { return redoStack.isEmpty() ? "" : redoStack.getLast().getName(); }

    // ═══════════════════════════════════════════════════════════
    //  JSON 序列化
    // ═══════════════════════════════════════════════════════════

    public String toJson() {
        return com.aetherforge.util.SceneSerializer.toJson(this);
    }

    public static Scene fromJson(String json) {
        return com.aetherforge.util.SceneSerializer.fromJson(json);
    }
}