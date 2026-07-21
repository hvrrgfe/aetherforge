package com.aetherforge.model.component;

import java.awt.Color;

public class RenderComponent implements Component {
    public enum RenderType { RECTANGLE, CIRCLE, IMAGE, TEXT }

    private RenderType type = RenderType.RECTANGLE;
    private Color color = Color.GRAY;
    private double width = 32, height = 32;
    private int zIndex;
    private boolean visible = true;
    private String imagePath = "";
    private String text = "";
    private int fontSize = 14;
    private String fontName = "Microsoft YaHei UI";
    private Color textColor = Color.WHITE;

    public RenderComponent() {}

    public RenderType getType() { return type; }
    public void setType(RenderType type) { this.type = type; }
    public Color getColor() { return color; }
    public void setColor(Color color) { this.color = color; }
    public double getWidth() { return width; }
    public void setWidth(double width) { this.width = width; }
    public double getHeight() { return height; }
    public void setHeight(double height) { this.height = height; }
    public void setSize(double w, double h) { this.width = w; this.height = h; }
    public int getZIndex() { return zIndex; }
    public void setZIndex(int zIndex) { this.zIndex = zIndex; }
    public boolean isVisible() { return visible; }
    public void setVisible(boolean visible) { this.visible = visible; }
    public String getImagePath() { return imagePath; }
    public void setImagePath(String imagePath) { this.imagePath = imagePath; }
    public String getText() { return text; }
    public void setText(String text) { this.text = text; }
    public int getFontSize() { return fontSize; }
    public void setFontSize(int fontSize) { this.fontSize = fontSize; }
    public String getFontName() { return fontName; }
    public void setFontName(String fontName) { this.fontName = fontName; }
    public Color getTextColor() { return textColor; }
    public void setTextColor(Color textColor) { this.textColor = textColor; }
}