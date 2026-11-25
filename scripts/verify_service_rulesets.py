import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


CASES = {
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


def main():
    mihomo, sing_box = (str(Path(arg).resolve()) for arg in sys.argv[1:])
    with TemporaryDirectory() as temporary:
        folder = Path(temporary)
        for name in CASES:
            text_file = folder / f"{name}.txt"
            json_file = folder / f"{name}.json"
            subprocess.run(
                [mihomo, "convert-ruleset", "domain", "mrs",
                 f"dist/mihomo/{name}.mrs", str(text_file)],
                check=True,
            )
            entries = text_file.read_text(encoding="utf-8").splitlines()
            domains = {entry for entry in entries if not entry.startswith("+.")}
            suffixes = {entry[2:] for entry in entries if entry.startswith("+.")}
            verify_cases(name, "Mihomo", domains, suffixes)

            subprocess.run(
                [sing_box, "rule-set", "decompile", f"dist/singbox/{name}.srs",
                 "-o", str(json_file)],
                check=True,
            )
            rules = json.loads(json_file.read_text(encoding="utf-8"))["rules"]
            domains = {host for rule in rules for host in rule.get("domain", [])}
            suffixes = {host for rule in rules for host in rule.get("domain_suffix", [])}
            verify_cases(name, "sing-box", domains, suffixes)
            print(f"PASS: {name} (Mihomo and sing-box)")


if __name__ == "__main__":
    main()
