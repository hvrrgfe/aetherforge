package com.aetherforge.model.dto;

public class DownloadProgress {
    private String model_id; private double progress; private String status;
    public String getModelId() { return model_id; }
    public void setModel_id(String v) { this.model_id = v; }
    public double getProgress() { return progress; }
    public void setProgress(double v) { this.progress = v; }
    public String getStatus() { return status; }
    public void setStatus(String v) { this.status = v; }
    public boolean isCompleted() { return "completed".equals(status); }
    public boolean isError() { return "error".equals(status); }
    public boolean isDownloading() { return "downloading".equals(status); }
}
