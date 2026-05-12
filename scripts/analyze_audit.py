#!/usr/bin/env -S uv run --with pandas python
"""Phase 1 audit headline-number generator.

Reads the audit CSV and prints (and writes) the summary numbers needed for the
Phase 1 Decision Point: top extensions, dupe concentration, scratch breakdown,
hot spots.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


def main(csv_path: Path, out_md: Path) -> None:
    df = pd.read_csv(csv_path)
    df["SizeMB"] = pd.to_numeric(df["SizeMB"], errors="coerce")
    df["DuplicateCount"] = pd.to_numeric(df["DuplicateCount"], errors="coerce").fillna(1).astype(int)
    df["AgeDays"] = pd.to_numeric(df["AgeDays"], errors="coerce")

    out: list[str] = []
    w = out.append

    total_gb = df["SizeMB"].sum() / 1024
    w(f"# ODG Asset Audit — Headline Summary ({csv_path.stem})\n")
    w(f"- **Rows:** {len(df):,}")
    w(f"- **Total size:** {total_gb:.2f} GB")
    w("")

    w("## By Location (count, MB)")
    loc = df.groupby("Location").agg(count=("FullPath", "size"), size_mb=("SizeMB", "sum")).sort_values("count", ascending=False)
    w("```")
    w(loc.round(1).to_string())
    w("```")
    w("")

    w("## By Category (count, MB)")
    cat = df.groupby("Category").agg(count=("FullPath", "size"), size_mb=("SizeMB", "sum")).sort_values("count", ascending=False)
    w("```")
    w(cat.round(1).to_string())
    w("```")
    w("")

    w("## Top 10 extensions by count")
    by_ext_count = df.groupby("Extension").agg(count=("FullPath", "size"), size_mb=("SizeMB", "sum")).sort_values("count", ascending=False).head(10)
    w("```")
    w(by_ext_count.round(1).to_string())
    w("```")
    w("")

    w("## Top 10 extensions by size")
    by_ext_size = df.groupby("Extension").agg(count=("FullPath", "size"), size_mb=("SizeMB", "sum")).sort_values("size_mb", ascending=False).head(10)
    w("```")
    w(by_ext_size.round(1).to_string())
    w("```")
    w("")

    w("## Duplicates (SHA256 exact)")
    dupes = df[df["DuplicateCount"] > 1].copy()
    n_files = len(dupes)
    n_groups = dupes["SHA256"].nunique()
    waste_per_group = dupes.groupby("SHA256").apply(lambda g: g["SizeMB"].iloc[0] * (len(g) - 1), include_groups=False)
    total_waste_mb = waste_per_group.sum()
    w(f"- **Files in dupe groups:** {n_files:,}")
    w(f"- **Unique groups:** {n_groups:,}")
    w(f"- **Wasted space:** {total_waste_mb:.1f} MB ({total_waste_mb/1024:.2f} GB)")
    w("")

    w("### Dupe files by Location")
    w("```")
    w(dupes.groupby("Location").size().sort_values(ascending=False).to_string())
    w("```")
    w("")

    w("### Dupe wasted space by Location (MB)")
    def loc_waste(g: pd.DataFrame) -> pd.Series:
        return pd.Series({"loc": g["Location"].iloc[0], "waste": g["SizeMB"].iloc[0] * (len(g) - 1)})
    per_grp = dupes.groupby("SHA256").apply(loc_waste, include_groups=False)
    loc_waste_summary = per_grp.groupby("loc")["waste"].sum().sort_values(ascending=False).round(1)
    w("```")
    w(loc_waste_summary.to_string())
    w("```")
    w("")

    w("### Top 10 dupe groups by wasted space")
    top_waste = waste_per_group.sort_values(ascending=False).head(10)
    for sha, waste in top_waste.items():
        grp = dupes[dupes["SHA256"] == sha]
        each_mb = grp["SizeMB"].iloc[0]
        w(f"- **{waste:.1f} MB wasted** — {len(grp)} copies × {each_mb:.1f} MB — `{grp['FileName'].iloc[0]}`")
        for p in grp["FullPath"].head(6):
            w(f"  - `{p}`")
        if len(grp) > 6:
            w(f"  - ...and {len(grp)-6} more")
    w("")

    w("## Likely scratch (count, MB)")
    scratch = df[df["LikelyScratch"].astype(str).str.upper() == "TRUE"]
    w(f"- **Total:** {len(scratch):,} files, {scratch['SizeMB'].sum():.1f} MB")
    w("")
    w("```")
    w(scratch.groupby("Location").size().sort_values(ascending=False).to_string())
    w("```")
    w("")

    w("## Hot spots — top 15 Category x Location combos by size")
    hot = df.groupby(["Category", "Location"]).agg(count=("FullPath", "size"), size_mb=("SizeMB", "sum")).sort_values("size_mb", ascending=False).head(15)
    w("```")
    w(hot.round(1).to_string())
    w("```")
    w("")

    w("## Orphans in scatter zones (Desktop / Downloads / Documents, age > 30 days)")
    orphans = df[df["Location"].isin(["Desktop", "Downloads", "Documents"]) & (df["AgeDays"] > 30)]
    w(f"- **Total:** {len(orphans):,} files, {orphans['SizeMB'].sum():.1f} MB")
    w("")
    w("By location × category:")
    if len(orphans):
        w("```")
        w(orphans.groupby(["Location", "Category"]).agg(count=("FullPath", "size"), size_mb=("SizeMB", "sum")).round(1).to_string())
        w("```")
    w("")

    w("### ODG-named orphans (filename hints at project work)")
    mask = orphans["FileName"].str.contains("tll|dhtw|probe|wall|opal|dragonfly|bailout|impede|civ|witness|triton", case=False, na=False)
    odg = orphans[mask]
    w(f"- **Count:** {len(odg):,}, {odg['SizeMB'].sum():.1f} MB")
    if len(odg):
        w("")
        w("Sample (first 20):")
        w("```")
        w(odg[["FullPath", "SizeMB", "AgeDays"]].head(20).to_string(index=False))
        w("```")

    text = "\n".join(out) + "\n"
    out_md.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    csv = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\ODG\repos\asset-management\data\audits\ODG-Audit-2026-05-11.csv")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else csv.with_name(f"audit-summary-{csv.stem.split('-',2)[-1]}.md")
    main(csv, out)
