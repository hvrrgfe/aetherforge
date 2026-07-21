package com.aetherforge.launcher;

import com.aetherforge.util.Colors;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.io.*;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

/**
 * 组件启动面板 — 管理 AetherForge 各组件启动/停止
 * 所有组件通过 cmd /c start /D <dir> 在新窗口中启动。
 * 服务类组件通过 HTTP ping 跟踪运行状态。
 */
public class ComponentPanel extends JPanel {

    private final List<ManagedProcess> processes = new ArrayList<>();
    private JLabel globalStatusLabel;
    private ComponentCard mcpCard, webCard, demo2dCard, demo3dCard;

    public ComponentPanel() {
        setLayout(new BoxLayout(this, BoxLayout.Y_AXIS));
        setBackground(Colors.bgDeepest());
        setBorder(new EmptyBorder(16, 16, 16, 16));
        buildHeader();
        add(Box.createVerticalStrut(12));
        buildComponentGrid();
    }

    public void setGlobalStatusLabel(JLabel label) { this.globalStatusLabel = label; }
    void setGlobalStatus(String text) { if (globalStatusLabel != null) globalStatusLabel.setText(text); }

    public void shutdownAll() {
        for (ManagedProcess p : processes) p.stop();
    }

    private void buildHeader() {
        JPanel header = new JPanel(new BorderLayout());
        header.setOpaque(false);
        JLabel title = new JLabel("组件管理");
        title.setFont(UIManager.getFont("defaultFont").deriveFont(Font.BOLD, 16f));
        title.setForeground(Colors.textPrimary());
        JLabel desc = new JLabel("启动/停止 AetherForge 各服务组件");
        desc.setFont(UIManager.getFont("defaultFont").deriveFont(12f));
        desc.setForeground(Colors.textMuted());
        header.add(title, BorderLayout.NORTH);
        header.add(desc, BorderLayout.SOUTH);
        add(header);
    }

    private void buildComponentGrid() {
        JPanel grid = new JPanel(new GridLayout(2, 2, 12, 12));
        grid.setOpaque(false);

        mcpCard = new ComponentCard("MCP Server",
            "AI Agent 工具接口 (76+ tools)",
            "Python 核心引擎，提供 MCP 协议接入",
            "python -m aetherforge.mcp_server",
            Colors.BLUE, this, true);
        grid.add(mcpCard);

        webCard = new ComponentCard("Web UI",
            "浏览器可视化界面",
            "Flask Web 服务器 (端口 7890)",
            "python -m aetherforge.main",
            Colors.GREEN, this, true);
        grid.add(webCard);

        demo2dCard = new ComponentCard("2D 引擎",
            "空白 2D 游戏引擎",
            "启动空白 2D 游戏世界（端口 7891）",
            "python -m aetherforge.main --port 7891",
            Colors.ORANGE, this, true);
        grid.add(demo2dCard);

        demo3dCard = new ComponentCard("3D 引擎",
            "空白 3D 游戏引擎",
            "启动空白 3D 游戏世界（端口 7892）",
            "python -m aetherforge.main --port 7892",
            Colors.ORANGE, this, true);
        grid.add(demo3dCard);

        add(grid);
    }

    private static String[] splitCommand(String cmd) {
        List<String> parts = new ArrayList<>();
        boolean inQuote = false;
        StringBuilder cur = new StringBuilder();
        for (int i = 0; i < cmd.length(); i++) {
            char c = cmd.charAt(i);
            if (c == '"') { inQuote = !inQuote; }
            else if (c == ' ' && !inQuote) {
                if (cur.length() > 0) { parts.add(cur.toString()); cur = new StringBuilder(); }
            } else { cur.append(c); }
        }
        if (cur.length() > 0) parts.add(cur.toString());
        return parts.toArray(new String[0]);
    }

    // ======================================
    //  进程管理
    // ======================================

    static class ManagedProcess {
        final String name;
        final String command;
        final boolean isServer;
        final String pingUrl;
        volatile boolean running;
        volatile long startTime;

        ManagedProcess(String name, String command, boolean isServer, String pingUrl) {
            this.name = name;
            this.command = command;
            this.isServer = isServer;
            this.pingUrl = pingUrl;
        }

        /**
         * 在新窗口中启动进程。
         * 使用 start /D <workDir> 设置工作目录。
         */
        void start() {
            if (running) return;
            running = true;
            startTime = System.currentTimeMillis();

            new Thread(() -> {
                try {
                    String workDir = System.getProperty("user.dir");
                    String[] cmdParts = splitCommand(command);

                    // cmd /c start "AetherForge X" /D <workDir> cmd /c <cmd> <args>
                    String[] fullCmd = new String[cmdParts.length + 8];
                    fullCmd[0] = "cmd";
                    fullCmd[1] = "/c";
                    fullCmd[2] = "start";
                    fullCmd[3] = "AetherForge " + name;
                    fullCmd[4] = "/D";
                    fullCmd[5] = workDir;
                    fullCmd[6] = "cmd";
                    fullCmd[7] = "/k";
                    System.arraycopy(cmdParts, 0, fullCmd, 8, cmdParts.length);

                    System.out.println("[launcher] " + String.join(" ", fullCmd));

                    ProcessBuilder pb = new ProcessBuilder(fullCmd);
                    pb.directory(new File(workDir));
                    pb.redirectErrorStream(true);
                    Process proc = pb.start();
                    try (BufferedReader br = new BufferedReader(new InputStreamReader(proc.getInputStream()))) {
                        while (br.readLine() != null) { /* discard */ }
                    }
                } catch (Exception e) {
                    System.err.println("[launcher] 启动失败 " + name + ": " + e.getMessage());
                    running = false;
                }
            }, "proc-" + name).start();
        }

        void stop() {
            running = false;
            new Thread(() -> {
                try {
                    String[] killCmd = {"cmd", "/c", "taskkill", "/fi",
                        "WINDOWTITLE eq AetherForge " + name, "/f"};
                    ProcessBuilder pb = new ProcessBuilder(killCmd);
                    pb.redirectErrorStream(true);
                    Process proc = pb.start();
                    try (BufferedReader br = new BufferedReader(new InputStreamReader(proc.getInputStream()))) {
                        String line;
                        while ((line = br.readLine()) != null) {
                            System.out.println("[launcher] kill(" + name + "): " + line);
                        }
                    }
                    proc.waitFor(3, java.util.concurrent.TimeUnit.SECONDS);

                    if (command.startsWith("python")) {
                        Runtime.getRuntime().exec("taskkill /f /im python.exe");
                    } else if (command.startsWith("java")) {
                        Runtime.getRuntime().exec("taskkill /f /im java.exe");
                    }
                } catch (Exception e) {
                    System.err.println("[launcher] 停止失败 " + name + ": " + e.getMessage());
                }
            }, "kill-" + name).start();
        }

        boolean isAlive() {
            if (!running) return false;
            if (pingUrl != null && !pingUrl.isEmpty()) {
                try {
                    URI uri = new URI(pingUrl);
                    HttpRequest req = HttpRequest.newBuilder().uri(uri).GET()
                        .timeout(Duration.ofSeconds(2)).build();
                    HttpResponse<String> res = HttpClient.newBuilder()
                        .connectTimeout(Duration.ofSeconds(2))
                        .build().send(req, HttpResponse.BodyHandlers.ofString());
                    boolean ok = res.statusCode() == 200;
                    if (!ok) running = false;
                    return ok;
                } catch (Exception e) {
                    if (System.currentTimeMillis() - startTime < 20000) return true;
                    running = false;
                    return false;
                }
            }
            return running;
        }
    }

    ManagedProcess startProcess(String name, String command, boolean isServer) {
        String pingUrl = isServer ? "http://127.0.0.1:7890/api/tools" : null;
        ManagedProcess mp = new ManagedProcess(name, command, isServer, pingUrl);
        processes.add(mp);
        mp.start();
        return mp;
    }

    void checkServerStatus() {
        new Thread(() -> {
            try {
                URI uri = new URI("http://127.0.0.1:7890/api/tools");
                HttpRequest req = HttpRequest.newBuilder().uri(uri).GET()
                    .timeout(Duration.ofSeconds(3)).build();
                HttpResponse<String> res = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(3))
                    .build().send(req, HttpResponse.BodyHandlers.ofString());
                boolean online = res.statusCode() == 200;
                SwingUtilities.invokeLater(() -> setGlobalStatus(online ? "服务器运行中" : "服务器未响应"));
            } catch (Exception e) {
                SwingUtilities.invokeLater(() -> setGlobalStatus("服务器未运行"));
            }
        }).start();
    }
}