# ODG Triage Plan — ODG-Audit-2026-05-11

**Status:** Draft. Mark each section's actions with ✅ keep / ❌ skip / ✏️ amend before Phase 3.

**Source CSV:** C:\ODG\repos\asset-management\data\audits\ODG-Audit-2026-05-11.csv

**Totals:** 5,188 files, 12.78 GB


---

## Section A — Duplicates

- **Dupe groups:** 491
- **Dupe files:** 1,437
- **Wasted space:** 906.0 MB

### Top 20 dupe groups by wasted space

For each group: the recommended canonical copy is marked **✓ KEEP** (priority order: ODG_Vault > repo > ODG_Other > Documents > Other > Downloads > Desktop, then shortest path within that bucket). All other copies marked **✗ remove** are candidates for quarantine in Phase 3.


#### A-01  `rocket sled 3d model.glb`
- **Waste:** 108.7 MB  (3 copies × 54.3 MB)
- **SHA256:** `720B86C1BBBF47DC...`
  - ✗ remove — `C:\Dev\rocket sled 3d model.glb`  (Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\rocket sled 3d model.glb`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\repos\dhtw\client\assets\3d\sleds\rocket_sled.glb`  (Repo_DHTW)

#### A-02  `DHTW_TGC_Upload_v20_1_5.zip`
- **Waste:** 41.5 MB  (3 copies × 20.7 MB)
- **SHA256:** `42C172E71DCF5DE0...`
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_v20_1_5.zip`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_v21_FINAL.zip`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\zips\DHTW_TGC_Upload_FINAL.zip`  (ODG_Other)

#### A-03  `console_smoke_v1.glb`
- **Waste:** 32.2 MB  (3 copies × 16.1 MB)
- **SHA256:** `E69A29AE444926FD...`
  - ✗ remove — `C:\ODG\generated\tll\hub\console_smoke_v1.glb`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\repos\tll\client\console_smoke_v1.glb`  (Repo_TLL)
  - ✗ remove — `C:\ODG\repos\tll\client\assets\3d\hub\console_smoke_v1.glb`  (Repo_TLL)

#### A-04  `DHTW_TGC_Upload_v13_1.zip`
- **Waste:** 26.1 MB  (2 copies × 26.1 MB)
- **SHA256:** `C3D4EE7D36B0DE70...`
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_v13_1.zip`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_v13.zip`  (ODG_Other)

#### A-05  `Meshy_AI_Emerald_Rocket_Sled_wings_removed_1.blend`
- **Waste:** 23.6 MB  (3 copies × 11.8 MB)
- **SHA256:** `CD38A87225A9DF93...`
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\blender-iterations\Meshy_AI_Emerald_Rocket_Sled_wings_removed_1.blend`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\blender-iterations\Meshy_AI_Emerald_Rocket_Sled_wings_removed_2.blend`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\blender-iterations\Meshy_AI_Emerald_Rocket_Sled_wings_removed.blend`  (ODG_Other)

#### A-06  `DHTW_TGC_Upload_20.zip`
- **Waste:** 21.3 MB  (3 copies × 10.6 MB)
- **SHA256:** `9BC8723288F6D3CA...`
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_20.zip`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_21.zip`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_Final.zip`  (ODG_Other)

#### A-07  `DHTW_TGC_Upload_v20_1.zip`
- **Waste:** 21.3 MB  (2 copies × 21.3 MB)
- **SHA256:** `88DBADCAA1DA1FF3...`
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_v20_1.zip`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_v20.zip`  (ODG_Other)

#### A-08  `ODG_logo_animated.mp4`
- **Waste:** 15.2 MB  (3 copies × 7.6 MB)
- **SHA256:** `41F2B04909FE8167...`
  - ✗ remove — `C:\Downloads\alogo\ODG_logo_animated.mp4`  (Downloads)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\ODG_Animated_Logo.mp4`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\repos\opaldragonfly\html\images\odg_logo_animated.mp4`  (Repo_Other)

#### A-09  `sled_mono_sleek_2.jpg`
- **Waste:** 15.1 MB  (7 copies × 2.5 MB)
- **SHA256:** `9D6DD951FACCDC47...`
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_2.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_blue_2.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_green_2.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_orange_2.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_purple_2.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_red_2.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_yellow_2.jpg`  (ODG_Other)

#### A-10  `sled_mono_sleek_blue.glb`
- **Waste:** 14.2 MB  (2 copies × 14.2 MB)
- **SHA256:** `87D677E809E9428B...`
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_blue.glb`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek.glb`  (ODG_Other)

#### A-11  `DHTW_TGC_Upload_34.zip`
- **Waste:** 13.4 MB  (2 copies × 13.4 MB)
- **SHA256:** `F843DD6C5B73EE70...`
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_34.zip`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_35.zip`  (ODG_Other)

#### A-12  `DHTW_Travel_TGC_Upload_v6_1.zip`
- **Waste:** 12.2 MB  (2 copies × 12.2 MB)
- **SHA256:** `9247B2D4EDF0BF56...`
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_Travel_TGC_Upload_v6_1.zip`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_Travel_TGC_Upload_v6.zip`  (ODG_Other)

#### A-13  `DHTW_TGC_Upload_31.zip`
- **Waste:** 11.9 MB  (2 copies × 11.9 MB)
- **SHA256:** `44BB56E6275F8D8E...`
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_31.zip`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_32.zip`  (ODG_Other)

#### A-14  `DHTW_TGC_Upload_24.zip`
- **Waste:** 11.9 MB  (2 copies × 11.9 MB)
- **SHA256:** `7987638E8F3E2607...`
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_24.zip`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_25.zip`  (ODG_Other)

#### A-15  `odg_logo_gold_t.png`
- **Waste:** 11.6 MB  (13 copies × 1.0 MB)
- **SHA256:** `4ACBF038D6B8D848...`
  - ✗ remove — `C:\Downloads\odg_logo_gold_t.png`  (Downloads)
  - ✗ remove — `C:\ODG\assets\logos\final\odg_logo_gold_t.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\brand\logo-experiments\odg_logo_gold_t.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\opaldragonfly\website-backups\backup_v2\odg_logo_gold_t.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\opaldragonfly\website-backups\backup_v3\images\odg_logo_gold_t.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\repos-old\opaldragonfly-snapshot\html\odg_logo_gold_t.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\repos-old\opaldragonfly-snapshot\html\backup_v2\odg_logo_gold_t.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\repos-old\opaldragonfly-snapshot\html\backup_v3\images\odg_logo_gold_t.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\repos-old\opaldragonfly-snapshot\html\images\odg_logo_gold_t.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Projects\dhtw-tabletop\source-art\logos\odg_logo_gold_t.png`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\repos\opaldragonfly\html\odg_logo_gold_t.png`  (Repo_Other)
  - ✗ remove — `C:\ODG\repos\opaldragonfly\html\images\odg_logo_gold_t.png`  (Repo_Other)
  - ✗ remove — `C:\ODG\repos\opaldragonfly\html\xenoreliquary\odg-logo.png`  (Repo_Other)

#### A-16  `sled_mono_sleek_1.jpg`
- **Waste:** 11.6 MB  (7 copies × 1.9 MB)
- **SHA256:** `52AD9496E8324201...`
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_1.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_blue_1.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_green_1.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_orange_1.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_purple_1.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_red_1.jpg`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw\3d-sleds-unused\sled_mono_sleek_yellow_1.jpg`  (ODG_Other)

#### A-17  `DHTW_TGC_Upload_12.zip`
- **Waste:** 10.7 MB  (2 copies × 10.7 MB)
- **SHA256:** `F5906980D5741AC9...`
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_12.zip`  (ODG_Other)
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\dhtw-tabletop\tgc-upload-iterations\DHTW_TGC_Upload_13.zip`  (ODG_Other)

#### A-18  `hull.png`
- **Waste:** 8.1 MB  (9 copies × 1.0 MB)
- **SHA256:** `8A9341E8987755E7...`
  - ✗ remove — `C:\ODG\generated\dhtw\regression\golden\foundation_v1\ronin\hull.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\generated\dhtw\sleds\audit_1778421459\ronin\current_hull.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\generated\dhtw\sleds\audit_1778421459\ronin\new_hull.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\generated\dhtw\sleds\premium_v9\ronin.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\generated\dhtw\sleds\_backups\pre_mythic_v3_20260511_113548\2d\ronin.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\generated\dhtw\sleds\_backups\pre_mythic_v3_20260511_113548\premium_v9\ronin.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\generated\dhtw\sleds\_backups\pre_mythic_v3_20260511_113548\ui\ronin.png`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\repos\dhtw\client\assets\2d\sleds\premium\ronin.png`  (Repo_DHTW)
  - ✗ remove — `C:\ODG\repos\dhtw\client\assets\ui\sleds\premium\ronin.png`  (Repo_DHTW)

#### A-19  `wraith_eternal.png`
- **Waste:** 8.0 MB  (7 copies × 1.3 MB)
- **SHA256:** `E6A807153501C38E...`
  - ✗ remove — `C:\ODG\generated\dhtw\sleds\premium_v9\wraith_eternal.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\generated\dhtw\sleds\_backups\pre_mythic_v3_20260511_113548\2d\wraith_eternal.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\generated\dhtw\sleds\_backups\pre_mythic_v3_20260511_113548\premium_v9\wraith_eternal.png`  (ODG_Other)
  - ✗ remove — `C:\ODG\generated\dhtw\sleds\_backups\pre_mythic_v3_20260511_113548\ui\wraith_eternal.png`  (ODG_Other)
  - 🔒 **PROTECTED — KEEP** — `C:\ODG\generated\dhtw\sleds\_protected_originals\wraith_eternal_PERFECT_DO_NOT_OVERWRITE.png`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\repos\dhtw\client\assets\2d\sleds\premium\wraith_eternal.png`  (Repo_DHTW)
  - ✗ remove — `C:\ODG\repos\dhtw\client\assets\ui\sleds\premium\wraith_eternal.png`  (Repo_DHTW)

#### A-20  `odg_logo_t.zip`
- **Waste:** 6.7 MB  (2 copies × 6.7 MB)
- **SHA256:** `456AE1F1DAF29F74...`
  - ✗ remove — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\brand\logo-sources\odg_logo_t.zip`  (ODG_Other)
  - **✓ KEEP** — `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Attachments\odg_logo_t.zip`  (ODG_Other)

---

## Section B — Likely scratch

- **Total:** 26 files, 16.3 MB

### By Location

```
           count  size_mb
Location                 
Downloads     20     0.76
Other          3     6.80
Documents      2     7.21
ODG_Other      1     1.50
```

### Sample paths (up to 20, newest first)

- `C:\Users\ODG_j\Pictures\Screenshots\Screenshot (3).png`  (5.4 MB, age 33d)
- `C:\Users\ODG_j\Pictures\Screenshots\Screenshot (2).png`  (0.5 MB, age 35d)
- `C:\ODG\OneDrive - Opal Dragonfly Games LLC\Archive\brand\logo-sources\odg_logo_t_backup.png`  (1.5 MB, age 53d)
- `C:\Downloads\pokerdeck (1).png`  (0.0 MB, age 55d)
- `C:\Users\ODG_j\Pictures\Screenshots\Screenshot (1).png`  (0.9 MB, age 72d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Electric\Piano Electric (3).wav`  (0.0 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Sytrus Rhodes Piano\Rhodes Piano (3).wav`  (0.0 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Electric\Piano Electric (1).wav`  (0.0 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Sytrus Rhodes Piano\Rhodes Piano (9).wav`  (0.1 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Sytrus Rhodes Piano\Rhodes Piano (8).wav`  (0.1 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Sytrus Rhodes Piano\Rhodes Piano (7).wav`  (0.0 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Sytrus Rhodes Piano\Rhodes Piano (6).wav`  (0.1 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Sytrus Rhodes Piano\Rhodes Piano (5).wav`  (0.0 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Electric\Piano Electric (4).wav`  (0.0 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Sytrus Rhodes Piano\Rhodes Piano (4).wav`  (0.1 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Electric\Piano Electric (2).wav`  (0.0 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Sytrus Rhodes Piano\Rhodes Piano (12).wav`  (0.0 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Sytrus Rhodes Piano\Rhodes Piano (11).wav`  (0.1 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Sytrus Rhodes Piano\Rhodes Piano (10).wav`  (0.1 MB, age 230d)
- `C:\Users\ODG_j\Documents\Image-Line\Downloads\FL Studio Mobile Factory Data\DirectWave Samples\Keyboard\Sytrus Rhodes Piano\Rhodes Piano (1).wav`  (0.0 MB, age 230d)

---

## Section C — Orphans in scatter zones

Asset files in `Desktop`, `Downloads`, or `Documents` older than 30 days. The ODG-named subset is highest-signal: those probably want a real home.

- **Total orphans:** 379 files, 284.0 MB

### By Location × Category

```
                     count  size_mb
Location  Category                 
Downloads Archive        6    119.7
          3D_Model       5    100.1
          Audio        191     27.5
Documents Document       4     12.0
          2D_Raster    144     10.2
Downloads Video          1      7.6
          2D_Raster     21      6.3
          Document       3      0.4
          2D_Vector      4      0.2
```

### ODG-named orphans (10 files, 72.6 MB)

- `C:\Downloads\sci-fi+exploration+probe+3d+model.glb`  (42.0 MB, age 35d) → hint: **tll**
- `C:\Downloads\Meshy_AI_Emerald_Rocket_Sled_0304020024_generate.blend`  (19.7 MB, age 69d) → hint: **dhtw**
- `C:\Downloads\alogo\ODG_logo_animated.mp4`  (7.6 MB, age 49d) → hint: **brand**
- `C:\Users\ODG_j\Downloads\dhtw_online_example.png`  (1.7 MB, age 49d) → hint: **dhtw**
- `C:\Downloads\odg_logo_gold_t.png`  (1.0 MB, age 60d) → hint: **brand**
- `C:\Downloads\odg_dragonfly.png`  (0.3 MB, age 53d) → hint: **brand**
- `C:\Downloads\odg_logo_gold.jpg`  (0.2 MB, age 60d) → hint: **brand**
- `C:\Downloads\sled3d_base.glb`  (0.1 MB, age 35d) → hint: **dhtw**
- `C:\Downloads\logo_bad_flap.png`  (0.0 MB, age 72d) → hint: **brand**
- `C:\Users\ODG_j\Downloads\OpalDragonfly-Vault.zip`  (0.0 MB, age 52d) → hint: **brand**

### Non-ODG-named orphans — summary by Category (no per-file listing)

```
           count  size_mb
Category                 
Archive        5    119.7
3D_Model       2     38.4
Audio        191     27.5
2D_Raster    160     13.2
Document       7     12.5
2D_Vector      4      0.2
```
_Suggested treatment: leave them — they're personal/unrelated content. Phase 3 protect-list should include these paths if they're not project work._

---

## Section D — Suggested permanent homes per (Category × Location)

Populated cells only (count > 0). "Home" is what the Phase 5 sorter should propose for new files matching this combo. The Phase 3 one-shot cleanup may also use these as proposed destinations for existing files outside their expected home.


| Category | Location | Count | Size | Suggested home | Notes |
|---|---|--:|--:|---|---|
| Archive | ODG_Other | 77 | 7.47 GB | (case-by-case — Section A dupes first, then move into repo/vault) | Biggest bucket: 7.8 GB of zips + 2.7 GB of 2D rasters. Probably contains LoRA datasets and generated/_backups/. |
| 2D_Raster | ODG_Other | 3,298 | 2.61 GB | (case-by-case — Section A dupes first, then move into repo/vault) | Biggest bucket: 7.8 GB of zips + 2.7 GB of 2D rasters. Probably contains LoRA datasets and generated/_backups/. |
| Audio | ODG_Other | 46 | 895.8 MB | (case-by-case — Section A dupes first, then move into repo/vault) | Biggest bucket: 7.8 GB of zips + 2.7 GB of 2D rasters. Probably contains LoRA datasets and generated/_backups/. |
| 2D_Raster | Other | 459 | 422.9 MB | (skip — mostly C:\tmp and Pictures\Screenshots) | Outside ODG scope; tighten audit excludes further if noise. |
| 2D_Raster | Repo_DHTW | 489 | 362.3 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| 3D_Model | Repo_DHTW | 40 | 321.6 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| 3D_Model | ODG_Other | 30 | 224.1 MB | (case-by-case — Section A dupes first, then move into repo/vault) | Biggest bucket: 7.8 GB of zips + 2.7 GB of 2D rasters. Probably contains LoRA datasets and generated/_backups/. |
| Archive | Downloads | 6 | 119.7 MB | `_intake/_unsorted/` (manual review) | Downloads is browser scratch; move only ODG-named files. |
| 3D_Model | Downloads | 5 | 100.1 MB | `_intake/_unsorted/` (route per filename: tll → repos/tll/assets/3d, dhtw → repos/dhtw/assets/3d) | Downloads is browser scratch; move only ODG-named files. |
| 3D_Model | Other | 2 | 54.5 MB | (skip — mostly C:\tmp and Pictures\Screenshots) | Outside ODG scope; tighten audit excludes further if noise. |
| 2D_Vector | ODG_Other | 38 | 42.4 MB | (case-by-case — Section A dupes first, then move into repo/vault) | Biggest bucket: 7.8 GB of zips + 2.7 GB of 2D rasters. Probably contains LoRA datasets and generated/_backups/. |
| 3D_Model | Repo_TLL | 6 | 36.3 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| Audio | Downloads | 191 | 27.5 MB | `_intake/_unsorted/` (manual review) | Downloads is browser scratch; move only ODG-named files. |
| Video | ODG_Other | 7 | 23.6 MB | (case-by-case — Section A dupes first, then move into repo/vault) | Biggest bucket: 7.8 GB of zips + 2.7 GB of 2D rasters. Probably contains LoRA datasets and generated/_backups/. |
| 2D_Raster | Repo_TLL | 35 | 22.2 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| Audio | Repo_DHTW | 145 | 16.6 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| 2D_Raster | Repo_Other | 27 | 12.2 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| Document | Documents | 4 | 12.0 MB | (leave alone unless ODG-named) | Documents is general personal use; respect non-ODG content. |
| 2D_Raster | Downloads | 39 | 12.0 MB | `_intake/_unsorted/` (route per filename: tll → repos/tll/assets/2d/raster, dhtw → repos/dhtw/assets/2d/raster) | Downloads is browser scratch; move only ODG-named files. |
| 2D_Raster | Documents | 144 | 10.2 MB | (leave alone unless ODG-named) | Documents is general personal use; respect non-ODG content. |
| 2D_Raster | ODG_Vault | 16 | 10.1 MB | (stays in vault) | Already in canonical knowledge base. |
| Video | Downloads | 1 | 7.6 MB | `_intake/_unsorted/` (manual review) | Downloads is browser scratch; move only ODG-named files. |
| Video | Repo_Other | 1 | 7.6 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| Document | Repo_DHTW | 1 | 6.9 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| Video | Other | 8 | 6.5 MB | (skip — mostly C:\tmp and Pictures\Screenshots) | Outside ODG scope; tighten audit excludes further if noise. |
| Archive | Repo_DHTW | 2 | 5.3 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| 2D_Vector | Other | 22 | 3.9 MB | (skip — mostly C:\tmp and Pictures\Screenshots) | Outside ODG scope; tighten audit excludes further if noise. |
| Document | OneDrive_Other | 1 | 1.1 MB | Vault or repo, depending on content | Single file — verify what it is. |
| 2D_Vector | Repo_DHTW | 8 | 0.7 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| Document | Downloads | 3 | 0.4 MB | `_intake/_unsorted/` (manual review) | Downloads is browser scratch; move only ODG-named files. |
| Game_Project | Repo_DHTW | 19 | 0.3 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| Document | ODG_Other | 3 | 0.2 MB | (case-by-case — Section A dupes first, then move into repo/vault) | Biggest bucket: 7.8 GB of zips + 2.7 GB of 2D rasters. Probably contains LoRA datasets and generated/_backups/. |
| 2D_Vector | Repo_Other | 4 | 0.2 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| 2D_Vector | Downloads | 4 | 0.2 MB | `_intake/_unsorted/` (route per filename: tll → repos/tll/assets/2d/vector, dhtw → repos/dhtw/assets/2d/vector) | Downloads is browser scratch; move only ODG-named files. |
| 2D_Vector | Repo_TLL | 3 | 0.1 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| Game_Project | Repo_TLL | 3 | 0.1 MB | (stays in repo) | Already in a project repo. Section A may still recommend dedupe. |
| 3D_Texture | Other | 1 | 0.0 MB | (skip — mostly C:\tmp and Pictures\Screenshots) | Outside ODG scope; tighten audit excludes further if noise. |

---

## Decision Point — what to authorize before Phase 3

Per the build plan, Phase 3 only runs after you mark which actions to actually take. Common shapes:


- ✅ **Section A** (top dupe groups): authorize quarantine of all ✗ marked paths, keeping the ✓ KEEP one. Estimated recovery: ~906.0 MB.
- ✅/❌ **Section B** (scratch): authorize quarantine of all LikelyScratch files (small impact: ~16.3 MB).
- ✅/❌ **Section C** (orphans): authorize moves only for ODG-named orphans into `_intake/`; leave non-ODG personal content alone.
- 📋 **Section D** (routing matrix): use as the rulebook for the Phase 5 intake sorter — no actions needed in Phase 3.

Write your decisions into `data/audits/triage-decisions-2026-05-11.json` (Phase 3 consumes that file).
