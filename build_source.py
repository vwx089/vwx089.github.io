#!/usr/bin/env python3
"""Baut die gemeinsame SideStore-Quelle aus apps.json.

Für jede App werden die Releases ihrer Repo über die GitHub-API gelesen.
Die neuesten brauchbaren Builds (IPA vorhanden und nicht winzig) landen
als Versionen in source.json. Neue App: nur einen Eintrag in apps.json.

Aufruf: python3 build_source.py [ausgabe.json]
Optional GH_TOKEN/GITHUB_TOKEN für höhere API-Grenzen.
"""
import json
import os
import re
import sys
import urllib.request

MAX_VERSIONS = 5          # so viele ältere Builds bleiben in SideStore wählbar
MIN_IPA_BYTES = 50_000    # kleinere IPAs sind kaputte Builds (leer)
APP_FIELDS = ("name", "bundleIdentifier", "developerName", "subtitle",
              "localizedDescription", "iconURL", "tintColor", "category",
              "screenshotURLs", "appPermissions")


def api(path):
    req = urllib.request.Request(f"https://api.github.com/{path}",
                                 headers={"Accept": "application/vnd.github+json",
                                          "User-Agent": "sidestore-source-builder"})
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def version_of(release):
    # Tags wie v1.0.11 oder build-2; Titel wie "Motorsound 0.1.2"
    for text in (release.get("name") or "", release.get("tag_name") or ""):
        m = re.search(r"\d+\.\d+(?:\.\d+)*", text)
        if m:
            return m.group(0)
    return release["tag_name"]


def notes_of(release):
    body = (release.get("body") or "").strip()
    return body.splitlines()[0] if body else release.get("name") or ""


def versions_for(app):
    releases = api(f"repos/{app['repo']}/releases?per_page=30")
    out = []
    for rel in releases:
        if rel.get("draft") or rel.get("prerelease"):
            continue
        asset = next((a for a in rel.get("assets", []) if a["name"] == app["asset"]), None)
        if not asset or asset["size"] < MIN_IPA_BYTES:
            continue
        version = version_of(rel)
        out.append({
            "version": version,
            "buildVersion": version.split(".")[-1],
            "date": rel["published_at"],
            "localizedDescription": notes_of(rel),
            "downloadURL": asset["browser_download_url"],
            "size": asset["size"],
            "minOSVersion": app.get("minOSVersion", "17.0"),
        })
        if len(out) >= MAX_VERSIONS:
            break
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    config = json.load(open(os.path.join(here, "apps.json"), encoding="utf-8"))
    source = {k: v for k, v in config.items() if k != "apps"}
    source["apps"] = []
    for app in config["apps"]:
        try:
            versions = versions_for(app)
        except Exception as err:  # z. B. Repo privat oder gelöscht
            print(f"WARNUNG: {app['repo']}: {err}", file=sys.stderr)
            versions = []
        if not versions:
            print(f"WARNUNG: {app['name']}: kein brauchbares Release, App fehlt in der Quelle",
                  file=sys.stderr)
            continue
        entry = {k: app[k] for k in APP_FIELDS if k in app}
        entry["versions"] = versions
        source["apps"].append(entry)
        print(f"{app['name']}: {versions[0]['version']} ({versions[0]['size']} Bytes)", file=sys.stderr)
    source["news"] = []
    if not source["apps"]:
        sys.exit("Keine App gefunden, Quelle wird nicht geschrieben.")
    target = sys.argv[1] if len(sys.argv) > 1 else "source.json"
    with open(target, "w", encoding="utf-8") as f:
        json.dump(source, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
