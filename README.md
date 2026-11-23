# ai-google-ruleset

自动生成 Mihomo（`.mrs` / `.yaml`）与 sing-box（`.srs` / `.json`）规则集：分离 Google AI/OpenAI（含 Google 登录认证）与 Google 其他服务，并提供独立的桌面进程与安卓包名规则集。

## 规则集说明

- **google-ai**：纯域名规则集，包含 Google AI（`google-deepmind` 及 Antigravity / AI Studio / Gemini 补漏）与 Google 登录认证相关域名（`accounts.google.com`、`oauth2.googleapis.com` 等），兼容 `.mrs` 与 DNS 规则。
- **openai**：纯域名规则集，包含 OpenAI / ChatGPT 相关域名（`openai`），兼容 `.mrs` 与 DNS 规则。
- **google-ai-apps**：独立进程与包名规则集，包含 Google AI 桌面端应用进程名与 Android 应用包名。
- **openai-apps**：独立进程与包名规则集，包含 OpenAI / ChatGPT 桌面端应用进程名与 Android 应用包名。注意：`ChatGPT.exe` 在某些 Windows 安装中也是 Codex 的进程名，因此该规则也会把该进程的流量送到 OpenAI 组。
- **google-other**：纯域名规则集，从 `google` 规则集中剔除已划入 `google-ai` 的域名与后缀后，剩余的 Google 常规服务。

## 订阅路径

### Mihomo (`.mrs` / `.yaml`)

- `dist/mihomo/google-ai.mrs`（`behavior: domain`，纯域名，推荐）
- `dist/mihomo/google-ai.yaml`
- `dist/mihomo/openai.mrs`（`behavior: domain`，纯域名，推荐）
- `dist/mihomo/openai.yaml`
- `dist/mihomo/google-ai-apps.yaml`（`behavior: classical`，Google AI 桌面进程 + 安卓包名）
- `dist/mihomo/openai-apps.yaml`（`behavior: classical`，OpenAI 桌面进程 + 安卓包名）
- `dist/mihomo/google-other.mrs`（`behavior: domain`，Google 其他常规服务）
- `dist/mihomo/google-other.yaml`

### sing-box (`.srs` / `.json`)

- `dist/singbox/google-ai.srs`（纯域名，DNS 与 Route 通用）
- `dist/singbox/google-ai.json`
- `dist/singbox/openai.srs`（纯域名，DNS 与 Route 通用）
- `dist/singbox/openai.json`
- `dist/singbox/google-ai-apps.srs`（`process_name` + `package_name`，Route 专用）
- `dist/singbox/google-ai-apps.json`
- `dist/singbox/openai-apps.srs`（`process_name` + `package_name`，Route 专用）
- `dist/singbox/openai-apps.json`
- `dist/singbox/google-other.srs`（Google 其他常规服务）
- `dist/singbox/google-other.json`
## 自动更新与邮件通知

- **自动分析与更新**：每日 UTC 04:00 定时运行（亦可在 Actions 页面手动触发 `Build Rulesets`），自动拉取上游规则并识别新增 AI 域名，编译生成 `.mrs` / `.yaml` / `.srs` / `.json` 产物及变更统计 `dist/latest_diff.md` 提交至 `dist/` 目录。
- **邮件通知方式**：
  1. **GitHub Issue 邮件通知（开箱即用）**：检测到规则集变更时自动创建 Issue，触发 GitHub 原生邮件通知。
  2. **自定义 SMTP 邮件通知（可选）**：在仓库 Secrets 中配置 `MAIL_SERVER`、`MAIL_PORT`、`MAIL_USERNAME`、`MAIL_PASSWORD`、`MAIL_TO` 即可启用。
## 最小接入示例

以下示例采用**应用优先**策略：将 `*-apps` 规则放在 AI 域名规则之前，且 `google-ai` 放在 `google-other` 之前；**DNS 规则只引用纯域名规则集**（`google-ai`、`openai`、`google-other`），并明确 `google-ai` 优先于 `google-other`。

### Mihomo 最小配置示例

```yaml
# 将 <RAW_BASE_URL> 替换为本仓库 main 分支对应 dist 文件的 Raw 地址前缀
rule-providers:
  google-ai-apps:
    type: http
    behavior: classical
    url: "<RAW_BASE_URL>/dist/mihomo/google-ai-apps.yaml"
    path: ./ruleset/google-ai-apps.yaml
    interval: 86400
  openai-apps:
    type: http
    behavior: classical
    url: "<RAW_BASE_URL>/dist/mihomo/openai-apps.yaml"
    path: ./ruleset/openai-apps.yaml
    interval: 86400
  google-ai:
    type: http
    behavior: domain
    format: mrs
    url: "<RAW_BASE_URL>/dist/mihomo/google-ai.mrs"
    path: ./ruleset/google-ai.mrs
    interval: 86400
  openai:
    type: http
    behavior: domain
    format: mrs
    url: "<RAW_BASE_URL>/dist/mihomo/openai.mrs"
    path: ./ruleset/openai.mrs
    interval: 86400
  google-other:
    type: http
    behavior: domain
    format: mrs
    url: "<RAW_BASE_URL>/dist/mihomo/google-other.mrs"
    path: ./ruleset/google-other.mrs
    interval: 86400

dns:
  # DNS 仅引用纯域名规则集，且 google-ai 优先于 google-other
  nameserver-policy:
    "rule-set:google-ai": tls://dns.google
    "rule-set:openai": tls://dns.google
    "rule-set:google-other": tls://1.1.1.1

rules:
  # 1. 应用优先：Apps 规则放在 AI 域名规则之前
  - RULE-SET,google-ai-apps,Google-AI
  - RULE-SET,openai-apps,OpenAI
  # 2. AI 域名规则：google-ai 放在 google-other 之前
  - RULE-SET,google-ai,Google-AI
  - RULE-SET,openai,OpenAI
  # 3. 其余 Google 常规服务
  - RULE-SET,google-other,Google-Other
```

### sing-box 最小配置示例

```json
{
  "dns": {
    "rules": [
      { "rule_set": "google-ai", "server": "dns_ai" },
      { "rule_set": "openai", "server": "dns_ai" },
      { "rule_set": "google-other", "server": "dns_google" }
    ]
  },
  "route": {
    "rule_set": [
      { "tag": "google-ai-apps", "type": "remote", "format": "binary", "url": "<RAW_BASE_URL>/dist/singbox/google-ai-apps.srs" },
      { "tag": "openai-apps", "type": "remote", "format": "binary", "url": "<RAW_BASE_URL>/dist/singbox/openai-apps.srs" },
      { "tag": "google-ai", "type": "remote", "format": "binary", "url": "<RAW_BASE_URL>/dist/singbox/google-ai.srs" },
      { "tag": "openai", "type": "remote", "format": "binary", "url": "<RAW_BASE_URL>/dist/singbox/openai.srs" },
      { "tag": "google-other", "type": "remote", "format": "binary", "url": "<RAW_BASE_URL>/dist/singbox/google-other.srs" }
    ],
    "rules": [
      { "rule_set": "google-ai-apps", "outbound": "Google-AI" },
      { "rule_set": "openai-apps", "outbound": "OpenAI" },
      { "rule_set": "google-ai", "outbound": "Google-AI" },
      { "rule_set": "openai", "outbound": "OpenAI" },
      { "rule_set": "google-other", "outbound": "Google-Other" }
    ]
  }
}
```

## 分流演示与注意事项

- **分流演示（`gemini.google.com` vs `mail.google.com`）**：
  - 访问 `gemini.google.com`：先命中 `google-ai`，请求被路由至 `Google-AI` 组。
  - 访问 `mail.google.com`：不命中 `google-ai`，继续向下命中 `google-other`，请求被路由至 `Google-Other` 组。
- **共享登录域名提示（`accounts.google.com`）**：`accounts.google.com` 属于 Google 共享登录域名；将其加入 `google-ai` 规则会同时影响其他 Google 服务的登录请求（例如登录 Gmail、YouTube 等常规服务时的认证流量也会一并走 `Google-AI` 组）。
