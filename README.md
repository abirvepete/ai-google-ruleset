# ai-google-ruleset

Automatically generated Mihomo (`.mrs` / `.yaml`) and sing-box (`.srs` / `.json`) rulesets that separate Google AI / OpenAI (including Google login authentication) from other Google services, with standalone rulesets for desktop processes and Android package names.

## Ruleset Overview

- **google-ai**: Pure domain ruleset containing Google AI (`google-deepmind` plus supplemental Antigravity / AI Studio / Gemini domains) and Google login authentication domains (`accounts.google.com`, `oauth2.googleapis.com`, etc.), compatible with `.mrs` and DNS rules.
- **openai**: Pure domain ruleset containing OpenAI / ChatGPT domains (`openai`), compatible with `.mrs` and DNS rules.
- **google-ai-apps**: Standalone process and package ruleset containing Google AI desktop application process names and Android package names.
- **openai-apps**: Standalone process and package ruleset containing OpenAI / ChatGPT desktop application process names and Android package names. Note: `ChatGPT.exe` is also the process name for Codex in some Windows installations, so this ruleset will also route that process's traffic to the OpenAI group.
- **google-other**: Pure domain ruleset containing the remaining regular Google services after excluding domains and suffixes already included in `google-ai` from the `google` ruleset.

## Subscription Paths

### Mihomo (`.mrs` / `.yaml`)

- `dist/mihomo/google-ai.mrs` (`behavior: domain`, pure domains, recommended)
- `dist/mihomo/google-ai.yaml`
- `dist/mihomo/openai.mrs` (`behavior: domain`, pure domains, recommended)
- `dist/mihomo/openai.yaml`
- `dist/mihomo/google-ai-apps.yaml` (`behavior: classical`, Google AI desktop processes + Android packages)
- `dist/mihomo/openai-apps.yaml` (`behavior: classical`, OpenAI desktop processes + Android packages)
- `dist/mihomo/google-other.mrs` (`behavior: domain`, other regular Google services)
- `dist/mihomo/google-other.yaml`

### sing-box (`.srs` / `.json`)

- `dist/singbox/google-ai.srs` (pure domains, for both DNS and Route)
- `dist/singbox/google-ai.json`
- `dist/singbox/openai.srs` (pure domains, for both DNS and Route)
- `dist/singbox/openai.json`
- `dist/singbox/google-ai-apps.srs` (`process_name` + `package_name`, for Route only)
- `dist/singbox/google-ai-apps.json`
- `dist/singbox/openai-apps.srs` (`process_name` + `package_name`, for Route only)
- `dist/singbox/openai-apps.json`
- `dist/singbox/google-other.srs` (pure domains, other regular Google services)
- `dist/singbox/google-other.json`

## Auto-Update & Email Notifications

- **Auto-analysis & update**: Runs daily at 04:00 UTC (or manually triggered via `Build Rulesets` in the Actions tab). Automatically fetches upstream rules, identifies newly added AI domains, compiles `.mrs` / `.yaml` / `.srs` / `.json` artifacts along with `dist/latest_diff.md`, and commits them to `dist/`.
- **Email notifications**:
  1. **GitHub Issue notifications (out-of-the-box)**: Automatically creates an Issue when ruleset changes are detected, triggering GitHub's native email notifications.
  2. **Custom SMTP email notifications (optional)**: Configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, and `MAIL_TO` in repository Secrets to enable.

## Minimal Integration Examples

The examples below follow an **apps-first** strategy: place `*-apps` rules before AI domain rules, and place `google-ai` before `google-other`; **DNS rules only reference pure domain rulesets** (`google-ai`, `openai`, `google-other`), with `google-ai` explicitly placed before `google-other`.

### Mihomo Minimal Configuration

```yaml
# Replace <RAW_BASE_URL> with the Raw URL prefix for the main branch of this repository
rule-providers:
  google-ai-apps:
    type: http
    behavior: classical
    format: yaml
    url: "<RAW_BASE_URL>/dist/mihomo/google-ai-apps.yaml"
    path: ./ruleset/google-ai-apps.yaml
    interval: 86400
  openai-apps:
    type: http
    behavior: classical
    format: yaml
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
  nameserver-policy:
    "rule-set:google-ai,openai": https://dns.google/dns-query
    "rule-set:google-other": https://dns.google/dns-query

rules:
  - RULE-SET,google-ai-apps,AI
  - RULE-SET,openai-apps,OpenAI
  - RULE-SET,google-ai,AI
  - RULE-SET,openai,OpenAI
  - RULE-SET,google-other,Google
```

### sing-box Minimal Configuration

```json
{
  "dns": {
    "rules": [
      {
        "rule_set": ["google-ai", "openai"],
        "server": "proxy-dns"
      },
      {
        "rule_set": ["google-other"],
        "server": "proxy-dns"
      }
    ]
  },
  "route": {
    "rules": [
      {
        "rule_set": "google-ai-apps",
        "outbound": "AI"
      },
      {
        "rule_set": "openai-apps",
        "outbound": "OpenAI"
      },
      {
        "rule_set": "google-ai",
        "outbound": "AI"
      },
      {
        "rule_set": "openai",
        "outbound": "OpenAI"
      },
      {
        "rule_set": "google-other",
        "outbound": "Google"
      }
    ],
    "rule_set": [
      {
        "tag": "google-ai-apps",
        "type": "remote",
        "format": "binary",
        "url": "<RAW_BASE_URL>/dist/singbox/google-ai-apps.srs"
      },
      {
        "tag": "openai-apps",
        "type": "remote",
        "format": "binary",
        "url": "<RAW_BASE_URL>/dist/singbox/openai-apps.srs"
      },
      {
        "tag": "google-ai",
        "type": "remote",
        "format": "binary",
        "url": "<RAW_BASE_URL>/dist/singbox/google-ai.srs"
      },
      {
        "tag": "openai",
        "type": "remote",
        "format": "binary",
        "url": "<RAW_BASE_URL>/dist/singbox/openai.srs"
      },
      {
        "tag": "google-other",
        "type": "remote",
        "format": "binary",
        "url": "<RAW_BASE_URL>/dist/singbox/google-other.srs"
      }
    ]
  }
}
```

## Split Routing Demonstration & Important Notes

- **Split routing (`gemini.google.com` vs `mail.google.com`)**:
  - `gemini.google.com` matches `google-ai` and is routed to the `AI` group.
  - `mail.google.com` does not match `google-ai`, so it falls through to `google-other` and is routed to the `Google` group.
- **Shared login domain (`accounts.google.com`)**: `accounts.google.com` is a shared Google authentication domain. Including it in `google-ai` keeps Google AI login requests consistent, but it will also affect other Google login requests (such as signing in to Gmail, Drive, or YouTube).
