# ai-google-ruleset

自动生成 Mihomo（`.mrs` / `.yaml`）与 sing-box（`.srs` / `.json`）规则集：分离 Google AI/OpenAI（含 Google 登录认证）与 Google 其他服务，并提供独立的桌面进程与安卓包名规则集。

## 规则集说明

- **`ai-google-openai`**：纯域名规则集，包含 Google AI（`google-deepmind` 及 Antigravity / AI Studio / Gemini 补漏）、OpenAI（`openai`）以及 Google 登录认证相关域名（`accounts.google.com`、`oauth2.googleapis.com` 等），兼容 `.mrs` 与 DNS 规则。
- **`ai-apps-process`**：独立进程与包名规则集（来自 `rules/custom_ai_apps.txt`），包含桌面端 AI 应用进程名与 Android 应用包名（不含 `com.google.android.gms`，登录认证交由域名规则精准分流）。
- **`google-other`**：纯域名规则集，从 `google` 规则集中剔除已划入 `ai-google-openai` 的域名与后缀后，剩余的 Google 常规服务。

## 订阅路径

### Mihomo（`.mrs` / `.yaml`）

- `dist/mihomo/ai-google-openai.mrs`（`behavior: domain`，纯域名，推荐）
- `dist/mihomo/ai-google-openai.yaml`
- `dist/mihomo/ai-apps-process.yaml`（`behavior: classical`，桌面进程 + 安卓包名）
- `dist/mihomo/google-other.mrs`（`behavior: domain`，Google 其他常规服务）
- `dist/mihomo/google-other.yaml`

### sing-box（`.srs` / `.json`）

- `dist/singbox/ai-google-openai.srs`（纯域名，DNS 与 Route 通用）
- `dist/singbox/ai-google-openai.json`
- `dist/singbox/ai-apps-process.srs`（`process_name` + `package_name`，Route 专用）
- `dist/singbox/ai-apps-process.json`
- `dist/singbox/google-other.srs`（Google 其他常规服务）
- `dist/singbox/google-other.json`

## 自动更新与邮件通知

- **自动分析与更新**：每日 UTC 04:00 定时运行（亦可在 Actions 页面手动触发 `Build Rulesets`），自动拉取上游规则并识别新增 AI 域名，编译生成 `.mrs` / `.yaml` / `.srs` / `.json` 产物及变更统计 `dist/latest_diff.md` 提交至 `dist/` 目录。
- **邮件通知方式**：
  1. **GitHub Issue 邮件通知（开箱即用）**：检测到规则集变更时自动创建 Issue，触发 GitHub 原生邮件通知。
  2. **自定义 SMTP 邮件通知（可选）**：在仓库 Secrets 中配置 `MAIL_SERVER`、`MAIL_PORT`、`MAIL_USERNAME`、`MAIL_PASSWORD`、`MAIL_TO` 即可启用。
