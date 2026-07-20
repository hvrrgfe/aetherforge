package com.aetherforge.model;

import java.awt.Color;
import java.util.UUID;
public class Entity {
    private static int instanceCounter = 0;
    private String id;
    private String type;
    private String name;
    private double x, y, width = 32, height = 32;
    private Color color;
    private boolean isCircle, isPlayer;

    public Entity(String type, String name) {
        this.id = "ent_" + UUID.randomUUID().toString().substring(0, 6);
        this.type = type; this.name = name;
        // 偏移位置防止实体重叠
        instanceCounter++;
        int offset = (instanceCounter % 10) * 40;
        this.x = offset - 180;
        this.y = (instanceCounter / 10) * 40 - 60;
        this.color = nextPresetColor();
    }

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

    public boolean containsPoint(double px, double py) {
        if (isCircle) {
            // 圆形：距离半径检查
            double dx = px - x;
            double dy = py - y;
            double r = Math.min(width, height) / 2.0;
            return dx * dx + dy * dy <= r * r;
        }
        // 矩形：AABB 检查
        return px >= x - width/2 && px <= x + width/2
            && py >= y - height/2 && py <= y + height/2;
    }

    // Colors.ENTITY_PALETTE 中定义的调色板
    private static int colorIndex = 0;

    public static java.awt.Color nextPresetColor() {
        return com.aetherforge.util.Colors.ENTITY_PALETTE[colorIndex++ % com.aetherforge.util.Colors.ENTITY_PALETTE.length];
    }

    @Override
    public String toString() { return name; }
}
