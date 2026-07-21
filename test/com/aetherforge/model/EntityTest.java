package com.aetherforge.model;

import org.junit.jupiter.api.Test;
import java.awt.Color;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Entity 模型单元测试
 */
class EntityTest {

    @Test
    void testCreateEntity() {
        Entity e = new Entity("player", "Hero");
        assertNotNull(e.getId());
        assertTrue(e.getId().startsWith("ent_"));
        assertEquals("player", e.getType());
        assertEquals("Hero", e.getName());
        assertNotNull(e.getColor());
    }

    @Test
    void testDefaultSize() {
        Entity e = new Entity("goblin", "Goblin");
        assertEquals(32.0, e.getWidth());
        assertEquals(32.0, e.getHeight());
    }

    @Test
    void testSetPosition() {
        Entity e = new Entity("test", "Test");
        e.setPosition(100, 200);
        assertEquals(100.0, e.getX());
        assertEquals(200.0, e.getY());
    }

    @Test
    void testRectangleHitDetection() {
        Entity e = new Entity("chest", "Chest");
        e.setPosition(0, 0);
        e.setCircle(false);
        // 中心点
        assertTrue(e.containsPoint(0, 0));
        // 边缘内部
        assertTrue(e.containsPoint(15, 0));
        assertTrue(e.containsPoint(0, -15));
        // 边缘外部
        assertFalse(e.containsPoint(17, 0));
        assertFalse(e.containsPoint(0, -17));
    }

    @Test
    void testCircleHitDetection() {
        Entity e = new Entity("orb", "Orb");
        e.setPosition(0, 0);
        e.setCircle(true);
        e.setWidth(40);
        e.setHeight(40);
        // 中心点
        assertTrue(e.containsPoint(0, 0));
        // 半径内 (r=20)
        assertTrue(e.containsPoint(10, 0));
        assertTrue(e.containsPoint(14, 14)); // ~19.8 < 20
        // 半径外
        assertFalse(e.containsPoint(15, 15)); // ~21.2 > 20
    }

    @Test
    void testToString() {
        Entity e = new Entity("npc", "Merchant");
        assertEquals("Merchant", e.toString());
    }

    @Test
    void testFlags() {
        Entity e = new Entity("player", "Player");
        e.setPlayer(true);
        e.setCircle(false);
        assertTrue(e.isPlayer());
        assertFalse(e.isCircle());
    }
}
