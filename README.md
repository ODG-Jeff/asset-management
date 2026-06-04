# odg-sorter

A Python daemon that watches studio inflow paths (ComfyUI output, `_intake/`)
and routes new generated assets into project-repo canonical homes, writing
Obsidian vault sidecars so the vault becomes the find-layer.

## Install

```bash
pip install -e .[dev]
```

## Run

```bash
odg-sorter daemon       # start the watcher
odg-sorter sort <path>  # one-shot, route a single file
odg-sorter digest       # generate the weekly digest now
odg-sorter reconcile    # walk known paths, route anything missed
```

## At logon

```powershell
.\scripts\install_task_scheduler.ps1
```

## Test

```bash
pytest -v
```

## Design

`docs/superpowers/specs/2026-06-04-asset-management-v1-design.md`

## Implementation plan

`docs/superpowers/plans/2026-06-04-asset-management-v1.md`
