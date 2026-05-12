# asset-management

Tooling for the ODG file-scatter problem. Three layers:

1. **Audit** — `scripts/Audit-ODGFiles.ps1` walks the disk and writes a CSV inventory of asset-shaped files (extensions categorized in the script). Output goes to `data/audits/`.
2. **Intake funnel** — `C:\ODG\_intake\YYYY-MM-DD\` is the single landing zone for new generated/downloaded art. Browser + tool download dirs are pointed here.
3. **Triage** — periodic sorter (`scripts/Sort-ODGIntake.ps1`, future) routes intake files into permanent homes under `repos/tll/assets/`, `repos/dhtw/assets/`, vault, etc.

Build plan: `C:\ODG\ODG-Asset-Management-Plan.md` — phased execution with user decision points between phases. Do not skip the decision points.

## Hard rules

- **Never delete.** Moves go to `C:\ODG\_quarantine\YYYY-MM-DD\`. User empties quarantine manually after a soak period.
- **Audit before action.** Refuse cleanup runs if the audit CSV is more than 7 days old.
- **Respect existing systems.** Do not touch `.git/`, active Godot projects, `_archive/` folders, or files modified in the last 7 days (probable WIP).
- **OneDrive coexistence.** Pause OneDrive sync before bulk moves inside the vault path.
- **Log every move** to `data/cleanup-log-YYYY-MM-DD.csv` or `data/intake-log-YYYY-MM-DD.csv` with original path, new path, timestamp, rule.

## Layout

```
asset-management/
  scripts/   PowerShell scripts (audit, cleanup, sorter)
  data/
    audits/  audit CSVs + triage plans (one per run)
  docs/      routing-rules.md, eagle-setup.md, etc.
```

## Workspace context

This is a tooling repo, not a game. Sits alongside `tll/`, `dhtw/`, `dhtw-tabletop/` in `C:\ODG\repos\`. PowerShell for filesystem walks; Python+pandas for CSV analysis.
