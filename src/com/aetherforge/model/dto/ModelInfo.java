package com.aetherforge.model.dto;

public class ModelInfo {
    private String name; private String model_id; private String type;
    private String description; private String params; private String status;
    private String local_path; private String source; private long size_bytes;
    public String getName() { return name; }
    public void setName(String n) { this.name = n; }
    public String getModelId() { return model_id; }
    public void setModel_id(String v) { this.model_id = v; }
    public String getType() { return type; }
    public void setType(String v) { this.type = v; }
    public String getDescription() { return description; }
    public void setDescription(String v) { this.description = v; }
    public String getParams() { return params; }
    public void setParams(String v) { this.params = v; }
    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
    public String getLocalPath() { return local_path; }
    public void setLocal_path(String v) { this.local_path = v; }
    public String getSource() { return source; }
    public void setSource(String v) { this.source = v; }
    public long getSizeBytes() { return size_bytes; }
    public void setSize_bytes(long v) { this.size_bytes = v; }
    public String getFormattedSize() {
        if (size_bytes < 1024) return size_bytes + "B";
        if (size_bytes < 1024*1024) return (size_bytes/1024) + "KB";
        if (size_bytes < 1024*1024*1024) return (size_bytes/(1024*1024)) + "MB";
        return String.format("%.1fGB", size_bytes / (1024.0*1024*1024));
    }
    public String getDisplayStatus() {
        if (status == null) return "unknown";
        return switch (status) {
            case "downloaded" -> "downloaded";
            case "not_downloaded" -> "not downloaded";
            case "downloading" -> "downloading...";
            default -> "unknown";
        };
    }
}
