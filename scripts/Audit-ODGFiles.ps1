<#
.SYNOPSIS
    Audits all art and asset files across the C: drive to map the scatter problem
    before implementing an intake/sorting system.

.DESCRIPTION
    Walks the entire C: drive (with sensible system exclusions) and inventories
    every file matching known art/asset extensions. Produces a CSV with full
    metadata including SHA256 hashes for duplicate detection.

    Read-only operation. Moves nothing, deletes nothing, touches nothing.

.PARAMETER OutputPath
    Where to write the CSV. Default: $env:USERPROFILE\Desktop\ODG-Audit-YYYY-MM-DD.csv

.PARAMETER IncludeHashes
    If set, computes SHA256 for each file. Adds significant time on large libraries
    but enables exact-duplicate detection. Default: $true

.PARAMETER MinSizeKB
    Skip files smaller than this. Filters out junk thumbnails, icon caches, etc.
    Default: 10

.EXAMPLE
    .\Audit-ODGFiles.ps1
    .\Audit-ODGFiles.ps1 -IncludeHashes:$false   # faster, no dedupe data
    .\Audit-ODGFiles.ps1 -MinSizeKB 1            # include tiny files too

.NOTES
    Author: Drafted for Jeff @ Opal Dragonfly Games
    Run from PowerShell 5.1+ or PowerShell 7. No admin required.
#>

[CmdletBinding()]
param(
    [string]$OutputPath = "$env:USERPROFILE\Desktop\ODG-Audit-$(Get-Date -Format 'yyyy-MM-dd').csv",
    [bool]$IncludeHashes = $true,
    [int]$MinSizeKB = 10
)

# ---------------------------------------------------------------------------
# CONFIG: what counts as an "asset" and what to skip
# ---------------------------------------------------------------------------

# Extensions we care about, grouped for clarity
$ArtExtensions = @{
    '2D_Raster'    = @('.png','.jpg','.jpeg','.gif','.bmp','.tif','.tiff','.webp','.heic')
    '2D_Vector'    = @('.svg','.ai','.eps','.afdesign','.afpub','.afphoto','.cdr')
    '2D_Layered'   = @('.psd','.psb','.xcf','.kra','.clip')
    '3D_Model'     = @('.glb','.gltf','.obj','.fbx','.blend','.dae','.3ds','.stl','.ply','.usd','.usdz')
    '3D_Texture'   = @('.exr','.hdr','.dds','.ktx','.basis')
    'Document'     = @('.pdf','.indd','.idml')
    'Audio'        = @('.wav','.mp3','.ogg','.flac','.aiff','.m4a')
    'Video'        = @('.mp4','.mov','.webm','.avi','.mkv')
    'Game_Project' = @('.tscn','.tres','.gd','.gdshader','.import')
    'Archive'      = @('.zip','.rar','.7z')  # often contains art assets
}

# Build a flat lookup
$ExtLookup = @{}
foreach ($category in $ArtExtensions.Keys) {
    foreach ($ext in $ArtExtensions[$category]) {
        $ExtLookup[$ext] = $category
    }
}

# Paths to skip entirely — system noise, caches, dependencies
$ExcludePaths = @(
    'C:\Windows'
    'C:\Program Files'
    'C:\Program Files (x86)'
    'C:\ProgramData'
    'C:\$Recycle.Bin'
    'C:\System Volume Information'
    'C:\Recovery'
    "$env:USERPROFILE\AppData\Local\Microsoft"
    "$env:USERPROFILE\AppData\Local\Packages"
    "$env:USERPROFILE\AppData\Local\Temp"
    "$env:USERPROFILE\AppData\Roaming\Microsoft"
    "$env:USERPROFILE\.cache"
    "$env:USERPROFILE\.nuget"
    "$env:USERPROFILE\.gradle"
)

# Folder name patterns to skip wherever they appear in the tree
$ExcludeFolderPatterns = @(
    'node_modules'
    '.git'
    '.svn'
    '.venv'
    'venv'
    '__pycache__'
    '.next'
    '.nuxt'
    'dist'
    'build'
    'target'
    '.godot'        # Godot editor cache
    '.import'       # Godot import cache
    'bin'
    'obj'
)

# Filename patterns that suggest "probably scratch / probably dupe"
$ScratchPatterns = @(
    '\s\(\d+\)\.'           # foo (1).png, bar (2).jpg
    '_copy\.'               # foo_copy.png
    '_copy\d*\.'            # foo_copy2.png
    '-copy\.'               # foo-copy.png
    '^Copy\sof\s'           # Copy of foo.png
    '^tmp_'                 # tmp_whatever.png
    '^temp_'                # temp_whatever.png
    '^untitled'             # untitled.png, Untitled-1.psd
    '_old\.'                # foo_old.png
    '_backup\.'             # foo_backup.png
    '~\$'                   # Office lock files
)

# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "=== ODG Asset Audit ===" -ForegroundColor Cyan
Write-Host "Output:        $OutputPath"
Write-Host "Include hash:  $IncludeHashes"
Write-Host "Min size:      $MinSizeKB KB"
Write-Host "Started:       $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

$startTime = Get-Date
$MinSizeBytes = $MinSizeKB * 1KB
$results = [System.Collections.Generic.List[PSCustomObject]]::new()
$errorLog = [System.Collections.Generic.List[string]]::new()
$scanned = 0
$matched = 0

# Compile scratch pattern once
$scratchRegex = ($ScratchPatterns -join '|')

# ---------------------------------------------------------------------------
# DRIVE WALK
# ---------------------------------------------------------------------------

Write-Host "Walking C:\ ... (this can take 5-20 minutes depending on disk size)" -ForegroundColor Yellow
Write-Host ""

# Top-level roots to scan — everything on C: except excluded paths
$rootCandidates = Get-ChildItem -Path 'C:\' -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object {
        $fullPath = $_.FullName
        -not ($ExcludePaths | Where-Object { $fullPath -like "$_*" })
    }

# Also include the user profile root files (Desktop, Downloads, Documents, etc.)
# These are usually under C:\Users\<name>\ which is covered, but be explicit

foreach ($root in $rootCandidates) {
    Write-Host "Scanning: $($root.FullName)" -ForegroundColor Gray

    try {
        Get-ChildItem -Path $root.FullName -Recurse -File -Force -ErrorAction SilentlyContinue |
            ForEach-Object {
                $scanned++
                if ($scanned % 5000 -eq 0) {
                    Write-Host "  ...scanned $scanned files, matched $matched so far" -ForegroundColor DarkGray
                }

                $file = $_
                $fullPath = $file.FullName

                # Skip if inside an excluded folder pattern
                foreach ($pattern in $ExcludeFolderPatterns) {
                    if ($fullPath -match "\\$pattern\\") { return }
                }

                # Skip if inside an explicit excluded path
                foreach ($exclude in $ExcludePaths) {
                    if ($fullPath -like "$exclude*") { return }
                }

                # Check extension
                $ext = $file.Extension.ToLower()
                if (-not $ExtLookup.ContainsKey($ext)) { return }

                # Check size threshold
                if ($file.Length -lt $MinSizeBytes) { return }

                $matched++

                # Compute hash if requested
                $hash = $null
                if ($IncludeHashes) {
                    try {
                        $hash = (Get-FileHash -Path $fullPath -Algorithm SHA256 -ErrorAction Stop).Hash
                    } catch {
                        $errorLog.Add("HASH FAIL: $fullPath -- $($_.Exception.Message)") | Out-Null
                    }
                }

                # Flag likely scratch
                $isScratch = $file.Name -match $scratchRegex

                # Categorize parent location
                $location = switch -Regex ($fullPath) {
                    '\\ODG_Vault\\'         { 'ODG_Vault'; break }
                    'C:\\ODG\\repos\\tll'   { 'Repo_TLL'; break }
                    'C:\\ODG\\repos\\dhtw'  { 'Repo_DHTW'; break }
                    'C:\\ODG\\repos\\'      { 'Repo_Other'; break }
                    'C:\\ODG\\'             { 'ODG_Other'; break }
                    '\\Downloads\\'         { 'Downloads'; break }
                    '\\Desktop\\'           { 'Desktop'; break }
                    '\\Documents\\'         { 'Documents'; break }
                    '\\OneDrive'            { 'OneDrive_Other'; break }
                    default                 { 'Other' }
                }

                $results.Add([PSCustomObject]@{
                    FullPath      = $fullPath
                    FileName      = $file.Name
                    Extension     = $ext
                    Category      = $ExtLookup[$ext]
                    Location      = $location
                    ParentFolder  = $file.Directory.FullName
                    SizeKB        = [math]::Round($file.Length / 1KB, 2)
                    SizeMB        = [math]::Round($file.Length / 1MB, 3)
                    Created       = $file.CreationTime.ToString('yyyy-MM-dd HH:mm:ss')
                    Modified      = $file.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
                    AgeDays       = [math]::Round(((Get-Date) - $file.LastWriteTime).TotalDays, 1)
                    LikelyScratch = $isScratch
                    SHA256        = $hash
                }) | Out-Null
            }
    } catch {
        $errorLog.Add("ROOT FAIL: $($root.FullName) -- $($_.Exception.Message)") | Out-Null
    }
}

# ---------------------------------------------------------------------------
# DUPLICATE DETECTION
# ---------------------------------------------------------------------------

if ($IncludeHashes -and $results.Count -gt 0) {
    Write-Host ""
    Write-Host "Detecting duplicates by SHA256..." -ForegroundColor Yellow

    $hashGroups = $results | Where-Object { $_.SHA256 } | Group-Object SHA256 | Where-Object { $_.Count -gt 1 }
    $dupePaths = @{}
    foreach ($group in $hashGroups) {
        foreach ($item in $group.Group) {
            $dupePaths[$item.FullPath] = $group.Count
        }
    }

    foreach ($r in $results) {
        $r | Add-Member -NotePropertyName 'DuplicateCount' -NotePropertyValue ($dupePaths[$r.FullPath] ?? 1) -Force
    }
}

# ---------------------------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------------------------

$results | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8

# Error log if any
if ($errorLog.Count -gt 0) {
    $errorLogPath = $OutputPath -replace '\.csv$', '-errors.log'
    $errorLog | Out-File -FilePath $errorLogPath -Encoding UTF8
    Write-Host "Wrote $($errorLog.Count) errors to: $errorLogPath" -ForegroundColor DarkYellow
}

# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------

$elapsed = (Get-Date) - $startTime
$totalSizeMB = [math]::Round((($results | Measure-Object SizeKB -Sum).Sum / 1024), 2)
$totalSizeGB = [math]::Round($totalSizeMB / 1024, 2)

Write-Host ""
Write-Host "=== AUDIT COMPLETE ===" -ForegroundColor Green
Write-Host "Elapsed:       $($elapsed.ToString('hh\:mm\:ss'))"
Write-Host "Files scanned: $scanned"
Write-Host "Assets found:  $($results.Count)"
Write-Host "Total size:    $totalSizeMB MB ($totalSizeGB GB)"
Write-Host ""

Write-Host "By Location:" -ForegroundColor Cyan
$results | Group-Object Location | Sort-Object Count -Descending |
    Format-Table @{N='Location';E={$_.Name}}, Count, @{N='SizeMB';E={[math]::Round((($_.Group | Measure-Object SizeKB -Sum).Sum / 1024), 1)}} -AutoSize

Write-Host "By Category:" -ForegroundColor Cyan
$results | Group-Object Category | Sort-Object Count -Descending |
    Format-Table @{N='Category';E={$_.Name}}, Count, @{N='SizeMB';E={[math]::Round((($_.Group | Measure-Object SizeKB -Sum).Sum / 1024), 1)}} -AutoSize

$scratchCount = ($results | Where-Object { $_.LikelyScratch }).Count
Write-Host "Likely scratch/temp files: $scratchCount" -ForegroundColor Yellow

if ($IncludeHashes) {
    $dupeCount = ($results | Where-Object { $_.DuplicateCount -gt 1 }).Count
    $uniqueDupeGroups = ($results | Where-Object { $_.DuplicateCount -gt 1 } | Select-Object -Unique SHA256).Count
    Write-Host "Exact duplicates: $dupeCount files across $uniqueDupeGroups groups" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "CSV ready at: $OutputPath" -ForegroundColor Green
Write-Host ""
Write-Host "Next: open in Excel, sort by Location, then by Modified desc, to triage." -ForegroundColor Cyan
