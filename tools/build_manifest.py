"""
Generate tools/manifest.json from the $Zones arrays in build_kmz_packs.ps1
(winter) + build_kmz_packs_summer.ps1 (summer, extra Mittelland zones) and
the KMZ files in out/packs/.

Single source of truth for the static-site tools. Schema:

{
  "release_tag": "...",
  "asset_url_template": "https://github.com/<repo>/releases/download/<tag>/{name}",
  "tile_cap": 500,
  "zones": [
    { "n": 1, "name": "...", "bbox_lv95": [...], "desc": "...",
      "files":            [{name, size_mb}],  # winter detail (backwards-compat)
      "winter_files":     [{name, size_mb}],  # winter detail T1 parts
      "winter_overview":  {name, size_mb} | null,  # NN_<zone>_overview.kmz
      "summer_files":     [{name, size_mb}],  # summer detail T1 parts
      "summer_overview":  {name, size_mb} | null,  # NN_<zone>_summer_overview.kmz
      "total_size_mb":    ...,                # winter (backwards-compat)
      "winter_size_mb":   ...,                # winter detail + overview combined
      "summer_size_mb":   ...,                # summer detail + overview combined
      "total_tiles_est":  ...,
      "seasons": ["winter"] | ["winter","summer"] | ...
    },
    ...
  ]
}

Note: the all-CH `00_overview_ch.kmz` was retired 2026-06-11 in favour of
per-zone multi-tier overview KMZs (T2/T3/T4 bundled). Each zone now ships its
own zoom-pyramid in `<zone>_overview.kmz`.
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


def _file_record(f: Path) -> dict:
    return {"name": f.name, "size_mb": round(f.stat().st_size / 1_048_576, 1)}


def detail_files(prefix: str, season: str = "winter") -> list[dict]:
    """Detail-tier KMZ parts for a zone (T1 only — overview tiers excluded).

    season='winter': matches NN_<name>.kmz or NN_<name>_part_NNN.kmz.
    season='summer': matches NN_<name>_summer.kmz or NN_<name>_summer_part_NNN.kmz.
    Excludes _overview.kmz files (those are the new T2/T3/T4 bundle).
    """
    files = []
    for f in sorted(PACKS.glob(f"{prefix}*.kmz")):
        stem = f.stem
        # Drop trailing _part_NNN to get the "bare" stem for season matching.
        m = re.match(r"(.+?)(_part_\d+)?$", stem)
        bare = m.group(1) if m else stem
        if bare.endswith("_overview"):
            continue
        if season == "winter":
            # _summer is the summer tier; _fenix6 is the 100-tile-cap tier —
            # neither belongs in the standard winter file list.
            if bare.endswith("_summer") or bare.endswith("_fenix6"):
                continue
            files.append(_file_record(f))
        elif season == "summer":
            if not bare.endswith("_summer"):
                continue
            files.append(_file_record(f))
    return files


def overview_file(prefix: str, season: str = "winter") -> dict | None:
    """Return the single overview KMZ for a zone, or None.

    winter: NN_<name>_overview.kmz
    summer: NN_<name>_summer_overview.kmz

    Exact-name match: a winter glob like ``{prefix}*_overview.kmz`` would also
    catch ``_summer_overview.kmz`` (and ``_fenix6_overview.kmz``), which is how
    summer-only zones used to wrongly report a winter overview.
    """
    suffix = "_summer_overview.kmz" if season == "summer" else "_overview.kmz"
    p = PACKS / f"{prefix}{suffix}"
    return _file_record(p) if p.exists() else None


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

    # Zones we still build locally for personal use but don't publish as winter.
    # Their winter KMZs land in out/packs/ but the public manifest only exposes
    # them as summer. See conversation 2026-06-10.
    PRIVATE_WINTER_ZONES = {21}

    url_tmpl = f"https://github.com/{args.repo_slug}/releases/download/{args.release_tag}/{{name}}"

    winter_zones = parse_zones(PS1_WINTER)
    summer_zones = parse_zones(PS1_SUMMER) if PS1_SUMMER.exists() else []
    merged = merge_zones(winter_zones, summer_zones)

    zips_dir = PACKS / "zips"
    def zip_for(name: str) -> dict | None:
        p = zips_dir / name
        if p.exists():
            return {"name": name, "size_mb": round(p.stat().st_size / 1_048_576, 1)}
        return None

    zones_out = []
    for z in merged:
        prefix = f"{z['n']:02d}_{z['name']}"
        winter_files = detail_files(prefix, "winter")
        summer_files = detail_files(prefix, "summer")
        winter_ov    = overview_file(prefix, "winter")
        summer_ov    = overview_file(prefix, "summer")
        if z["n"] in PRIVATE_WINTER_ZONES:
            winter_files = []
            winter_ov    = None
        winter_zip = zip_for(f"{z['n']:02d}_{z['name']}.zip") if winter_files else None
        summer_zip = zip_for(f"{z['n']:02d}_{z['name']}_summer.zip") if summer_files else None
        seasons = []
        if winter_files: seasons.append("winter")
        if summer_files: seasons.append("summer")
        winter_total = sum_mb(winter_files) + (winter_ov["size_mb"] if winter_ov else 0)
        summer_total = sum_mb(summer_files) + (summer_ov["size_mb"] if summer_ov else 0)
        zones_out.append({
            **z,
            "files":            winter_files,                # backwards-compat
            "winter_files":     winter_files,
            "winter_overview":  winter_ov,
            "summer_files":     summer_files,
            "summer_overview":  summer_ov,
            "winter_zip":       winter_zip,
            "summer_zip":       summer_zip,
            "total_size_mb":    round(winter_total, 1),      # backwards-compat
            "winter_size_mb":   round(winter_total, 1),
            "summer_size_mb":   round(summer_total, 1),
            "total_tiles_est":  estimate_tiles(z),
            "seasons": seasons,
        })

    manifest = {
        "release_tag": args.release_tag,
        "asset_url_template": url_tmpl,
        "tile_cap": 500,
        "zones": zones_out,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2))

    winter_n = sum(1 for z in zones_out if "winter" in z["seasons"])
    summer_n = sum(1 for z in zones_out if "summer" in z["seasons"])
    winter_ov_n = sum(1 for z in zones_out if z["winter_overview"])
    summer_ov_n = sum(1 for z in zones_out if z["summer_overview"])
    detail_parts = (sum(len(z["winter_files"]) for z in zones_out)
                  + sum(len(z["summer_files"]) for z in zones_out))
    total_files = detail_parts + winter_ov_n + summer_ov_n
    print(f"wrote {out}")
    print(f"  zones: {len(zones_out)} total / winter={winter_n} / summer={summer_n}")
    print(f"  files: {total_files} ({sum(len(z['winter_files']) for z in zones_out)} winter detail parts, "
          f"{sum(len(z['summer_files']) for z in zones_out)} summer detail parts, "
          f"{winter_ov_n} winter overview, {summer_ov_n} summer overview)")


if __name__ == "__main__":
    main()
