package com.aetherforge.model;

import java.awt.Color;
import java.util.UUID;
import com.aetherforge.util.Colors;

public class Entity {
    private String id;
    private String type;
    private String name;
    private double x, y, width = 32, height = 32;
    private Color color = Colors.BLUE;
    private boolean isCircle, isPlayer;

    public Entity(String type, String name) {
        this.id = "ent_" + UUID.randomUUID().toString().substring(0, 6);
        this.type = type; this.name = name;
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
    public void setPosition(double x, double y) { this.x = x; this.y = y; }

    public boolean containsPoint(double px, double py) {
        return px >= x - width/2 && px <= x + width/2
            && py >= y - height/2 && py <= y + height/2;
    }

    @Override
    public String toString() { return name; }
}
