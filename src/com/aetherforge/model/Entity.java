package com.aetherforge.model;

import com.aetherforge.util.Colors;
import java.awt.Color;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

/**
 * 实体数据模型 — 场景中的基本元素
 */
public class Entity {
    private static int instanceCounter = 0;

    private String id;
    private String type;
    private String name;
    private double x, y, width = 32, height = 32;
    private int serial;
    private Color color;
    private boolean isCircle, isPlayer;

    public Entity(String type, String name) {
        this.id = "ent_" + UUID.randomUUID().toString().substring(0, 6);
        this.type = type;
        this.name = name;
        this.serial = instanceCounter++;
        int offset = (serial % 10) * 40;
        this.x = offset - 180;
        this.y = (serial / 10) * 40 - 60;
        this.color = randomPaletteColor();
    }

    /** 从调色板中随机取色，而非全局轮转，避免跨场景共享状态 */
    private static Color randomPaletteColor() {
        Color[] palette = Colors.ENTITY_PALETTE;
        return palette[ThreadLocalRandom.current().nextInt(palette.length)];
    }

    // ─── Getters ───

    public String getId() { return id; }
    public String getType() { return type; }
    public String getName() { return name; }
    public double getX() { return x; }
    public double getY() { return y; }
    public double getWidth() { return width; }
    public double getHeight() { return height; }
    public Color getColor() { return color; }
    public boolean isCircle() { return isCircle; }
    public boolean isPlayer() { return isPlayer; }

    // ─── Setters ───

    public void setX(double x) { this.x = x; }
    public void setY(double y) { this.y = y; }
    public void setWidth(double w) { this.width = w; }
    public void setHeight(double h) { this.height = h; }
    public void setColor(Color c) { this.color = c; }
    public void setCircle(boolean v) { isCircle = v; }
    public void setPlayer(boolean v) { isPlayer = v; }
    public void setType(String t) { this.type = t; }
    public void setName(String n) { this.name = n; }
    public void setId(String id) { this.id = id; }
    public void setPosition(double x, double y) { this.x = x; this.y = y; }

    /** 碰撞检测：判断点 (px, py) 是否在实体范围内 */
    public boolean containsPoint(double px, double py) {
        if (isCircle) {
            double dx = px - x;
            double dy = py - y;
            double r = Math.min(width, height) / 2.0;
            return dx * dx + dy * dy <= r * r;
        }
        // AABB 检测
        return px >= x - width / 2 && px <= x + width / 2
            && py >= y - height / 2 && py <= y + height / 2;
    }

    @Override
    public String toString() { return name; }
}
