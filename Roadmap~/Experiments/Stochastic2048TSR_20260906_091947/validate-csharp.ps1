param(
    [string]$ProjectRoot = 'E:/VividRP_Reborn',
    [string]$UnityDataRoot = 'E:/Unity/6000.7.0a6/Editor/Data'
)
$ErrorActionPreference = 'Stop'
$outputDirectory = Join-Path ([System.IO.Path]::GetTempPath()) 'vsm-stochastic-final-csharp-check'
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
$sourceResponse = Join-Path $ProjectRoot 'Library/Bee/artifacts/1900b0aE.dag/VividRP.Editor.Tests.rsp'
$compiler = Join-Path $UnityDataRoot 'DotNetSdk/sdk/10.0.301/Roslyn/bincore/csc.dll'
$runtime = Join-Path $UnityDataRoot 'DotNetSdk/dotnet.exe'
$arguments = [System.Collections.Generic.List[string]]::new()
foreach ($line in Get-Content -LiteralPath $sourceResponse) {
    if ($line.StartsWith('-out:')) { $arguments.Add('-out:"' + (Join-Path $outputDirectory 'VividRP.Editor.Tests.dll') + '"') }
    elseif ($line.StartsWith('-refout:')) { $arguments.Add('-refout:"' + (Join-Path $outputDirectory 'VividRP.Editor.Tests.ref.dll') + '"') }
    else { $arguments.Add($line) }
}
$responsePath = Join-Path $outputDirectory 'VividRP.Editor.Tests.rsp'
$compilerLog = Join-Path $outputDirectory 'VividRP.Editor.Tests.log'
[System.IO.File]::WriteAllLines($responsePath, $arguments)
Push-Location -LiteralPath $ProjectRoot
try {
    & $runtime $compiler ('@' + $responsePath) *> $compilerLog
    $compilerExit = $LASTEXITCODE
} finally { Pop-Location }

# Read metadata only. This neither loads Unity behavior nor invokes the test runner.
Add-Type -AssemblyName System.Reflection.Metadata
function Read-StochasticBindings([string]$AssemblyPath) {
    $stream = [System.IO.File]::OpenRead($AssemblyPath)
    $pe = [System.Reflection.PortableExecutable.PEReader]::new($stream)
    $volumeField = $false; $baselineField = $false; $volumeReference = $false
    try {
        $metadata = [System.Reflection.Metadata.PEReaderExtensions]::GetMetadataReader($pe)
        foreach ($typeHandle in $metadata.TypeDefinitions) {
            $type = $metadata.GetTypeDefinition($typeHandle)
            $typeName = $metadata.GetString($type.Name)
            if ($typeName -ne 'CascadedShadowSettingsVolume' -and $typeName -ne 'VSMBaselineCase') { continue }
            foreach ($fieldHandle in $type.GetFields()) {
                $field = $metadata.GetFieldDefinition($fieldHandle)
                $fieldName = $metadata.GetString($field.Name)
                if ($typeName -eq 'CascadedShadowSettingsVolume' -and $fieldName -eq 'virtualShadowMapStochasticFiltering') { $volumeField = $true }
                if ($typeName -eq 'VSMBaselineCase' -and $fieldName -eq 'stochasticFiltering') { $baselineField = $true }
            }
        }
        foreach ($memberHandle in $metadata.MemberReferences) {
            $member = $metadata.GetMemberReference($memberHandle)
            if ($metadata.GetString($member.Name) -eq 'virtualShadowMapStochasticFiltering') { $volumeReference = $true }
        }
    } finally { $pe.Dispose(); $stream.Dispose() }
    return [ordered]@{
        path = $AssemblyPath
        sha256 = (Get-FileHash -LiteralPath $AssemblyPath -Algorithm SHA256).Hash
        lastWriteUtc = (Get-Item -LiteralPath $AssemblyPath).LastWriteTimeUtc.ToString('o')
        volumeFieldDeclared = $volumeField
        baselineFieldDeclared = $baselineField
        volumeFieldReferenced = $volumeReference
    }
}
$runtimeAssembly = Read-StochasticBindings (Join-Path $ProjectRoot 'Library/ScriptAssemblies/VividRP.Runtime.dll')
$editorAssembly = Read-StochasticBindings (Join-Path $ProjectRoot 'Library/ScriptAssemblies/VividRP.Editor.dll')
$runtimeReference = Read-StochasticBindings (Join-Path $ProjectRoot 'Library/Bee/artifacts/1900b0aE.dag/VividRP.Runtime.ref.dll')
$editorReference = Read-StochasticBindings (Join-Path $ProjectRoot 'Library/Bee/artifacts/1900b0aE.dag/VividRP.Editor.ref.dll')
$bindingsMatch = $runtimeAssembly.volumeFieldDeclared -and $runtimeReference.volumeFieldDeclared `
    -and $editorAssembly.baselineFieldDeclared -and $editorAssembly.volumeFieldReferenced -and $editorReference.baselineFieldDeclared
$warnings = @(Get-Content -LiteralPath $compilerLog | Where-Object { $_ -match 'warning CS|error CS' })
[System.IO.File]::WriteAllLines((Join-Path $PSScriptRoot 'csharp-warnings.log'), [string[]]$warnings)
$sources = @(
    'Tests/Editor/RenderPass/Shadows/VirtualShadowMapSamplingTests.cs',
    'Tests/Editor/RenderPass/Shadows/VirtualShadowMapSamplingTests.compute',
    'Tests/Editor/RenderPass/Shadows/CascadedShadowSettingsVolumeTests.cs',
    'Tests/Editor/RenderPass/Shadows/VSMBaselineRecorderTests.cs',
    'Runtime/RenderPipeline/CascadedShadowSettingsVolume.cs',
    'Editor/Tools/VSMBaselineData.cs'
)
$sourceHashes = foreach ($source in $sources) {
    [ordered]@{ path = $source; sha256 = (Get-FileHash -LiteralPath (Join-Path $ProjectRoot ('Packages/VividRP/' + $source)) -Algorithm SHA256).Hash }
}
$manifest = [ordered]@{
    checkedUtc = [DateTime]::UtcNow.ToString('o')
    success = ($compilerExit -eq 0 -and $bindingsMatch)
    compilerExitCode = $compilerExit
    command = '& "' + $runtime + '" "' + $compiler + '" "@' + $responsePath + '"'
    sourceResponse = $sourceResponse
    sourceResponseSha256 = (Get-FileHash -LiteralPath $sourceResponse -Algorithm SHA256).Hash
    binaryAndResponseOutput = $outputDirectory
    warningCount = $warnings.Count
    warningsFile = 'csharp-warnings.log'
    metadataBindingsMatch = $bindingsMatch
    assemblies = @($runtimeAssembly, $editorAssembly, $runtimeReference, $editorReference)
    sourceHashes = @($sourceHashes)
    unityTestFrameworkRun = $false
    reason = 'Unity Editor remained open. This check compiled C# and read PE metadata only; the separate isolated GPU diagnostic used no NUnit runner.'
    manualFixtures = @('VividRP.Editor.Tests.VirtualShadowMapSamplingTests', 'VividRP.Editor.Tests.CascadedShadowSettingsVolumeTests', 'VividRP.Editor.Tests.VSMBaselineRecorderTests')
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'csharp-validation.json') -Encoding utf8
Write-Output ('C# compiler exit=' + $compilerExit + '; current Unity assembly bindings=' + $bindingsMatch + '; warnings=' + $warnings.Count)
if (-not $bindingsMatch) { exit 2 }
exit $compilerExit
