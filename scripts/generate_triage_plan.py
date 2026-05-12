#!/usr/bin/env -S uv run --with pandas python
"""Phase 2 — Triage plan generator.

Reads the latest audit CSV and produces a triage plan with four sections:
  A: Top 20 dupe groups by wasted space, with a recommended canonical
  B: Likely-scratch breakdown by location, with a 20-path sample
  C: Orphans in scatter zones (Desktop/Downloads/Documents, age > 30 days)
  D: Suggested permanent homes per (Category x Location)

The plan is an advisory document — it does not move or delete anything.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

# Routing rules from Phase 5 of ODG-Asset-Management-Plan.md
TLL_TOKENS = ("tll", "probe", "civ", "witness", "triton")
DHTW_TOKENS = ("dhtw", "wall", "bailout", "impede", "assist", "sled", "arlo")
BRAND_TOKENS = ("opal", "dragonfly", "logo", "brand")

# Canonical-priority order for dupe recommendations.
# Lower number = higher priority to keep.
CANONICAL_PRIORITY = {
    "ODG_Vault": 1,
    "Repo_TLL": 2,
    "Repo_DHTW": 2,
    "Repo_Other": 3,
    "ODG_Other": 4,
    "Documents": 5,
    "OneDrive_Other": 6,
    "Other": 7,
    "Downloads": 8,
    "Desktop": 9,
}

# Category to sub-folder within an assets/ tree
CATEGORY_SUBFOLDER = {
    "2D_Raster": "2d/raster",
    "2D_Vector": "2d/vector",
    "2D_Layered": "2d/layered",
    "3D_Model": "3d",
    "3D_Texture": "3d/textures",
    "Audio": "audio",
    "Video": "video",
    "Document": "docs",
    "Archive": "archives",
    "Game_Project": "(in-tree code — leave alone)",
}


def project_hint(filename: str) -> str | None:
    """Return 'tll' | 'dhtw' | 'brand' | None based on filename tokens."""
    lower = filename.lower()
    if any(tok in lower for tok in BRAND_TOKENS):
        return "brand"
    if any(tok in lower for tok in TLL_TOKENS):
        return "tll"
    if any(tok in lower for tok in DHTW_TOKENS):
        return "dhtw"
    return None


PROTECTED_MARKERS = ("_protected_originals", "PROTECTED", "DO_NOT_OVERWRITE", "DO-NOT-OVERWRITE", "DO_NOT_DELETE")


def is_protected(path: str) -> bool:
    """Files the user has explicitly marked untouchable — never mark for removal."""
    return any(m in path for m in PROTECTED_MARKERS)


def pick_canonical(group: pd.DataFrame) -> pd.Series:
    """From a group of duplicate rows, pick the one to keep as the source-of-truth.

    Protected files (under _protected_originals/, PROTECTED, DO_NOT_OVERWRITE)
    are kept regardless — but that's handled at the marker layer. Here we pick
    the *working* canonical: location priority, then shortest path. Protected
    files are excluded from the canonical pool because they're backups, not the
    canonical working copy.
    """
    g = group.copy()
    # Exclude protected files from canonical candidacy — they're backups, not working canonicals.
    g["_protected"] = g["FullPath"].apply(is_protected)
    candidates = g[~g["_protected"]] if (~g["_protected"]).any() else g
    candidates = candidates.copy()
    candidates["_prio"] = candidates["Location"].map(CANONICAL_PRIORITY).fillna(99)
    candidates["_plen"] = candidates["FullPath"].str.len()
    candidates = candidates.sort_values(["_prio", "_plen"])
    return candidates.iloc[0]


def fmt_mb(x: float) -> str:
    return f"{x:.1f} MB" if x < 1024 else f"{x/1024:.2f} GB"


def main(csv_path: Path, out_md: Path) -> None:
    df = pd.read_csv(csv_path)
    df["SizeMB"] = pd.to_numeric(df["SizeMB"], errors="coerce")
    df["DuplicateCount"] = pd.to_numeric(df["DuplicateCount"], errors="coerce").fillna(1).astype(int)
    df["AgeDays"] = pd.to_numeric(df["AgeDays"], errors="coerce")
    df["LikelyScratch"] = df["LikelyScratch"].astype(str).str.upper() == "TRUE"

    out: list[str] = []
    w = out.append

    w(f"# ODG Triage Plan — {csv_path.stem}\n")
    w("**Status:** Draft. Mark each section's actions with ✅ keep / ❌ skip / ✏️ amend before Phase 3.\n")
    w("**Source CSV:** " + str(csv_path) + "\n")
    w(f"**Totals:** {len(df):,} files, {df['SizeMB'].sum()/1024:.2f} GB\n")
    w("")
    w("---\n")

    # ─────────────────────────────────────────────────────────────
    # Section A — Duplicates
    # ─────────────────────────────────────────────────────────────
    w("## Section A — Duplicates\n")

    dupes = df[df["DuplicateCount"] > 1].copy()
    waste_per_grp = dupes.groupby("SHA256").apply(lambda g: g["SizeMB"].iloc[0] * (len(g) - 1), include_groups=False)
    total_waste = waste_per_grp.sum()

    w(f"- **Dupe groups:** {dupes['SHA256'].nunique():,}")
    w(f"- **Dupe files:** {len(dupes):,}")
    w(f"- **Wasted space:** {fmt_mb(total_waste)}")
    w("")
    w("### Top 20 dupe groups by wasted space\n")
    w("For each group: the recommended canonical copy is marked **✓ KEEP** (priority order: ODG_Vault > repo > ODG_Other > Documents > Other > Downloads > Desktop, then shortest path within that bucket). All other copies marked **✗ remove** are candidates for quarantine in Phase 3.\n")

    top_groups = waste_per_grp.sort_values(ascending=False).head(20)
    for i, (sha, waste) in enumerate(top_groups.items(), 1):
        grp = dupes[dupes["SHA256"] == sha].copy()
        canonical = pick_canonical(grp)
        each = grp["SizeMB"].iloc[0]
        w(f"\n#### A-{i:02d}  `{grp['FileName'].iloc[0]}`")
        w(f"- **Waste:** {fmt_mb(waste)}  ({len(grp)} copies × {each:.1f} MB)")
        w(f"- **SHA256:** `{sha[:16]}...`")
        for _, row in grp.iterrows():
            if is_protected(row["FullPath"]):
                marker = "🔒 **PROTECTED — KEEP**"
            elif row["FullPath"] == canonical["FullPath"]:
                marker = "**✓ KEEP**"
            else:
                marker = "✗ remove"
            w(f"  - {marker} — `{row['FullPath']}`  ({row['Location']})")

    w("\n---\n")

    # ─────────────────────────────────────────────────────────────
    # Section B — Likely scratch
    # ─────────────────────────────────────────────────────────────
    w("## Section B — Likely scratch\n")

    scratch = df[df["LikelyScratch"]]
    w(f"- **Total:** {len(scratch):,} files, {fmt_mb(scratch['SizeMB'].sum())}")
    w("")
    w("### By Location\n")
    sloc = scratch.groupby("Location").agg(count=("FullPath", "size"), size_mb=("SizeMB", "sum")).sort_values("count", ascending=False)
    w("```")
    w(sloc.round(2).to_string())
    w("```")
    w("")
    w("### Sample paths (up to 20, newest first)\n")
    for _, row in scratch.sort_values("Modified", ascending=False).head(20).iterrows():
        w(f"- `{row['FullPath']}`  ({row['SizeMB']:.1f} MB, age {row['AgeDays']:.0f}d)")
    if scratch.empty:
        w("_(no LikelyScratch matches — heuristic regex is conservative; see Section D for orphans / Section A for dupes)_")
    w("\n---\n")

    # ─────────────────────────────────────────────────────────────
    # Section C — Orphans in scatter zones
    # ─────────────────────────────────────────────────────────────
    w("## Section C — Orphans in scatter zones\n")
    w("Asset files in `Desktop`, `Downloads`, or `Documents` older than 30 days. The ODG-named subset is highest-signal: those probably want a real home.\n")

    orphans = df[df["Location"].isin(["Desktop", "Downloads", "Documents"]) & (df["AgeDays"] > 30)].copy()
    w(f"- **Total orphans:** {len(orphans):,} files, {fmt_mb(orphans['SizeMB'].sum())}\n")

    w("### By Location × Category\n")
    by_lc = orphans.groupby(["Location", "Category"]).agg(count=("FullPath", "size"), size_mb=("SizeMB", "sum")).sort_values("size_mb", ascending=False)
    if not by_lc.empty:
        w("```")
        w(by_lc.round(1).to_string())
        w("```")
    w("")

    odg_re = re.compile("|".join(TLL_TOKENS + DHTW_TOKENS + BRAND_TOKENS), re.IGNORECASE)
    mask = orphans["FileName"].apply(lambda n: bool(odg_re.search(str(n))))
    odg_orphans = orphans[mask].sort_values("SizeMB", ascending=False)
    w(f"### ODG-named orphans ({len(odg_orphans)} files, {fmt_mb(odg_orphans['SizeMB'].sum())})\n")
    if odg_orphans.empty:
        w("_None._")
    else:
        for _, row in odg_orphans.iterrows():
            hint = project_hint(row["FileName"]) or "?"
            w(f"- `{row['FullPath']}`  ({row['SizeMB']:.1f} MB, age {row['AgeDays']:.0f}d) → hint: **{hint}**")

    w("")
    w("### Non-ODG-named orphans — summary by Category (no per-file listing)\n")
    nonodg = orphans[~mask]
    by_cat = nonodg.groupby("Category").agg(count=("FullPath", "size"), size_mb=("SizeMB", "sum")).sort_values("size_mb", ascending=False)
    if not by_cat.empty:
        w("```")
        w(by_cat.round(1).to_string())
        w("```")
        w("_Suggested treatment: leave them — they're personal/unrelated content. Phase 3 protect-list should include these paths if they're not project work._")
    w("\n---\n")

    # ─────────────────────────────────────────────────────────────
    # Section D — Suggested permanent homes
    # ─────────────────────────────────────────────────────────────
    w("## Section D — Suggested permanent homes per (Category × Location)\n")
    w("Populated cells only (count > 0). \"Home\" is what the Phase 5 sorter should propose for new files matching this combo. The Phase 3 one-shot cleanup may also use these as proposed destinations for existing files outside their expected home.\n")
    w("")
    w("| Category | Location | Count | Size | Suggested home | Notes |")
    w("|---|---|--:|--:|---|---|")

    combos = df.groupby(["Category", "Location"]).agg(count=("FullPath", "size"), size_mb=("SizeMB", "sum")).sort_values("size_mb", ascending=False)

    for (cat, loc), row in combos.iterrows():
        sub = CATEGORY_SUBFOLDER.get(cat, cat.lower())
        # Default home depends on location + category
        if loc in ("Repo_TLL", "Repo_DHTW", "Repo_Other"):
            home = "(stays in repo)"
            note = "Already in a project repo. Section A may still recommend dedupe."
        elif loc == "ODG_Vault":
            home = "(stays in vault)"
            note = "Already in canonical knowledge base."
        elif loc == "Downloads":
            if cat in ("3D_Model", "2D_Raster", "2D_Vector", "2D_Layered", "3D_Texture"):
                home = f"`_intake/_unsorted/` (route per filename: tll → repos/tll/assets/{sub}, dhtw → repos/dhtw/assets/{sub})"
            else:
                home = "`_intake/_unsorted/` (manual review)"
            note = "Downloads is browser scratch; move only ODG-named files."
        elif loc == "Desktop":
            home = "`_intake/_unsorted/`"
            note = "Desktop should hold zero assets long-term."
        elif loc == "Documents":
            home = "(leave alone unless ODG-named)"
            note = "Documents is general personal use; respect non-ODG content."
        elif loc == "ODG_Other":
            home = "(case-by-case — Section A dupes first, then move into repo/vault)"
            note = "Biggest bucket: 7.8 GB of zips + 2.7 GB of 2D rasters. Probably contains LoRA datasets and generated/_backups/."
        elif loc == "Other":
            home = "(skip — mostly C:\\tmp and Pictures\\Screenshots)"
            note = "Outside ODG scope; tighten audit excludes further if noise."
        elif loc == "OneDrive_Other":
            home = "Vault or repo, depending on content"
            note = "Single file — verify what it is."
        else:
            home = "?"
            note = "?"
        w(f"| {cat} | {loc} | {int(row['count']):,} | {fmt_mb(row['size_mb'])} | {home} | {note} |")

    w("\n---\n")

    # ─────────────────────────────────────────────────────────────
    # Decision-point summary
    # ─────────────────────────────────────────────────────────────
    w("## Decision Point — what to authorize before Phase 3\n")
    w("Per the build plan, Phase 3 only runs after you mark which actions to actually take. Common shapes:\n")
    w("")
    w("- ✅ **Section A** (top dupe groups): authorize quarantine of all ✗ marked paths, keeping the ✓ KEEP one. Estimated recovery: ~" + fmt_mb(total_waste) + ".")
    w("- ✅/❌ **Section B** (scratch): authorize quarantine of all LikelyScratch files (small impact: ~" + fmt_mb(scratch['SizeMB'].sum()) + ").")
    w("- ✅/❌ **Section C** (orphans): authorize moves only for ODG-named orphans into `_intake/`; leave non-ODG personal content alone.")
    w("- 📋 **Section D** (routing matrix): use as the rulebook for the Phase 5 intake sorter — no actions needed in Phase 3.")
    w("")
    w("Write your decisions into `data/audits/triage-decisions-" + csv_path.stem.split("-", 2)[-1] + ".json` (Phase 3 consumes that file).")

    out_md.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {out_md} ({len('\\n'.join(out))} chars)")


if __name__ == "__main__":
    csv = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\ODG\repos\asset-management\data\audits\ODG-Audit-2026-05-11.csv")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else csv.with_name(f"triage-plan-{csv.stem.split('-', 2)[-1]}.md")
    main(csv, out)
