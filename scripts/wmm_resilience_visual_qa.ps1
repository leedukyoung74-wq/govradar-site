# WMM Resilience visual capture | local-only | no installs, no uploads, no deployments
# Prerequisites: Windows Edge and a local preview server on 127.0.0.1:8765.
# Captures screenshots for manual review; does not certify accessibility or layout.
param(
    [int]$Port = 8765,
    [string]$OutputDir = (Join-Path $env:TEMP "WMM_Resilience_Visual_QA")
)
$ErrorActionPreference = "Stop"
$pf86 = [Environment]::GetFolderPath('ProgramFilesX86')
$edgeCandidates = @(
    (Join-Path $pf86 "Microsoft\Edge\Application\msedge.exe"),
    (Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"),
    (Join-Path $env:LOCALAPPDATA "Microsoft\Edge\Application\msedge.exe")
)
$edge = $edgeCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $edge) { throw "Microsoft Edge not found. Nothing was changed." }
$origin = "http://127.0.0.1:$Port"
try {
    $r = Invoke-WebRequest -Uri "$origin/ko/resilience/" -UseBasicParsing -TimeoutSec 8
    if ($r.StatusCode -ne 200) { throw "Local preview HTTP $($r.StatusCode)" }
} catch {
    throw "Local preview server unavailable at $origin. Keep python http.server running."
}
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$profile = Join-Path $OutputDir "edge-isolated-profile"
$records = @()
$views = @(
    @{ Name="desktop"; W=1440; H=900 },
    @{ Name="mobile"; W=390; H=844 }
)
$langs = @("ko","en","es","fr","ar","vi","id")
foreach ($lang in $langs) {
    foreach ($view in $views) {
        $name = "$lang-$($view.Name)"
        $file = Join-Path $OutputDir "$name.png"
        $url = "$origin/$lang/resilience/"
        $args = @(
            "--headless=new","--no-first-run","--disable-gpu",
            "--disable-extensions","--disable-background-networking",
            "--hide-scrollbars","--force-device-scale-factor=1",
            "--user-data-dir=$profile",
            "--window-size=$($view.W),$($view.H)",
            "--virtual-time-budget=5000",
            "--screenshot=$file",
            $url
        )
        Write-Host "Capture: $name"
        $stderrFile = Join-Path $OutputDir "$name-edge-stderr.log"
        $stdoutFile = Join-Path $OutputDir "$name-edge-stdout.log"
        $process = Start-Process -FilePath $edge -ArgumentList $args -Wait -PassThru -RedirectStandardError $stderrFile -RedirectStandardOutput $stdoutFile
        $exit = $process.ExitCode
        $ok = (Test-Path $file) -and ((Get-Item $file).Length -gt 5000)
        $records += [pscustomobject]@{
            Language=$lang
            Viewport=$view.Name
            Width=$view.W
            Height=$view.H
            File=$file
            Captured=$ok
            EdgeExitCode=$exit
            Sha256=if ($ok) {(Get-FileHash -Algorithm SHA256 $file).Hash} else {""}
        }
    }
}
$records | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $OutputDir "capture-results.csv")
$records | Format-Table Language,Viewport,Captured,EdgeExitCode -AutoSize
Write-Host "Output folder: $OutputDir"
Write-Host "Captures are for manual visual review. No live site changes, no data uploads."
if ($records.Where({-not $_.Captured}).Count -gt 0) { throw "At least one screenshot failed. See capture-results.csv" }
