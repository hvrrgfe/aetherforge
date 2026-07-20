package com.aetherforge.util;

import com.aetherforge.model.Entity;
import com.aetherforge.model.Scene;
import java.awt.Color;

/**
 * 场景序列化/反序列化 — 独立于 Scene 领域模型
 * 当前使用手写 JSON 解析器，后续可替换为 Gson/Jackson
 */
public final class SceneSerializer {
    private SceneSerializer() {}

    public static String toJson(Scene scene) {
        StringBuilder sb = new StringBuilder();
        sb.append("{\"cameraX\":").append(scene.getCameraX())
          .append(",\"cameraY\":").append(scene.getCameraY())
          .append(",\"cameraZoom\":").append(scene.getCameraZoom())
          .append(",\"entities\":[");
        java.util.List<Entity> entities = scene.getEntities();
        for (int i = 0; i < entities.size(); i++) {
            if (i > 0) sb.append(",");
            sb.append(entityToJson(entities.get(i)));
        }
        sb.append("]}");
        return sb.toString();
    }

    private static String entityToJson(Entity e) {
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

                static String escapeJson(String s) {
        if (s == null) return "";
        StringBuilder sb = new StringBuilder(s.length() + 16);
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"':  sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n"); break;
                case '\r': sb.append("\\r"); break;
                case '\t': sb.append("\\t"); break;
                case '\b': sb.append("\\b"); break;
                case '\f': sb.append("\\f"); break;
                default:
                    if (c < 0x20) {
                        sb.append(String.format("\\u%04x", (int)c));
                    } else {
                        sb.append(c);
                    }
            }
        }
        return sb.toString();
    }

    public static Scene fromJson(String json) {
        Scene scene = new Scene();
        try {
            int entIdx = json.indexOf("\"entities\":[");
            if (entIdx < 0) return scene;
            int arrStart = json.indexOf("[", entIdx);
            int arrEnd = json.lastIndexOf("]");
            if (arrStart < 0 || arrEnd < 0) return scene;

            String arr = json.substring(arrStart + 1, arrEnd);
            if (arr.trim().isEmpty()) return scene;

            extractCamera(json, scene);
            parseEntities(arr, scene);
        } catch (Exception e) {
            System.err.println("[SceneSerializer] JSON parse error: " + e.getMessage());
        }
        return scene;
    }

    private static void extractCamera(String json, Scene scene) {
        scene.moveCamera(extractDouble(json, "\"cameraX\":"), extractDouble(json, "\"cameraY\":"));
        double zoom = extractDouble(json, "\"cameraZoom\":");
        if (zoom > 0) { scene.resetCamera(); scene.zoomCamera(zoom); }
    }

    private static void parseEntities(String arr, Scene scene) {
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
            System.err.println("[SceneSerializer] Entity parse error: " + e.getMessage());
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
