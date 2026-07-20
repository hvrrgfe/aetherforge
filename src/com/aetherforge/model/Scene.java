package com.aetherforge.model;

import com.aetherforge.util.Colors;
import com.aetherforge.util.I18n;
import java.awt.Color;
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
        StringBuilder sb = new StringBuilder();
        sb.append("{\"cameraX\":").append(cameraX)
          .append(",\"cameraY\":").append(cameraY)
          .append(",\"cameraZoom\":").append(cameraZoom)
          .append(",\"entities\":[");
        for (int i = 0; i < entities.size(); i++) {
            if (i > 0) sb.append(",");
            sb.append(entityToJson(entities.get(i)));
        }
        sb.append("]}");
        return sb.toString();
    }

    private String entityToJson(Entity e) {
        return "{\"id\":\"" + escapeJson(e.getId()) +
            "\",\"type\":\"" + escapeJson(e.getType()) +
            "\",\"name\":\"" + escapeJson(e.getName()) +
            "\",\"x\":" + e.getX() +
            ",\"y\":" + e.getY() +
            ",\"width\":" + e.getWidth() +
            ",\"height\":" + e.getHeight() +
            ",\"color\":\"" + String.format("%06x", e.getColor().getRGB() & 0xFFFFFF) +
            "\",\"isCircle\":" + e.isCircle() +
            ",\"isPlayer\":" + e.isPlayer() +
            "}";
    }

    private String escapeJson(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\\n", "\\\\n").replace("\\r", "\\\\r")
                .replace("\\t", "\\\\t");
    }

    public static Scene fromJson(String json) {
        Scene scene = new Scene();
        // simple JSON parser for the known format
        try {
            int entIdx = json.indexOf("\"entities\":[");
            if (entIdx < 0) return scene;
            int arrStart = json.indexOf("[", entIdx);
            int arrEnd = json.lastIndexOf("]");
            if (arrStart < 0 || arrEnd < 0) return scene;

            String arr = json.substring(arrStart + 1, arrEnd);
            if (arr.trim().isEmpty()) return scene;

            // extract camera
            scene.cameraX = extractDouble(json, "\"cameraX\":");
            scene.cameraY = extractDouble(json, "\"cameraY\":");
            scene.cameraZoom = extractDouble(json, "\"cameraZoom\":");

            // parse entity objects
            int depth = 0, start = 0;
            for (int i = 0; i < arr.length(); i++) {
                char c = arr.charAt(i);
                if (c == '{') { if (depth++ == 0) start = i; }
                else if (c == '}') {
                    if (--depth == 0) {
                        Entity e = parseEntity(arr.substring(start, i + 1));
                        if (e != null) scene.addEntity(e);
                    }
                }
            }
        } catch (Exception ignored) {
            System.err.println("[Scene] JSON parse error");
        }
        return scene;
    }

    private static double extractDouble(String json, String key) {
        int idx = json.indexOf(key);
        if (idx < 0) return 0;
        idx += key.length();
        int end = json.indexOf(",", idx);
        if (end < 0) end = json.indexOf("}", idx);
        if (end < 0) return 0;
        try { return Double.parseDouble(json.substring(idx, end).trim()); }
        catch (NumberFormatException e) { return 0; }
    }

    private static Entity parseEntity(String obj) {
        try {
            String id = extractString(obj, "\"id\"");
            String type = extractString(obj, "\"type\"");
            String name = extractString(obj, "\"name\"");
            double x = extractDouble(obj, "\"x\":");
            double y = extractDouble(obj, "\"y\":");
            double w = extractDouble(obj, "\"width\":");
            double h = extractDouble(obj, "\"height\":");
            String colorStr = extractString(obj, "\"color\"");
            boolean isCircle = obj.contains("\"isCircle\":true");
            boolean isPlayer = obj.contains("\"isPlayer\":true");

            Entity entity = new Entity(type, name);
            if (!id.isEmpty()) entity.setId(id);
            entity.setX(x); entity.setY(y);
            entity.setWidth(w); entity.setHeight(h);
            if (!colorStr.isEmpty()) {
                try { entity.setColor(Color.decode("#" + colorStr)); }
                catch (Exception ignored) {}
            }
            entity.setCircle(isCircle);
            entity.setPlayer(isPlayer);
            return entity;
        } catch (Exception e) {
            System.err.println("[Scene] Entity parse error: " + e.getMessage());
            return null;
        }
    }

    private static String extractString(String json, String key) {
        int idx = json.indexOf(key + "\":\"");
        if (idx < 0) return "";
        idx += key.length() + 3;
        int end = json.indexOf("\"", idx);
        if (end < 0) return "";
        return json.substring(idx, end);
    }
}
