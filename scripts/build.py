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
    for old_file in (
        f"{OUT_MIHOMO}/ai-google-openai.txt",
        f"{OUT_MIHOMO}/ai-google-openai.yaml",
        f"{OUT_MIHOMO}/ai-google-openai.mrs",
        f"{OUT_MIHOMO}/ai-apps-process.yaml",
        f"{OUT_SINGBOX}/ai-google-openai.json",
        f"{OUT_SINGBOX}/ai-google-openai.srs",
        f"{OUT_SINGBOX}/ai-apps-process.json",
        f"{OUT_SINGBOX}/ai-apps-process.srs",
    ):
        if os.path.exists(old_file):
            os.remove(old_file)

    g_ai_d, g_ai_s = fetch_yaml_domains("google-deepmind")
    g_cus_d, g_cus_s = load_custom_domains("rules/google_ai_domains.txt")
    google_d, google_s = fetch_yaml_domains("google")

    oai_d, oai_s = fetch_yaml_domains("openai")
    oai_cus_d, oai_cus_s = load_custom_domains("rules/openai_domains.txt")

    g_apps_proc, g_apps_pkg = load_custom_apps("rules/google_ai_apps.txt")
    oai_apps_proc, oai_apps_pkg = load_custom_apps("rules/openai_apps.txt")

    base_google_ai_d = g_ai_d | g_cus_d
    base_google_ai_s = g_ai_s | g_cus_s

    auto_d = {d for d in google_d if d not in base_google_ai_d and is_auto_ai(d)}
    auto_s = {s for s in google_s if s not in base_google_ai_s and is_auto_ai(s)}

    google_ai_domains = base_google_ai_d | auto_d
    google_ai_suffixes = base_google_ai_s | auto_s

    openai_domains = oai_d | oai_cus_d
    openai_suffixes = oai_s | oai_cus_s

    other_domains = {
        d for d in google_d
        if d not in google_ai_domains and not any(d == s or d.endswith("." + s) for s in google_ai_suffixes)
    }
    other_suffixes = {
        s for s in google_s
        if s not in google_ai_suffixes and not any(s.endswith("." + a) for a in google_ai_suffixes)
    }

    g_ai_add, g_ai_del = write_domain_outputs("google-ai", google_ai_domains, google_ai_suffixes)
    oai_add, oai_del = write_domain_outputs("openai", openai_domains, openai_suffixes)
    ot_add, ot_del = write_domain_outputs("google-other", other_domains, other_suffixes)
    g_app_add, g_app_del = write_app_outputs("google-ai-apps", g_apps_proc, g_apps_pkg)
    oai_app_add, oai_app_del = write_app_outputs("openai-apps", oai_apps_proc, oai_apps_pkg)

    auto_list = sorted(auto_d | {f"+.{s}" for s in auto_s})
    with open("dist/auto_discovered_ai.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(auto_list) + ("\n" if auto_list else ""))

    changed = bool(
        g_ai_add or g_ai_del or oai_add or oai_del or ot_add or ot_del or g_app_add or g_app_del or oai_app_add or oai_app_del
    )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = [f"# 规则集变更报告 ({now})\n"]
    report.append(f"- `google-ai`: 新增 {len(g_ai_add)} 条, 移除 {len(g_ai_del)} 条")
    report.append(f"- `openai`: 新增 {len(oai_add)} 条, 移除 {len(oai_del)} 条")
    report.append(f"- `google-other`: 新增 {len(ot_add)} 条, 移除 {len(ot_del)} 条")
    report.append(f"- `google-ai-apps`: 新增 {len(g_app_add)} 条, 移除 {len(g_app_del)} 条")
    report.append(f"- `openai-apps`: 新增 {len(oai_app_add)} 条, 移除 {len(oai_app_del)} 条")
    report.append(f"- 自动分析从 Google 上游新识别的 AI 域名: {len(auto_list)} 条\n")

    def append_section(title, items):
        if items:
            report.append(f"## {title} ({len(items)})")
            report.extend([f"- `{x}`" for x in items[:100]])
            if len(items) > 100:
                report.append(f"- ...其余 {len(items) - 100} 条略")
            report.append("")

    append_section("google-ai 新增", g_ai_add)
    append_section("google-ai 移除", g_ai_del)
    append_section("openai 新增", oai_add)
    append_section("openai 移除", oai_del)
    append_section("google-other 新增", ot_add)
    append_section("google-other 移除", ot_del)
    append_section("google-ai-apps 新增", g_app_add)
    append_section("google-ai-apps 移除", g_app_del)
    append_section("openai-apps 新增", oai_app_add)
    append_section("openai-apps 移除", oai_app_del)
    append_section("自动识别的 AI 域名", auto_list)

    with open("dist/latest_diff.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    main()

def main():
