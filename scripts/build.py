import json
import os
import urllib.request

BASE = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite"
OUT_MIHOMO = "dist/mihomo"
OUT_SINGBOX = "dist/singbox"


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


def load_custom(path):
    domains, suffixes = set(), set()
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("+."):
                suffixes.add(line[2:].lower())
            elif line.startswith("."):
                suffixes.add(line[1:].lower())
            else:
                domains.add(line.lower())
    return domains, suffixes


def write_outputs(name, domains, suffixes):
    os.makedirs(OUT_MIHOMO, exist_ok=True)
    os.makedirs(OUT_SINGBOX, exist_ok=True)
    sorted_domains = sorted(domains)
    sorted_suffixes = sorted(suffixes)

    # Mihomo text & yaml
    lines = [f"+.{s}" for s in sorted_suffixes] + sorted_domains
    with open(f"{OUT_MIHOMO}/{name}.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(f"{OUT_MIHOMO}/{name}.yaml", "w", encoding="utf-8") as f:
        f.write("payload:\n")
        for item in lines:
            f.write(f"  - '{item}'\n")

    # sing-box rule-set source json (version 2)
    rule = {}
    if sorted_domains:
        rule["domain"] = sorted_domains
    if sorted_suffixes:
        rule["domain_suffix"] = sorted_suffixes
    payload = {"version": 2, "rules": [rule]}
    with open(f"{OUT_SINGBOX}/{name}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    g_ai_d, g_ai_s = fetch_yaml_domains("google-deepmind")
    oai_d, oai_s = fetch_yaml_domains("openai")
    cus_d, cus_s = load_custom("rules/custom_ai_auth.txt")
    google_d, google_s = fetch_yaml_domains("google")

    ai_domains = g_ai_d | oai_d | cus_d
    ai_suffixes = g_ai_s | oai_s | cus_s

    # Google 其他服务：剔除已划入 AI 通道的域名与后缀
    other_domains = {
        d for d in google_d
        if d not in ai_domains and not any(d == s or d.endswith("." + s) for s in ai_suffixes)
    }
    other_suffixes = {
        s for s in google_s
        if s not in ai_suffixes and not any(s.endswith("." + a) for a in ai_suffixes)
    }

    write_outputs("ai-google-openai", ai_domains, ai_suffixes)
    write_outputs("google-other", other_domains, other_suffixes)


if __name__ == "__main__":
    main()
