# Conveyor is the production operating system/platform; SimilarStoic is its first
# pilot channel. The ATLAS_* names below remain only as a temporary compatibility
# contract until the current technical API undergoes its controlled migration.

& {
$ErrorActionPreference = 'Stop'

function Resolve-RequiredDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string] $LiteralPath,

        [Parameter(Mandatory = $true)]
        [string] $Description
    )

    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Container)) {
        throw "$Description was not found at the required path: $LiteralPath"
    }

    return (Resolve-Path -LiteralPath $LiteralPath).Path
}

function Resolve-RequiredFile {
    param(
        [Parameter(Mandatory = $true)]
        [string] $LiteralPath,

        [Parameter(Mandatory = $true)]
        [string] $Description
    )

    if (-not (Test-Path -LiteralPath $LiteralPath -PathType Leaf)) {
        throw "$Description was not found at the required path: $LiteralPath"
    }

    return (Resolve-Path -LiteralPath $LiteralPath).Path
}

# Derive the approved layout from this file:
# <ConveyorOS>\source\Conveyor\scripts\set_conveyor_environment.ps1
$repositoryRoot = Resolve-RequiredDirectory -LiteralPath (Join-Path $PSScriptRoot '..') -Description 'Conveyor repository root'
$sourceRoot = Split-Path -Parent $repositoryRoot
$conveyorRoot = Split-Path -Parent $sourceRoot

if ((Split-Path -Leaf $PSScriptRoot) -ne 'scripts' -or
    (Split-Path -Leaf $repositoryRoot) -ne 'Conveyor' -or
    (Split-Path -Leaf $sourceRoot) -ne 'source') {
    throw "The script is not in the expected <ConveyorOS>\source\Conveyor\scripts structure. Resolved repository root: $repositoryRoot"
}

$conveyorRoot = Resolve-RequiredDirectory -LiteralPath $conveyorRoot -Description 'ConveyorOS root'
$runtimeRoot = Resolve-RequiredDirectory -LiteralPath (Join-Path $conveyorRoot 'runtime\ConveyorRuntime') -Description 'Conveyor runtime root'
$databasePath = Resolve-RequiredFile -LiteralPath (Join-Path $runtimeRoot 'conveyor.db') -Description 'Production Conveyor database'
$assetRoot = Resolve-RequiredDirectory -LiteralPath (Join-Path $runtimeRoot 'assets') -Description 'Production asset root'
$mediaRoot = Resolve-RequiredDirectory -LiteralPath (Join-Path $runtimeRoot 'media') -Description 'Production media root'
$toolsRoot = Resolve-RequiredDirectory -LiteralPath (Join-Path $repositoryRoot '.tools') -Description 'Repository tools root'

$ffmpegCandidates = @(Get-ChildItem -LiteralPath $toolsRoot -Recurse -File -Filter 'ffmpeg.exe' | Where-Object { $_.Length -gt 0 })
if ($ffmpegCandidates.Count -ne 1) {
    throw "Expected exactly one usable ffmpeg.exe under $toolsRoot, but found $($ffmpegCandidates.Count)."
}

$ffprobeCandidates = @(Get-ChildItem -LiteralPath $toolsRoot -Recurse -File -Filter 'ffprobe.exe' | Where-Object { $_.Length -gt 0 })
if ($ffprobeCandidates.Count -ne 1) {
    throw "Expected exactly one usable ffprobe.exe under $toolsRoot, but found $($ffprobeCandidates.Count)."
}

$ffmpegPath = $ffmpegCandidates[0].FullName
$ffprobePath = $ffprobeCandidates[0].FullName
if ((Split-Path -Parent $ffmpegPath) -ne (Split-Path -Parent $ffprobePath)) {
    throw "The unique ffprobe.exe does not correspond to the selected ffmpeg.exe directory: $ffmpegPath"
}

# Set values only after every required production path has passed validation.
$env:ATLAS_DB_PATH = $databasePath
$env:ATLAS_ASSET_STORAGE_ROOT = $assetRoot
$env:ATLAS_MEDIA_STORAGE_ROOT = $mediaRoot
$env:ATLAS_FFMPEG_PATH = $ffmpegPath
$env:ATLAS_FFPROBE_PATH = $ffprobePath

Write-Host 'Conveyor runtime environment configured for this PowerShell process:'
Write-Host "ATLAS_DB_PATH=$($env:ATLAS_DB_PATH)"
Write-Host "ATLAS_ASSET_STORAGE_ROOT=$($env:ATLAS_ASSET_STORAGE_ROOT)"
Write-Host "ATLAS_MEDIA_STORAGE_ROOT=$($env:ATLAS_MEDIA_STORAGE_ROOT)"
Write-Host "ATLAS_FFMPEG_PATH=$($env:ATLAS_FFMPEG_PATH)"
Write-Host "ATLAS_FFPROBE_PATH=$($env:ATLAS_FFPROBE_PATH)"
}
