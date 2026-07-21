package com.aetherforge.model.component;

public class TransformComponent implements Component {
    private double x, y;
    private double rotation;
    private double scaleX = 1.0, scaleY = 1.0;

    public TransformComponent() {}
    public TransformComponent(double x, double y) { this.x = x; this.y = y; }

    public double getX() { return x; }
    public void setX(double x) { this.x = x; }
    public double getY() { return y; }
    public void setY(double y) { this.y = y; }
    public void setPosition(double x, double y) { this.x = x; this.y = y; }

    public double getRotation() { return rotation; }
    public void setRotation(double rotation) { this.rotation = rotation; }

    public double getScaleX() { return scaleX; }
    public void setScaleX(double scaleX) { this.scaleX = scaleX; }
    public double getScaleY() { return scaleY; }
    public void setScaleY(double scaleY) { this.scaleY = scaleY; }
}