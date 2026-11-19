import json
import os
import urllib.request
from datetime import datetime, timezone

BASE = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite"
OUT_MIHOMO = "dist/mihomo"
OUT_SINGBOX = "dist/singbox"

AUTO_AI_KEYWORDS = (
    "antigravity",
    "gemini",
    "aistudio",
    "makersuite",
    "deepmind",
    "generativelanguage",
    "generativeai",
    "cloudcode",
    "aicode",
    "aiplatform",
    "aisandbox",
    "notebooklm",
    "jules",
    "bard",
    "labs.google",
    "robinfrontend",
)


def fetch_yaml_domains(name):
    url = f"{BASE}/{name}.yaml"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    domains, suffixes = set(), set()
    with urllib.request.urlopen(req, timeout=30) as resp:
        for raw in resp.read().decode("utf-8").splitlines():
            line = raw.strip()
            if not line.startswith("-"):
                continue
            item = line.lstrip("-").strip().strip("'\"")
            if not item or item.startswith("#"):
                continue
            if item.startswith("+."):
                suffixes.add(item[2:].lower())
            elif item.startswith("."):
                suffixes.add(item[1:].lower())
            else:
                domains.add(item.lower())
    return domains, suffixes


def load_lines(path):
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip() and not line.strip().startswith("#")}


def load_custom_domains(path):
    domains, suffixes = set(), set()
    for item in load_lines(path):
        if item.startswith("+."):
            suffixes.add(item[2:].lower())
        elif item.startswith("."):
            suffixes.add(item[1:].lower())
        else:
            domains.add(item.lower())
    return domains, suffixes


def load_custom_apps(path):
    processes, packages = set(), set()
    for item in load_lines(path):
        if item.startswith("process:"):
            processes.add(item[len("process:"):].strip())
        elif item.startswith("package:"):
            packages.add(item[len("package:"):].strip())
    return processes, packages


def is_auto_ai(host):
    return any(kw in host for kw in AUTO_AI_KEYWORDS)


def write_domain_outputs(name, domains, suffixes):
    os.makedirs(OUT_MIHOMO, exist_ok=True)
    os.makedirs(OUT_SINGBOX, exist_ok=True)
    sorted_domains = sorted(domains)
    sorted_suffixes = sorted(suffixes)

    lines = [f"+.{s}" for s in sorted_suffixes] + sorted_domains
    txt_path = f"{OUT_MIHOMO}/{name}.txt"
    old_lines = load_lines(txt_path)
    new_lines = set(lines)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(f"{OUT_MIHOMO}/{name}.yaml", "w", encoding="utf-8") as f:
        f.write("payload:\n")
        for item in lines:
            f.write(f"  - '{item}'\n")

    rule = {}
    if sorted_domains:
        rule["domain"] = sorted_domains
    if sorted_suffixes:
        rule["domain_suffix"] = sorted_suffixes
    payload = {"version": 2, "rules": [rule]}
    with open(f"{OUT_SINGBOX}/{name}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return sorted(new_lines - old_lines), sorted(old_lines - new_lines)


def write_app_outputs(name, processes, packages):
    os.makedirs(OUT_MIHOMO, exist_ok=True)
    os.makedirs(OUT_SINGBOX, exist_ok=True)
    sorted_proc = sorted(processes)
    sorted_pkg = sorted(packages)

    # Mihomo classical yaml (PROCESS-NAME 兼容桌面进程名与安卓包名)
    mihomo_lines = [f"PROCESS-NAME,{p}" for p in sorted_proc + sorted_pkg]
    yaml_path = f"{OUT_MIHOMO}/{name}.yaml"
    old_lines = set()
    if os.path.exists(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            for raw in f:
                s = raw.strip()
                if s.startswith("- "):
                    old_lines.add(s[2:].strip().strip("'\""))
    new_lines = set(mihomo_lines)

    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write("payload:\n")
        for item in mihomo_lines:
            f.write(f"  - '{item}'\n")

    # sing-box rule-set source json (version 2)
    rule = {}
    if sorted_proc:
        rule["process_name"] = sorted_proc
    if sorted_pkg:
        rule["package_name"] = sorted_pkg
    payload = {"version": 2, "rules": [rule]}
    with open(f"{OUT_SINGBOX}/{name}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return sorted(new_lines - old_lines), sorted(old_lines - new_lines)


def main():
    g_ai_d, g_ai_s = fetch_yaml_domains("google-deepmind")
    oai_d, oai_s = fetch_yaml_domains("openai")
    cus_d, cus_s = load_custom_domains("rules/custom_ai_auth.txt")
    google_d, google_s = fetch_yaml_domains("google")
    processes, packages = load_custom_apps("rules/custom_ai_apps.txt")

    base_ai_d = g_ai_d | oai_d | cus_d
    base_ai_s = g_ai_s | oai_s | cus_s

    auto_d = {d for d in google_d if d not in base_ai_d and is_auto_ai(d)}
    auto_s = {s for s in google_s if s not in base_ai_s and is_auto_ai(s)}

    ai_domains = base_ai_d | auto_d
    ai_suffixes = base_ai_s | auto_s

    other_domains = {
        d for d in google_d
        if d not in ai_domains and not any(d == s or d.endswith("." + s) for s in ai_suffixes)
    }
    other_suffixes = {
        s for s in google_s
        if s not in ai_suffixes and not any(s.endswith("." + a) for a in ai_suffixes)
    }

    ai_add, ai_del = write_domain_outputs("ai-google-openai", ai_domains, ai_suffixes)
    ot_add, ot_del = write_domain_outputs("google-other", other_domains, other_suffixes)
    app_add, app_del = write_app_outputs("ai-apps-process", processes, packages)

    auto_list = sorted([f"+.{s}" for s in auto_s] + list(auto_d))
    with open("dist/auto_detected.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(auto_list) + ("\n" if auto_list else ""))

    changed = bool(ai_add or ai_del or ot_add or ot_del or app_add or app_del)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = [f"# 规则集变更报告 ({now})\n"]
    report.append(f"- `ai-google-openai`: 新增 {len(ai_add)} 条，移除 {len(ai_del)} 条")
    report.append(f"- `google-other`: 新增 {len(ot_add)} 条，移除 {len(ot_del)} 条")
    report.append(f"- `ai-apps-process`: 新增 {len(app_add)} 条，移除 {len(app_del)} 条")
    report.append(f"- 自动分析从 Google 上游新识别的 AI 域名: {len(auto_list)} 条\n")

    def append_section(title, items):
        if items:
            report.append(f"## {title} ({len(items)})")
            report.extend([f"- `{x}`" for x in items[:100]])
            if len(items) > 100:
                report.append(f"- ...其余 {len(items) - 100} 条略")
            report.append("")

    append_section("ai-google-openai 新增", ai_add)
    append_section("ai-google-openai 移除", ai_del)
    append_section("google-other 新增", ot_add)
    append_section("google-other 移除", ot_del)
    append_section("ai-apps-process 新增", app_add)
    append_section("ai-apps-process 移除", app_del)
    append_section("自动分析识别的 AI 域名", auto_list)

    with open("dist/latest_diff.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    main()
