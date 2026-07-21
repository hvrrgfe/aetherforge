package com.aetherforge.util;

import com.aetherforge.model.Entity;
import com.aetherforge.model.Scene;
import org.junit.jupiter.api.Test;
import java.awt.Color;
import static org.junit.jupiter.api.Assertions.*;

/**
 * SceneSerializer Gson 序列化/反序列化测试
 */
class SceneSerializerTest {

    @Test
    void testRoundTripEmptyScene() {
        Scene scene = new Scene();
        String json = SceneSerializer.toJson(scene);
        assertNotNull(json);
        assertTrue(json.contains("\"entities\":"));

        Scene restored = SceneSerializer.fromJson(json);
        assertNotNull(restored);
        assertEquals(0, restored.getEntities().size());
    }

    @Test
    void testRoundTripWithEntities() {
        Scene scene = new Scene();
        Entity e1 = new Entity("player", "Hero");
        e1.setPosition(100, 200);
        e1.setWidth(48);
        e1.setHeight(48);
        e1.setColor(Color.RED);
        e1.setPlayer(true);
        scene.addEntity(e1);

        Entity e2 = new Entity("goblin", "Grunt");
        e2.setPosition(-50, 80);
        e2.setWidth(32);
        e2.setHeight(32);
        e2.setCircle(true);
        scene.addEntity(e2);

        String json = SceneSerializer.toJson(scene);
        assertNotNull(json);
        assertTrue(json.contains("\"player\""));
        assertTrue(json.contains("\"goblin\""));

        Scene restored = SceneSerializer.fromJson(json);
        assertEquals(2, restored.getEntities().size());

        Entity r1 = restored.getEntities().get(0);
        assertEquals("player", r1.getType());
        assertEquals("Hero", r1.getName());
        assertEquals(100.0, r1.getX());
        assertEquals(200.0, r1.getY());
        assertEquals(48.0, r1.getWidth());
        assertEquals(Color.RED, r1.getColor());
        assertTrue(r1.isPlayer());

        Entity r2 = restored.getEntities().get(1);
        assertEquals("goblin", r2.getType());
        assertEquals(-50.0, r2.getX());
        assertTrue(r2.isCircle());
    }

    @Test
    void testCameraPreserved() {
        Scene scene = new Scene();
        scene.moveCamera(120, 80);
        scene.setCameraZoom(1.5);

        String json = SceneSerializer.toJson(scene);
        Scene restored = SceneSerializer.fromJson(json);

        assertEquals(120.0, restored.getCameraX(), 0.001);
        assertEquals(80.0, restored.getCameraY(), 0.001);
        assertEquals(1.5, restored.getCameraZoom(), 0.001);
    }

    @Test
    void testInvalidJsonReturnsEmptyScene() {
        Scene scene = SceneSerializer.fromJson("not json at all");
        assertNotNull(scene);
        assertEquals(0, scene.getEntities().size());
    }

    @Test
    void testEmptyJsonReturnsEmptyScene() {
        Scene scene = SceneSerializer.fromJson("");
        assertNotNull(scene);
        assertEquals(0, scene.getEntities().size());
    }

    @Test
    void testEntityIdPreserved() {
        Scene scene = new Scene();
        Entity e = new Entity("test", "Test");
        String originalId = e.getId();
        scene.addEntity(e);

        String json = SceneSerializer.toJson(scene);
        Scene restored = SceneSerializer.fromJson(json);

        assertEquals(1, restored.getEntities().size());
        assertEquals(originalId, restored.getEntities().get(0).getId());
    }

    @Test
    void testColorRoundTrip() {
        Color[] colors = {Color.RED, Color.GREEN, Color.BLUE, Color.ORANGE, Color.MAGENTA};
        for (Color c : colors) {
            Scene scene = new Scene();
            Entity e = new Entity("test", "Color");
            e.setColor(c);
            scene.addEntity(e);

            String json = SceneSerializer.toJson(scene);
            Scene restored = SceneSerializer.fromJson(json);

            assertEquals(c, restored.getEntities().get(0).getColor());
        }
    }
}
