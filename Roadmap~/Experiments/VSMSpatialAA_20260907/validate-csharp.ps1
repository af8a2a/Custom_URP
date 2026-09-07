param(
    [string]$ProjectRoot = 'E:/VividRP_Reborn',
    [string]$UnityDataRoot = 'E:/Unity/6000.7.0a6/Editor/Data',
    [string]$BeeDirectory,
    [string]$OutputDirectory,
    [switch]$ListOnly
)
$ErrorActionPreference = 'Stop'
$assemblies = @('VividRP.Runtime', 'VividRP.Editor', 'VividRP.Editor.Tests')
if (-not $BeeDirectory) {
    $latest = Get-ChildItem -LiteralPath (Join-Path $ProjectRoot 'Library/Bee/artifacts') -Filter 'VividRP.Runtime.rsp' -Recurse -File |
        Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    if (-not $latest) { throw 'No Unity Bee Runtime response file was found.' }
    $BeeDirectory = $latest.DirectoryName
}
$responses = @(foreach ($assembly in $assemblies) {
    $path = Join-Path $BeeDirectory ($assembly + '.rsp')
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing Bee response file: $path" }
    [pscustomobject]@{ assembly = $assembly; path = $path; sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
})
if ($ListOnly) { $responses | ConvertTo-Json -Depth 4; return }
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $PSScriptRoot ('validation-' + [DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss_fff') + '/csharp')
}
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path
$runtime = Join-Path $UnityDataRoot 'DotNetSdk/dotnet.exe'
$compiler = Join-Path $UnityDataRoot 'DotNetSdk/sdk/10.0.301/Roslyn/bincore/csc.dll'
$sourcePaths = @(foreach ($response in $responses) {
    foreach ($line in Get-Content -LiteralPath $response.path) {
        $path = $line.Trim().Trim('"')
        if ($path.EndsWith('.cs', [StringComparison]::OrdinalIgnoreCase)) {
            if (-not [IO.Path]::IsPathRooted($path)) { $path = Join-Path $ProjectRoot $path }
            (Resolve-Path -LiteralPath $path).Path
        }
    }
}) | Sort-Object -Unique
function Get-CSharpSnapshot {
    @(foreach ($path in $sourcePaths) {
        [ordered]@{ path = $path; sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
    })
}
$before = Get-CSharpSnapshot
$before | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'source-sha256-before.json') -Encoding utf8
$compiledReferences = @{}
$upstreamFailed = $false
$results = @(foreach ($response in $responses) {
    $assembly = $response.assembly
    $arguments = [System.Collections.Generic.List[string]]::new()
    $newReference = Join-Path $OutputDirectory ($assembly + '.ref.dll')
    foreach ($line in Get-Content -LiteralPath $response.path) {
        if ($line.StartsWith('-out:')) { $arguments.Add('-out:"' + (Join-Path $OutputDirectory ($assembly + '.dll')) + '"') }
        elseif ($line.StartsWith('-refout:')) { $arguments.Add('-refout:"' + $newReference + '"') }
        elseif ($line -match '^-r:"?(.+[/\\])(VividRP\.(?:Runtime|Editor))\.ref\.dll"?$' -and $compiledReferences.ContainsKey($Matches[2])) {
            $arguments.Add('-r:"' + $compiledReferences[$Matches[2]] + '"')
        }
        else { $arguments.Add($line) }
    }
    $responsePath = Join-Path $OutputDirectory ($assembly + '.rsp')
    $log = Join-Path $OutputDirectory ($assembly + '.log')
    [IO.File]::WriteAllLines($responsePath, $arguments)
    Copy-Item -LiteralPath $response.path -Destination (Join-Path $OutputDirectory ($assembly + '.original.rsp'))
    if ($upstreamFailed) {
        'Skipped because a required assembly failed; stale Unity references were not substituted.' | Set-Content -LiteralPath $log
        $compilerExit = -1
    }
    else {
        Push-Location -LiteralPath $ProjectRoot
        try { & $runtime $compiler ('@' + $responsePath) *> $log; $compilerExit = $LASTEXITCODE }
        finally { Pop-Location }
        if ($compilerExit -eq 0) { $compiledReferences[$assembly] = $newReference }
        else { $upstreamFailed = $true }
    }
    [ordered]@{
        assembly = $assembly; exitCode = $compilerExit; log = $log
        originalResponse = $response.path; originalResponseSha256 = $response.sha256
        response = $responsePath; responseSha256 = (Get-FileHash -LiteralPath $responsePath -Algorithm SHA256).Hash
        referenceSha256 = $(if ($compilerExit -eq 0) { (Get-FileHash -LiteralPath $newReference -Algorithm SHA256).Hash } else { $null })
    }
})
$after = Get-CSharpSnapshot
$after | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'source-sha256-after.json') -Encoding utf8
$stable = ($before | ConvertTo-Json -Depth 4 -Compress) -ceq ($after | ConvertTo-Json -Depth 4 -Compress)
$responseStable = @($responses | Where-Object { (Get-FileHash -LiteralPath $_.path -Algorithm SHA256).Hash -cne $_.sha256 }).Count -eq 0
$report = [ordered]@{
    checkedUtc = [DateTime]::UtcNow.ToString('o'); projectRoot = $ProjectRoot
    compiler = $compiler; compilerSha256 = (Get-FileHash -LiteralPath $compiler -Algorithm SHA256).Hash
    sourceTreeStable = $stable; beeResponsesStable = $responseStable; results = $results
    rebuiltDependenciesUsed = $true; unityTestFrameworkRun = $false
    reason = 'Interactive Editor remains open. Compile Runtime, Editor and Tests only; no Unity or NUnit invocation.'
}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'csharp-validation.json') -Encoding utf8
$report | ConvertTo-Json -Depth 6
if (-not $stable -or -not $responseStable -or @($results | Where-Object { $_.exitCode -ne 0 }).Count -ne 0) { exit 1 }
