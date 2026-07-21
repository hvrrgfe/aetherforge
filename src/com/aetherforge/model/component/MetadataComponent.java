package com.aetherforge.model.component;

import java.util.*;

public class MetadataComponent implements Component {
    private String type = "generic";
    private String description = "";
    private boolean isPlayer;
    private List<String> tags = new ArrayList<>();
    private Map<String, Object> properties = new HashMap<>();

    public MetadataComponent() {}

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public boolean isPlayer() { return isPlayer; }
    public void setPlayer(boolean player) { isPlayer = player; }
    public List<String> getTags() { return tags; }
    public void setTags(List<String> tags) { this.tags = tags; }
    public void addTag(String tag) { tags.add(tag); }
    public boolean hasTag(String tag) { return tags.contains(tag); }
    public Map<String, Object> getProperties() { return properties; }
    public void setProperties(Map<String, Object> properties) { this.properties = properties; }
    public void setProperty(String key, Object value) { properties.put(key, value); }
    @SuppressWarnings("unchecked")
    public <T> T getProperty(String key) { return (T) properties.get(key); }
    public boolean hasProperty(String key) { return properties.containsKey(key); }
}