# WMM Resilience 7-language Edge DOM audit (LOCAL ONLY, READ-ONLY)
# PowerShell 5.1; requires Microsoft Edge and localhost:8765 preview.
# Does not edit site files, send records to any server, deploy, or merge.
param([int]$Port=8765,[string]$OutputDir=(Join-Path $env:TEMP "WMM_Resilience_DOM_QA"))
$ErrorActionPreference="Stop"
$pf86=[Environment]::GetFolderPath("ProgramFilesX86")
$candidates=@(
 (Join-Path $pf86 "Microsoft\Edge\Application\msedge.exe"),
 (Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"),
 (Join-Path $env:LOCALAPPDATA "Microsoft\Edge\Application\msedge.exe")
)
$edge=$candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if(-not $edge){throw "Microsoft Edge not found"}
$origin="http://127.0.0.1:$Port"
try {
 $response=Invoke-WebRequest -Uri "$origin/ko/resilience/" -UseBasicParsing -TimeoutSec 8
 if($response.StatusCode -ne 200){throw "HTTP $($response.StatusCode)"}
} catch {throw "Preview server unavailable at $origin"}
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$results=@()
$langs=@("ko","en","es","fr","ar","vi","id")
foreach($lang in $langs) {
 $name="$lang-dom"
 $stdout=Join-Path $OutputDir "$name.html"
 $stderr=Join-Path $OutputDir "$name-stderr.log"
 $profile=Join-Path $OutputDir "$name-edge-profile"
 $url="$origin/$lang/resilience/?country=NZ"
 $args=@("--headless=new","--no-first-run","--disable-gpu",
  "--disable-extensions","--disable-background-networking",
  "--user-data-dir=$profile","--virtual-time-budget=7000","--dump-dom",$url)
 $proc=Start-Process -FilePath $edge -ArgumentList $args -PassThru -Wait -RedirectStandardOutput $stdout -RedirectStandardError $stderr
 $dom=if(Test-Path $stdout){Get-Content -Path $stdout -Raw -Encoding UTF8}else{""}
 $countrySelect=[regex]::Match($dom,'(?is)<select\b[^>]*\bid="rs-country"[^>]*>(.*?)</select>')
 $countries=if($countrySelect.Success){([regex]::Matches($countrySelect.Groups[1].Value,'(?i)<option\b')).Count}else{0}
 # Browser selected option serialization differs; confirm NZ using the rendered panel instead.
 $countryPanel=[regex]::Match($dom,'(?is)<div\b[^>]*\bid="rs-foodcountry"[^>]*>(.*?)</div>')
 $panelHasNZ=$countryPanel.Success -and $countryPanel.Groups[1].Value.Contains('(NZ)')
 $hasMainHeading=[regex]::IsMatch($dom,'(?is)<h1\b[^>]*>[^<]+</h1>')
 $rtl=if($lang -eq "ar") {[regex]::IsMatch($dom,'(?is)<main\b[^>]*\bdir="rtl"')} else {[regex]::IsMatch($dom,'(?is)<main\b[^>]*\bdir="ltr"')}
 $computed=[regex]::IsMatch($dom,'(?is)<div\b[^>]*\bid="rs-out"[^>]*>.*?rs-metric.*?</div>')
 $loaded=$countries -eq 193 -and $panelHasNZ
 $passed=$proc.ExitCode -eq 0 -and $hasMainHeading -and $rtl -and $computed -and $loaded
 $results += [pscustomobject]@{
  Language=$lang;EdgeExitCode=$proc.ExitCode;Countries=$countries;
  CountryPanelNZ=$panelHasNZ;Heading=$hasMainHeading;Direction=$rtl;
  Computed=$computed;Pass=$passed;DomFile=$stdout
 }
 Write-Host "$lang : $([string]$passed) (countries=$countries, NZ=$panelHasNZ, calc=$computed)"
}
$csv=Join-Path $OutputDir "dom-results.csv"
$results | Export-Csv -Encoding UTF8 -NoTypeInformation -Path $csv
$results | Format-Table Language,Countries,CountryPanelNZ,Heading,Direction,Computed,Pass -AutoSize
if(@($results | Where-Object { -not $_.Pass }).Count -gt 0){
 Write-Warning "DOM QA has failures; inspect dom-results.csv and individual .html files."
 throw "DOM QA did not pass all seven locales"
}
Write-Host "PASS: 7 locales executed and loaded 193 countries in real Edge headless DOM."
Write-Host "Artifacts: $OutputDir"
Write-Host "Limits: Not a phone device test, visual review, WCAG audit, or translation verification."
