package com.aetherforge.tools;

import com.aetherforge.model.dto.DownloadProgress;
import com.aetherforge.model.dto.ModelInfo;
import com.google.gson.*;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class ModelDownloadClient {
    private static final String BASE = "http://127.0.0.1:7890";
    private final String baseUrl;
    private final HttpClient http;
    private final Gson gson;

    public ModelDownloadClient() { this(BASE); }
    public ModelDownloadClient(String baseUrl) {
        this.baseUrl = baseUrl;
        this.http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
        this.gson = new Gson();
    }

    public List<ModelInfo> listModels(String modelType) {
        try {
            String url = baseUrl + "/api/models/list";
            if (modelType != null && !modelType.isEmpty()) url += "?model_type=" + modelType;
            HttpRequest req = HttpRequest.newBuilder().uri(URI.create(url)).GET()
                .timeout(Duration.ofSeconds(15)).build();
            HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
            if (res.statusCode() != 200) return List.of();
            JsonObject json = JsonParser.parseString(res.body()).getAsJsonObject();
            if (!json.get("success").getAsBoolean()) return List.of();
            JsonArray arr = json.getAsJsonArray("models");
            List<ModelInfo> models = new ArrayList<>();
            for (JsonElement el : arr) {
                ModelInfo m = gson.fromJson(el, ModelInfo.class);
                if (m.getName() == null || m.getName().isEmpty()) m.setName(m.getModelId());
                models.add(m);
            }
            return models;
        } catch (Exception e) { return List.of(); }
    }

    public boolean startDownload(String modelId) {
        try {
            String json = gson.toJson(Map.of("model_id", modelId));
            HttpRequest req = HttpRequest.newBuilder().uri(URI.create(baseUrl + "/api/models/download"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .timeout(Duration.ofSeconds(10)).build();
            HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
            return res.statusCode() == 200
                && JsonParser.parseString(res.body()).getAsJsonObject().get("success").getAsBoolean();
        } catch (Exception e) { return false; }
    }

    public List<DownloadProgress> getDownloadProgress() {
        try {
            HttpRequest req = HttpRequest.newBuilder().uri(URI.create(baseUrl + "/api/models/downloads")).GET()
                .timeout(Duration.ofSeconds(10)).build();
            HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
            if (res.statusCode() != 200) return List.of();
            JsonArray arr = JsonParser.parseString(res.body()).getAsJsonObject().getAsJsonArray("downloads");
            List<DownloadProgress> list = new ArrayList<>();
            for (JsonElement el : arr) list.add(gson.fromJson(el, DownloadProgress.class));
            return list;
        } catch (Exception e) { return List.of(); }
    }

    public boolean selectModel(String modelType, String modelId) {
        try {
            String json = gson.toJson(Map.of("model_type", modelType, "model_id", modelId));
            HttpRequest req = HttpRequest.newBuilder().uri(URI.create(baseUrl + "/api/models/select"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .timeout(Duration.ofSeconds(10)).build();
            return http.send(req, HttpResponse.BodyHandlers.ofString()).statusCode() == 200;
        } catch (Exception e) { return false; }
    }

    public boolean deleteModel(String modelId) {
        try {
            String json = gson.toJson(Map.of("model_id", modelId));
            HttpRequest req = HttpRequest.newBuilder().uri(URI.create(baseUrl + "/api/models/delete"))
                .header("Content-Type", "application/json")
                .method("DELETE", HttpRequest.BodyPublishers.ofString(json))
                .timeout(Duration.ofSeconds(10)).build();
            HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
            return res.statusCode() == 200
                && JsonParser.parseString(res.body()).getAsJsonObject().get("success").getAsBoolean();
        } catch (Exception e) { return false; }
    }

    public boolean isServerOnline() {
        try {
            HttpRequest req = HttpRequest.newBuilder().uri(URI.create(baseUrl + "/api/tools")).GET()
                .timeout(Duration.ofSeconds(3)).build();
            return http.send(req, HttpResponse.BodyHandlers.ofString()).statusCode() == 200;
        } catch (Exception e) { return false; }
    }
}
