param(
    [string]$ProjectRoot = 'E:/VividRP_Reborn',
    [string]$UnityDataRoot = 'E:/Unity/6000.7.0a6/Editor/Data'
)
$ErrorActionPreference = 'Stop'
$outputDirectory = Join-Path ([System.IO.Path]::GetTempPath()) 'tsr-lighting-final-csharp-check'
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
$compiler = Join-Path $UnityDataRoot 'DotNetSdk/sdk/10.0.301/Roslyn/bincore/csc.dll'
$runtime = Join-Path $UnityDataRoot 'DotNetSdk/dotnet.exe'
$results = foreach ($assembly in @('VividRP.Runtime', 'VividRP.Editor', 'VividRP.Editor.Tests')) {
    $sourceResponse = Join-Path $ProjectRoot ('Library/Bee/artifacts/1900b0aE.dag/' + $assembly + '.rsp')
    $arguments = [System.Collections.Generic.List[string]]::new()
    foreach ($line in Get-Content -LiteralPath $sourceResponse) {
        if ($line.StartsWith('-out:')) { $arguments.Add('-out:"' + (Join-Path $outputDirectory ($assembly + '.dll')) + '"') }
        elseif ($line.StartsWith('-refout:')) { $arguments.Add('-refout:"' + (Join-Path $outputDirectory ($assembly + '.ref.dll')) + '"') }
        else { $arguments.Add($line) }
    }
    $responsePath = Join-Path $outputDirectory ($assembly + '.rsp')
    $compilerLog = Join-Path $outputDirectory ($assembly + '.log')
    [System.IO.File]::WriteAllLines($responsePath, $arguments)
    Push-Location -LiteralPath $ProjectRoot
    try { & $runtime $compiler ('@' + $responsePath) *> $compilerLog; $compilerExit = $LASTEXITCODE }
    finally { Pop-Location }
    Copy-Item -LiteralPath $compilerLog -Destination (Join-Path $PSScriptRoot ($assembly + '.compile.log'))
    [ordered]@{ assembly = $assembly; exitCode = $compilerExit; response = $responsePath }
}
[ordered]@{
    checkedUtc = [DateTime]::UtcNow.ToString('o')
    results = @($results)
    unityTestFrameworkRun = $false
    reason = 'Interactive Editor remained open. These checks compile assemblies without invoking NUnit or Unity behavior.'
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'csharp-validation.json') -Encoding utf8
$results | ConvertTo-Json -Depth 3
if (@($results | Where-Object { $_.exitCode -ne 0 }).Count -ne 0) { exit 1 }
