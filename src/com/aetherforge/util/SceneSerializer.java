package com.aetherforge.util;

import com.aetherforge.model.Entity;
import com.aetherforge.model.Scene;
import com.aetherforge.model.component.*;
import com.google.gson.*;
import java.awt.Color;
import java.lang.reflect.Type;
import java.util.*;

/**
 * 场景序列化 — 组件感知版
 * 
 * 序列化格式（示例）：
 * {
 *   "camera": { "x": 0, "y": 0, "zoom": 1.0 },
 *   "entities": [{
 *     "id": "ent_abc123",
 *     "name": "Player",
 *     "components": {
 *       "transform": { "x": 100, "y": 200, "rotation": 0, "scaleX": 1, "scaleY": 1 },
 *       "render": { "type": "RECTANGLE", "color": "#4488cc", "width": 32, "height": 32, ... }
 *     }
 *   }]
 * }
 */
public final class SceneSerializer {
    private SceneSerializer() {}

    private static final Gson GSON = new GsonBuilder()
            .registerTypeAdapter(Color.class, new ColorAdapter())
            .registerTypeAdapter(Entity.class, new EntitySerializer())
            .registerTypeAdapter(Entity.class, new EntityDeserializer())
            .setPrettyPrinting()
            .create();

    // ─────────── 序列化 ───────────

    public static String toJson(Scene scene) {
        JsonObject root = new JsonObject();

        JsonObject cam = new JsonObject();
        cam.addProperty("x", scene.getCameraX());
        cam.addProperty("y", scene.getCameraY());
        cam.addProperty("zoom", scene.getCameraZoom());
        root.add("camera", cam);

        JsonArray arr = new JsonArray();
        for (Entity e : scene.getEntities()) {
            arr.add(GSON.toJsonTree(e, Entity.class));
        }
        root.add("entities", arr);
        root.addProperty("entityCount", scene.getEntities().size());

        return GSON.toJson(root);
    }

    // ─────────── 反序列化 ───────────

    public static Scene fromJson(String json) {
        Scene scene = new Scene();
        try {
            JsonObject root = GSON.fromJson(json, JsonObject.class);
            if (root == null) return scene;

            // 恢复相机
            if (root.has("camera")) {
                JsonObject cam = root.getAsJsonObject("camera");
                scene.resetCamera();
                if (cam.has("zoom")) scene.setCameraZoom(cam.get("zoom").getAsDouble());
                if (cam.has("x")) scene.moveCamera(cam.get("x").getAsDouble(), 0);
                if (cam.has("y")) scene.moveCamera(0, cam.get("y").getAsDouble());
            }

            // 恢复实体
            if (root.has("entities")) {
                JsonArray arr = root.getAsJsonArray("entities");
                for (JsonElement el : arr) {
                    Entity entity = GSON.fromJson(el, Entity.class);
                    if (entity != null) {
                        scene.addEntity(entity);
                    }
                }
            }
        } catch (JsonSyntaxException e) {
            System.err.println("[SceneSerializer] JSON parse error: " + e.getMessage());
        }
        return scene;
    }

    // ─────────── Entity 序列化器 ───────────

    private static class EntitySerializer implements JsonSerializer<Entity> {
        @Override
        public JsonElement serialize(Entity src, Type typeOfSrc, JsonSerializationContext context) {
            JsonObject obj = new JsonObject();
            obj.addProperty("id", src.getId());
            obj.addProperty("name", src.getName());

            JsonObject comps = new JsonObject();
            for (Component c : src.getComponents()) {
                String key = c.componentType().replace("Component", "").toLowerCase();
                comps.add(key, context.serialize(c));
            }
            obj.add("components", comps);

            return obj;
        }
    }

    // ─────────── Entity 反序列化器 ───────────

    private static class EntityDeserializer implements JsonDeserializer<Entity> {
        @Override
        public Entity deserialize(JsonElement json, Type typeOfT, JsonDeserializationContext context)
                throws JsonParseException {
            JsonObject obj = json.getAsJsonObject();
            Entity entity = new Entity("generic", "Entity");
            if (obj.has("id")) entity.setId(obj.get("id").getAsString());
            if (obj.has("name")) entity.setName(obj.get("name").getAsString());

            if (obj.has("components")) {
                JsonObject comps = obj.getAsJsonObject("components");

                // Transform
                if (comps.has("transform")) {
                    JsonObject t = comps.getAsJsonObject("transform");
                    TransformComponent tc = new TransformComponent();
                    if (t.has("x")) tc.setX(t.get("x").getAsDouble());
                    if (t.has("y")) tc.setY(t.get("y").getAsDouble());
                    if (t.has("rotation")) tc.setRotation(t.get("rotation").getAsDouble());
                    if (t.has("scaleX")) tc.setScaleX(t.get("scaleX").getAsDouble());
                    if (t.has("scaleY")) tc.setScaleY(t.get("scaleY").getAsDouble());
                    entity.add(tc);
                }

                // Render
                if (comps.has("render")) {
                    JsonObject r = comps.getAsJsonObject("render");
                    RenderComponent rc = new RenderComponent();
                    if (r.has("type")) rc.setType(RenderComponent.RenderType.valueOf(r.get("type").getAsString()));
                    if (r.has("color")) rc.setColor(Color.decode(r.get("color").getAsString()));
                    if (r.has("width")) rc.setWidth(r.get("width").getAsDouble());
                    if (r.has("height")) rc.setHeight(r.get("height").getAsDouble());
                    if (r.has("zIndex")) rc.setZIndex(r.get("zIndex").getAsInt());
                    if (r.has("visible")) rc.setVisible(r.get("visible").getAsBoolean());
                    if (r.has("imagePath")) rc.setImagePath(r.get("imagePath").getAsString());
                    if (r.has("text")) rc.setText(r.get("text").getAsString());
                    if (r.has("fontSize")) rc.setFontSize(r.get("fontSize").getAsInt());
                    entity.add(rc);
                }

                // Metadata
                if (comps.has("metadata")) {
                    JsonObject m = comps.getAsJsonObject("metadata");
                    MetadataComponent mc = new MetadataComponent();
                    if (m.has("type")) mc.setType(m.get("type").getAsString());
                    if (m.has("description")) mc.setDescription(m.get("description").getAsString());
                    if (m.has("isPlayer")) mc.setPlayer(m.get("isPlayer").getAsBoolean());
                    if (m.has("tags")) {
                        List<String> tags = new ArrayList<>();
                        for (JsonElement tag : m.getAsJsonArray("tags")) tags.add(tag.getAsString());
                        mc.setTags(tags);
                    }
                    entity.add(mc);
                }
            }

            return entity;
        }
    }

    // ─────────── Color 适配器 ───────────

    private static class ColorAdapter implements JsonSerializer<Color>, JsonDeserializer<Color> {
        @Override
        public JsonElement serialize(Color src, Type typeOfSrc, JsonSerializationContext context) {
            return new JsonPrimitive(String.format("#%06x", src.getRGB() & 0xFFFFFF));
        }

        @Override
        public Color deserialize(JsonElement json, Type typeOfT, JsonDeserializationContext context)
                throws JsonParseException {
            try { return Color.decode(json.getAsString()); }
            catch (Exception e) { return Color.GRAY; }
        }
    }
}
