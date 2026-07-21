package com.aetherforge.model;

import com.aetherforge.util.I18n;
import java.util.*;

/**
 * 鍦烘櫙鏁版嵁妯″瀷 鈥?瀹炰綋绠＄悊 + 浜嬩欢鐩戝惉 + 鎾ら攢/閲嶅仛鏍?
 * Viewport 鍜?MainWindow 閮戒緷璧栨妯″瀷鑰岄潪浜掔浉渚濊禆
 */
public class Scene {

    // 鈹€鈹€鈹€ 鏁版嵁 鈹€鈹€鈹€
    private final List<Entity> entities = new ArrayList<>();
    private Entity selectedEntity;
    private final Set<Entity> multiSelected = new HashSet<>();
    private double cameraX, cameraY, cameraZoom = 1.0;

    // 鈹€鈹€鈹€ 浜嬩欢鐩戝惉 鈹€鈹€鈹€
    private final List<SceneListener> listeners = new ArrayList<>();

    // 鈹€鈹€鈹€ 鎾ら攢/閲嶅仛 鈹€鈹€鈹€
    private final Deque<Command> undoStack = new ArrayDeque<>();
    private final Deque<Command> redoStack = new ArrayDeque<>();
    private static final int MAX_UNDO = 100;

    // 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
    //  鐩戝惉鍣?
    // 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

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

    // 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
    //  瀹炰綋 CRUD
    // 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

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

    // 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
    //  鐩告満
    // 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

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

    public void setCameraZoom(double zoom) {
        this.cameraZoom = Math.max(0.05, Math.min(20, zoom));
        fireChange();
    }

    // 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
    //  鎾ら攢/閲嶅仛
    // 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

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

    // 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
    //  JSON 搴忓垪鍖?
    // 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?

    public String toJson() {
        return com.aetherforge.util.SceneSerializer.toJson(this);
    }

    public static Scene fromJson(String json) {
        return com.aetherforge.util.SceneSerializer.fromJson(json);
    }
}


