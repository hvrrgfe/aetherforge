package com.aetherforge.model;

import com.aetherforge.model.component.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 实体 — 基于组件的游戏对象
 * 
 * 所有数据通过 Component 持有，实体本身只做路由：
 * - Entity.get(TransformComponent.class).setX(100)
 * - Entity.has(RenderComponent.class)
 * 
 * 默认自带 TransformComponent + MetadataComponent
 * 旧接口方法（getWidth/setColor/isCircle等）自动委派到 RenderComponent
 */
public class Entity {
    private static int instanceCounter = 0;

    private String id;
    private String name;
    private final int serial;
    private final Map<Class<? extends Component>, Component> components = new ConcurrentHashMap<>();

    public Entity() {
        this("generic", "New Entity");
    }

    public Entity(String type, String name) {
        this.id = "ent_" + UUID.randomUUID().toString().substring(0, 6);
        this.name = name;
        this.serial = instanceCounter++;
        // 默认组件：Transform + Metadata
        add(new TransformComponent());
        add(new MetadataComponent());
        get(MetadataComponent.class).setType(type);
    }

    // ═══════════════ 组件访问 ═══════════════

    @SuppressWarnings("unchecked")
    public <T extends Component> T get(Class<T> type) {
        return (T) components.get(type);
    }

    public <T extends Component> T add(T component) {
        components.put((Class<T>) component.getClass(), component);
        return component;
    }

    public <T extends Component> void remove(Class<T> type) {
        components.remove(type);
    }

    public boolean has(Class<? extends Component> type) {
        return components.containsKey(type);
    }

    public Collection<Component> getComponents() {
        return components.values();
    }

    public int componentCount() { return components.size(); }

    // ═══════════════ 确保组件存在（惰性创建） ═══════════════

    private RenderComponent ensureRender() {
        RenderComponent r = get(RenderComponent.class);
        if (r == null) {
            r = new RenderComponent();
            add(r);
        }
        return r;
    }

    // ═══════════════ 旧接口兼容（委派到组件） ═══════════════

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    // Transform 委派
    public double getX() {
        TransformComponent t = get(TransformComponent.class);
        return t != null ? t.getX() : 0;
    }
    public void setX(double x) {
        TransformComponent t = get(TransformComponent.class);
        if (t != null) t.setX(x);
    }
    public double getY() {
        TransformComponent t = get(TransformComponent.class);
        return t != null ? t.getY() : 0;
    }
    public void setY(double y) {
        TransformComponent t = get(TransformComponent.class);
        if (t != null) t.setY(y);
    }
    public void setPosition(double x, double y) {
        TransformComponent t = get(TransformComponent.class);
        if (t != null) t.setPosition(x, y);
    }

    // Render 委派（旧接口）
    public double getWidth() {
        RenderComponent r = get(RenderComponent.class);
        return r != null ? r.getWidth() : 32;
    }
    public void setWidth(double w) { ensureRender().setWidth(w); }
    public double getHeight() {
        RenderComponent r = get(RenderComponent.class);
        return r != null ? r.getHeight() : 32;
    }
    public void setHeight(double h) { ensureRender().setHeight(h); }
    public java.awt.Color getColor() {
        RenderComponent r = get(RenderComponent.class);
        return r != null ? r.getColor() : java.awt.Color.GRAY;
    }
    public void setColor(java.awt.Color c) { ensureRender().setColor(c); }
    public boolean isCircle() {
        RenderComponent r = get(RenderComponent.class);
        return r != null && r.getType() == RenderComponent.RenderType.CIRCLE;
    }
    public void setCircle(boolean v) {
        ensureRender().setType(v ? RenderComponent.RenderType.CIRCLE
                                  : RenderComponent.RenderType.RECTANGLE);
    }

    // Metadata 委派（旧接口）
    public String getType() {
        MetadataComponent m = get(MetadataComponent.class);
        return m != null ? m.getType() : "generic";
    }
    public void setType(String type) {
        MetadataComponent m = get(MetadataComponent.class);
        if (m != null) m.setType(type);
    }
    public boolean isPlayer() {
        MetadataComponent m = get(MetadataComponent.class);
        return m != null && m.isPlayer();
    }
    public void setPlayer(boolean v) {
        MetadataComponent m = get(MetadataComponent.class);
        if (m != null) m.setPlayer(v);
    }

    // ═══════════════ 碰撞检测 ═══════════════

    public boolean containsPoint(double px, double py) {
        RenderComponent r = get(RenderComponent.class);
        TransformComponent t = get(TransformComponent.class);
        if (t == null) return false;

        double x = t.getX(), y = t.getY();
        double w = r != null ? r.getWidth() : 32;
        double h = r != null ? r.getHeight() : 32;

        if (r != null && r.getType() == RenderComponent.RenderType.CIRCLE) {
            double dx = px - x;
            double dy = py - y;
            double radius = Math.min(w, h) / 2.0;
            return dx * dx + dy * dy <= radius * radius;
        }
        return px >= x - w / 2 && px <= x + w / 2
            && py >= y - h / 2 && py <= y + h / 2;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Entity e)) return false;
        return id.equals(e.id);
    }

    @Override
    public int hashCode() { return id.hashCode(); }

    @Override
    public String toString() { return name; }
}
