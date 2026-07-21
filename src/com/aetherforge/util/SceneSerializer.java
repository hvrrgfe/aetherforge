package com.aetherforge.util;

import com.aetherforge.model.Entity;
import com.aetherforge.model.Scene;
import com.google.gson.*;
import com.google.gson.reflect.TypeToken;
import java.awt.Color;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

/**
 * 场景序列化/反序列化 — 基于 Gson，消除手写 JSON 解析器
 */
public final class SceneSerializer {
    private SceneSerializer() {}

    private static final Gson GSON = new GsonBuilder()
            .registerTypeAdapter(Color.class, new ColorAdapter())
            .setPrettyPrinting()
            .create();

    private static final Type ENTITY_LIST_TYPE = new TypeToken<List<EntityData>>() {}.getType();

    /** 用于 Gson 序列化的中间 DTO，避免污染 Entity 领域模型 */
    private record SceneData(
            double cameraX,
            double cameraY,
            double cameraZoom,
            List<EntityData> entities
    ) {}

    /** 实体 DTO */
    private record EntityData(
            String id,
            String type,
            String name,
            double x, double y,
            double width, double height,
            String color,
            boolean isCircle,
            boolean isPlayer
    ) {}

    public static String toJson(Scene scene) {
        List<EntityData> edList = new ArrayList<>();
        for (Entity e : scene.getEntities()) {
            edList.add(new EntityData(
                    e.getId(), e.getType(), e.getName(),
                    e.getX(), e.getY(), e.getWidth(), e.getHeight(),
                    String.format("%06x", e.getColor().getRGB() & 0xFFFFFF),
                    e.isCircle(), e.isPlayer()
            ));
        }
        SceneData data = new SceneData(
                scene.getCameraX(), scene.getCameraY(), scene.getCameraZoom(),
                edList
        );
        return GSON.toJson(data);
    }

    public static Scene fromJson(String json) {
        Scene scene = new Scene();
        try {
            SceneData data = GSON.fromJson(json, SceneData.class);
            if (data == null) return scene;

            // 恢复相机
            scene.resetCamera();
            scene.setCameraZoom(data.cameraZoom);
            scene.moveCamera(data.cameraX, data.cameraY);

            // 恢复实体
            if (data.entities != null) {
                for (EntityData ed : data.entities) {
                    Entity entity = new Entity(ed.type, ed.name);
                    entity.setId(ed.id);
                    entity.setX(ed.x);
                    entity.setY(ed.y);
                    entity.setWidth(ed.width);
                    entity.setHeight(ed.height);
                    if (ed.color != null && !ed.color.isEmpty()) {
                        try {
                            entity.setColor(Color.decode("#" + ed.color));
                        } catch (Exception ignored) {}
                    }
                    entity.setCircle(ed.isCircle);
                    entity.setPlayer(ed.isPlayer);
                    scene.addEntity(entity);
                }
            }
        } catch (JsonSyntaxException e) {
            System.err.println("[SceneSerializer] JSON parse error: " + e.getMessage());
        }
        return scene;
    }

    /** Color 序列化适配器 */
    private static class ColorAdapter implements JsonSerializer<Color>, JsonDeserializer<Color> {
        @Override
        public JsonElement serialize(Color src, Type typeOfSrc, JsonSerializationContext context) {
            return new JsonPrimitive(String.format("#%06x", src.getRGB() & 0xFFFFFF));
        }

        @Override
        public Color deserialize(JsonElement json, Type typeOfT, JsonDeserializationContext context) throws JsonParseException {
            try {
                return Color.decode(json.getAsString());
            } catch (Exception e) {
                return Color.GRAY;
            }
        }
    }
}
