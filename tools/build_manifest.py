"""
Generate tools/manifest.json from the $Zones arrays in build_kmz_packs.ps1
(winter) + build_kmz_packs_summer.ps1 (summer, extra Mittelland zones) and
the KMZ files in out/packs/.

Single source of truth for the static-site tools. Schema:

{
  "release_tag": "...",
  "asset_url_template": "https://github.com/<repo>/releases/download/<tag>/{name}",
  "tile_cap": 500,
  "overview_tiles_est": 89,
  "overview": {
    "name": "overview_ch",
    "files":         [{name, size_mb}],     # winter overview (backwards-compat)
    "winter_files":  [{name, size_mb}],
    "summer_files":  [{name, size_mb}],     # may be []
    "total_size_mb": ...                    # winter total
  },
  "zones": [
    { "n": 1, "name": "...", "bbox_lv95": [...], "desc": "...",
      "files":          [{name, size_mb}],   # winter (backwards-compat)
      "winter_files":   [{name, size_mb}],
      "summer_files":   [{name, size_mb}],   # may be []
      "total_size_mb":  ...,                 # winter
      "winter_size_mb": ...,
      "summer_size_mb": ...,
      "total_tiles_est":...,
      "seasons": ["winter"] | ["winter","summer"]  # what's actually shipped
    },
    ...
  ]
}
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO  = Path(__file__).resolve().parent.parent
PACKS = REPO / "out" / "packs"
PS1_WINTER = REPO / "build_kmz_packs.ps1"
PS1_SUMMER = REPO / "build_kmz_packs_summer.ps1"


ROW_RE = re.compile(
    r"@\{\s*N\s*=\s*(?P<n>\d+)\s*;\s*"
    r"Name\s*=\s*\"(?P<name>[^\"]+)\"\s*;\s*"
    r"Bbox\s*=\s*\"(?P<bbox>[^\"]+)\"\s*;\s*"
    r"Desc\s*=\s*\"(?P<desc>[^\"]+)\"\s*\}",
    re.DOTALL,
)


def parse_zones(ps1: Path) -> list[dict]:
    text = ps1.read_text(encoding="utf-8")
    zones = []
    for m in ROW_RE.finditer(text):
        zones.append({
            "n": int(m.group("n")),
            "name": m.group("name"),
            "bbox_lv95": [int(x) for x in m.group("bbox").split(",")],
            "desc": m.group("desc"),
        })
    if not zones:
        raise SystemExit(f"could not parse $Zones from {ps1}")
    return zones


def merge_zones(winter: list[dict], summer: list[dict]) -> list[dict]:
    """Winter is the canonical bbox source; summer adds the Mittelland extras.

    Where the same N appears in both, prefer winter's bbox/desc (the user has
    been running the winter build for months; bboxes are tuned). Summer's
    extras (N=22+) are appended.
    """
    by_n = {z["n"]: z for z in winter}
    for z in summer:
        if z["n"] not in by_n:
            by_n[z["n"]] = z
    return sorted(by_n.values(), key=lambda z: z["n"])


def kmz_files_for(prefix: str, suffix: str = "") -> list[dict]:
    """Match `<prefix><anything><suffix>.kmz`. Empty suffix matches winter
    naming (NN_<name>.kmz or NN_<name>_part_NNN.kmz). suffix=_summer matches
    NN_<name>_summer.kmz / NN_<name>_summer_part_NNN.kmz.
    """
    files = []
    for f in sorted(PACKS.glob(f"{prefix}*.kmz")):
        # Filter on the _summer suffix being present (or absent) before .kmz
        # or before _part_NNN.kmz.
        stem = f.stem
        m = re.match(r".+?(_part_\d+)?$", stem)
        bare = stem[:-len(m.group(1))] if m and m.group(1) else stem
        if suffix and not bare.endswith(suffix):
            continue
        if not suffix and bare.endswith("_summer"):
            continue
        files.append({"name": f.name, "size_mb": round(f.stat().st_size / 1_048_576, 1)})
    return files


def estimate_tiles(zone: dict) -> int:
    """Rough estimate from bbox: ~10 kept tiles per 10×10 km cell at 2.5 m/px."""
    e0, n0, e1, n1 = zone["bbox_lv95"]
    cells = ((e1 - e0) / 10000) * ((n1 - n0) / 10000)
    return round(cells * 10)


def sum_mb(files: list[dict]) -> float:
    return round(sum(f["size_mb"] for f in files), 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--release-tag", default="v1",
                    help="GitHub Release tag where KMZs are hosted")
    ap.add_argument("--repo-slug", default="JoepVdE/garminswisstopo-public",
                    help="GitHub <user>/<repo> for the download URL")
    ap.add_argument("--out", default=str(REPO / "tools" / "manifest.json"))
    args = ap.parse_args()

    url_tmpl = f"https://github.com/{args.repo_slug}/releases/download/{args.release_tag}/{{name}}"

    winter_zones = parse_zones(PS1_WINTER)
    summer_zones = parse_zones(PS1_SUMMER) if PS1_SUMMER.exists() else []
    merged = merge_zones(winter_zones, summer_zones)

    zones_out = []
    for z in merged:
        prefix = f"{z['n']:02d}_{z['name']}"
        winter_files = kmz_files_for(prefix)
        summer_files = kmz_files_for(prefix, suffix="_summer")
        seasons = []
        if winter_files: seasons.append("winter")
        if summer_files: seasons.append("summer")
        zones_out.append({
            **z,
            "files":          winter_files,                  # backwards-compat
            "winter_files":   winter_files,
            "summer_files":   summer_files,
            "total_size_mb":  sum_mb(winter_files),          # backwards-compat
            "winter_size_mb": sum_mb(winter_files),
            "summer_size_mb": sum_mb(summer_files),
            "total_tiles_est": estimate_tiles(z),
            "seasons": seasons,
        })

    overview_winter = kmz_files_for("00_overview_ch")
    overview_summer = kmz_files_for("00_overview_ch", suffix="_summer")

    manifest = {
        "release_tag": args.release_tag,
        "asset_url_template": url_tmpl,
        "tile_cap": 500,
        "overview_tiles_est": 89,
        "overview": {
            "name": "overview_ch",
            "desc": "All of Switzerland @ 25 m/px. Always-on background.",
            "files":         overview_winter,
            "winter_files":  overview_winter,
            "summer_files":  overview_summer,
            "total_size_mb": sum_mb(overview_winter),
        },
        "zones": zones_out,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2))

    winter_n = sum(1 for z in zones_out if "winter" in z["seasons"])
    summer_n = sum(1 for z in zones_out if "summer" in z["seasons"])
    total_files = (sum(len(z["winter_files"]) + len(z["summer_files"]) for z in zones_out)
                   + len(overview_winter) + len(overview_summer))
    print(f"wrote {out}")
    print(f"  zones: {len(zones_out)} total / winter={winter_n} / summer={summer_n}")
    print(f"  files: {total_files} ({sum(len(z['winter_files']) for z in zones_out)} winter zone parts, "
          f"{sum(len(z['summer_files']) for z in zones_out)} summer zone parts, "
          f"{len(overview_winter)} winter overview, {len(overview_summer)} summer overview)")


if __name__ == "__main__":
    main()
