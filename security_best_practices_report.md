# AetherForge 安全审计报告

> 日期：2026-07-17
> 范围：Flask Web Server（main.py, server.py），API 层，配置系统
> 参考：python-flask-web-server-security.md

---

## 执行摘要

审计发现 **1 个运行时崩溃缺陷**（self 未定义），**4 项关键安全配置缺失**（SECRET_KEY、CSRF、CORS、安全头），以及若干中等严重性问题。MCP Server 层（asyncio 驱动）无 HTTP 攻击面，风险较低。

---

## 严重问题

### CRIT-001：server.py game_state_3d 引用未定义 self → 运行时崩溃

- **Severity**: Critical
- **Location**: `aetherforge/api/server.py` L71-L85，`game_state_3d()` 函数
- **Evidence**:
  ```python
  @app.route("/api/game-state-3d", methods=["GET"])
  def game_state_3d():
      sg = SceneGraph3D(self.world)   # ← self 不存在！
      ...
      state["tick"] = self.world.tick # ← self 不存在！
  ```
- **Impact**: 调用 `/api/game-state-3d` 直接抛 `NameError: name "self" is not defined`，返回 500。该端点本应为 3D 渲染提供数据。
- **Root Cause**: `game_state_3d` 是嵌套函数（非方法），`self` 未从闭包传入。外层 `create_server()` 返回了 `world` 变量但未被函数捕获。
- **Fix**: 使用 `world` 闭包变量替代 `self.world`。

---

## 高严重性问题

### HIGH-001：Flask 应用未设置 SECRET_KEY

- **Severity**: High
- **Location**: `aetherforge/main.py` L78 (`app = Flask(...)`) 和 `aetherforge/api/server.py` L11
- **Evidence**:
  ```python
  app = Flask(__name__, static_folder=static_dir, static_url_path="")
  # 从未设置 app.secret_key 或 app.config["SECRET_KEY"]
  ```
- **Impact**: Flask 使用 `session` 对象时报错（`RuntimeError: The session is unavailable because no secret key was set`）。如果使用了 session，服务端直接崩溃。即使用不到 session，缺少 SECRET_KEY 也意味着后续扩展 session 功能时必须断代。
- **Fix**: 从环境变量或配置加载：
  ```python
  app.config["SECRET_KEY"] = os.environ.get(
      "AETHERFORGE_SECRET_KEY",
      "dev-secret-do-not-use-in-production"  # 开发用，生产必须覆盖
  )
  ```

### HIGH-002：API 端点无 CSRF 保护

- **Severity**: High
- **Location**: `aetherforge/main.py` L56-62 (`/api/tools/<tool_name>` POST 和 `/api/tools` GET) 以及 `server.py` L19-25
- **Evidence**: 所有 POST 端点直接调用 `request.get_json()` → `fn(**data)`，无 CSRF token 校验。
- **Impact**: 如果用户通过浏览器访问了恶意站点，该站点可以跨站请求伪造对 AetherForge API 执行任意工具调用（创建实体、修改世界状态等）。
- **Fix**: 由于 AetherForge 是本地开发工具（监听 127.0.0.1），CSRF 风险较低。但如果未来开放到网络，必须添加 CSRF 保护。当前建议：
  - 确认 `host` 始终绑定 `127.0.0.1`（当前默认且推荐）
  - 添加 `flask-wtf` CSRFProtect 或自定义 token 校验

### HIGH-003：无 CORS 配置

- **Severity**: High
- **Location**: `aetherforge/main.py`，`aetherforge/api/server.py`
- **Evidence**: 未使用 `flask_cors.CORS()`，也没有自定义 `Access-Control-Allow-Origin` 头。
- **Impact**: 当部署到非 localhost 环境时（比如局域网），前端页面跨域请求 API 会被浏览器拦截。
- **Fix**: 添加 CORS 支持（限制到可信任源）：

### HIGH-004：缺少安全响应头

- **Severity**: High
- **Location**: `aetherforge/main.py` L56-100，所有 API 路由
- **Evidence**: 响应头中未设置：
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Content-Security-Policy`
- **Impact**: 静态文件或 API 响应可能被浏览器 MIME 嗅探，或被嵌入 iframe 导致点击劫持。
- **Fix**: 使用 Flask `after_request` 处理器添加默认安全头。

---

## 中严重性问题

### MED-001：工具调用参数无输入校验

- **Severity**: Medium
- **Location**: `main.py` L58-62
  ```python
  result = call_fn(tool_name, request.get_json(silent=True) or {})
  ```
- **Impact**: 用户通过 HTTP POST 发送的 JSON 被直接解包为 `**kwargs` 传给工具函数。虽然攻击面限于 EngineTools 的公开方法列表，但恶意 payload（如超长字符串、嵌套 dict 炸弹）可能导致拒绝服务。
- **Fix**: 对 `tool_name` 做 allowlist 校验；对 `request.content_length` 设上限。

### MED-002：webbrowser.open 使用用户可控 host

- **Severity**: Medium
- **Location**: `main.py` L101-102
  ```python
  webbrowser.open(f"http://{self.host}:{self.port}/")
  ```
- **Impact**: 如果 `--host` 参数被注入（例如 `--host "attacker.com/foo"`），`webbrowser.open` 可能被诱导打开恶意地址。虽然 CLI 参数通常可信，但应加校验。
- **Fix**: 对 `host` 做格式校验（只允许 IP 或合法的 hostname）。

### MED-003：config.yaml 写入了明文路径

- **Severity**: Medium
- **Location**: `config.py` L117-118
  ```python
  with open(CONFIG_FILE, "w", encoding="utf-8") as f:
      yaml.dump(cfg.to_dict(), f, ...)
  ```
- **Evidence**: 配置中可能包含 `model_path` 等本地路径信息。虽非密码，但本地路径泄露可被用于定位用户文件系统结构。
- **Fix**: 文档中提醒用户检查 config.yaml 内容，不要提交到公开仓库。已加入 `.gitignore` 最佳实践。

---

## 低严重性问题

### LOW-001：Flask 开发服务器警告

- **Severity**: Low
- **Location**: `main.py` L103
  ```python
  self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
  ```
- **Evidence**: 启动时 Flask 输出 `WARNING: This is a development server.` 这是正常行为，因为确实在用内置 dev server。
- **Note**: 生产部署记得换 WSGI（gunicorn/waitress），目前对 AI 工具开发场景可以接受。

### LOW-002：server.py `game_state_3d` 缩进不一致

- **Severity**: Low
- **Location**: `server.py` L63-85
- **Evidence**: `game_state_3d` 函数与其他路由的缩进层级不同（多缩进了一级），表明它可能是从其他类复制粘贴的残留代码。
- **Fix**: 统一缩进并修复 self → world 引用。

---

## 总结

| ID | 严重性 | 问题 | 文件 |
|----|--------|------|------|
| CRIT-001 | 🔴 Critical | `self` 未定义 → 崩溃 | `server.py:71` |
| HIGH-001 | 🟠 High | 无 SECRET_KEY | `main.py:78` |
| HIGH-002 | 🟠 High | 无 CSRF 保护 | `main.py:56` |
| HIGH-003 | 🟠 High | 无 CORS 配置 | `main.py` |
| HIGH-004 | 🟠 High | 无安全响应头 | `main.py` |
| MED-001 | 🟡 Medium | 输入无校验 | `main.py:59` |
| MED-002 | 🟡 Medium | host 参数未校验 | `main.py:102` |
| MED-003 | 🟡 Medium | 明文路径写入 config | `config.py:117` |
| LOW-001 | ⚪ Low | 开发服务器警告 | `main.py:103` |
| LOW-002 | ⚪ Low | 缩进不一致 | `server.py:63` |
