import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


CASES = {
    "google-ai": (("gemini.google.com", "accounts.google.com"), ("mail.google.com",)),
    "google-other": (("mail.google.com", "drive.google.com"), ()),
    "openai": (("api.openai.com",), ("gemini.google.com",)),
    "google-drive": (
        ("drive.google.com", "sub.docs.google.com", "drive.usercontent.google.com",
         "drive-data-export.usercontent.google.com", "drivefs.googleapis.com"),
        ("accounts.google.com", "gemini.google.com", "storage.googleapis.com"),
    ),
    "github": (
        ("github.com", "raw.githubusercontent.com", "release-assets.githubusercontent.com"),
        ("github.com.example.org", "x.com"),
    ),
    "x": (("x.com", "pbs.twimg.com", "video.twimg.com", "t.co"), ("github.com",)),
    "telegram": (("t.me", "telegram.org", "cdn-telegram.org"), ("x.com",)),
}

APP_CASES = {
    "google-ai-apps": ("Gemini.exe", "com.google.android.apps.bard"),
    "openai-apps": ("ChatGPT.exe", "com.openai.chatgpt"),
}


def matches(host, domains, suffixes):
    return host in domains or any(host == suffix or host.endswith("." + suffix) for suffix in suffixes)


def verify_cases(name, engine, domains, suffixes):
    included, excluded = CASES[name]
    for host in included:
        if not matches(host, domains, suffixes):
            raise ValueError(f"{engine} {name} failed to match {host}")
    for host in excluded:
        if matches(host, domains, suffixes):
            raise ValueError(f"{engine} {name} unexpectedly matched {host}")


def values(value):
    # sing-box decompiles a one-item list to a scalar.
    return [value] if isinstance(value, str) else value


def decompile_sing_box(sing_box, name, folder):
    path = folder / f"{name}.json"
    subprocess.run(
        [sing_box, "rule-set", "decompile", f"dist/singbox/{name}.srs", "-o", str(path)],
        check=True,
    )
    return json.loads(path.read_text(encoding="utf-8"))["rules"]


def matches_app(rules, field, name):
    return any(rule and all(key == field and name in values(value) for key, value in rule.items())
               for rule in rules)


def verify_apps(sing_box, folder):
    for name, (process, package) in APP_CASES.items():
        alternatives = {value for other, pair in APP_CASES.items() if other != name for value in pair}
        rules = decompile_sing_box(sing_box, name, folder)
        lines = Path(f"dist/mihomo/{name}.yaml").read_text(encoding="utf-8").splitlines()
        entries = {line.strip()[2:].strip("'\"") for line in lines if line.strip().startswith("- ")}
        if not matches_app(rules, "process_name", process) or not matches_app(rules, "package_name", package):
            raise ValueError(f"sing-box {name} must match both the process and package independently")
        for value in (process, package):
            if f"PROCESS-NAME,{value}" not in entries:
                raise ValueError(f"Mihomo {name} failed to match {value}")
        for value in alternatives:
            if any(matches_app(rules, field, value) for field in ("process_name", "package_name")):
                raise ValueError(f"sing-box {name} unexpectedly matched {value}")
            if f"PROCESS-NAME,{value}" in entries or f"PACKAGE-NAME,{value}" in entries:
                raise ValueError(f"Mihomo {name} unexpectedly matched {value}")
        print(f"PASS: {name} process and package (Mihomo and sing-box)")


def main():
    mihomo, sing_box = (str(Path(arg).resolve()) for arg in sys.argv[1:])
    with TemporaryDirectory() as temporary:
        folder = Path(temporary)
        for name in CASES:
            text_file = folder / f"{name}.txt"
            subprocess.run(
                [mihomo, "convert-ruleset", "domain", "mrs",
                 f"dist/mihomo/{name}.mrs", str(text_file)],
                check=True,
            )
            entries = text_file.read_text(encoding="utf-8").splitlines()
            domains = {entry for entry in entries if not entry.startswith("+.")}
            suffixes = {entry[2:] for entry in entries if entry.startswith("+.")}
            verify_cases(name, "Mihomo", domains, suffixes)

            rules = decompile_sing_box(sing_box, name, folder)
            domains = {host for rule in rules for host in values(rule.get("domain", []))}
            suffixes = {host for rule in rules for host in values(rule.get("domain_suffix", []))}
            verify_cases(name, "sing-box", domains, suffixes)
            print(f"PASS: {name} (Mihomo and sing-box)")
        verify_apps(sing_box, folder)


if __name__ == "__main__":
    main()
