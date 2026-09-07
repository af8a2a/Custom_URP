param(
    [string]$PackageRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path,
    [string]$CoreRoot = 'E:/VividRP_Reborn/Packages/CoreRP',
    [string]$Dxc = 'dxc',
    [string]$OutputDirectory,
    [switch]$ListOnly
)
$ErrorActionPreference = 'Stop'
$sources = @(
    'Shaders/Core/Private/CSMShadowResolve.compute',
    'Tests/Editor/RenderPass/Shadows/VirtualShadowMapSamplingTests.compute'
)
$entries = @(foreach ($source in $sources) {
    foreach ($line in Get-Content -LiteralPath (Join-Path $PackageRoot $source)) {
        if ($line -match '^\s*#pragma\s+multi_compile') {
            throw "New multi_compile directive requires an explicit variant matrix: $source : $line"
        }
        if ($line -notmatch '^\s*#pragma\s+kernel\s+(.+)$') { continue }
        $parts = (($Matches[1] -split '//', 2)[0].Trim()) -split '\s+'
        [pscustomobject]@{ source = $source; kernel = $parts[0]; defines = @($parts | Select-Object -Skip 1) }
    }
})
if ($ListOnly) { $entries | ConvertTo-Json -Depth 5; return }
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $PSScriptRoot ('validation-' + [DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss_fff') + '/shaders')
}
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path
$includeRoot = Join-Path $OutputDirectory 'include'
$includePackages = Join-Path $includeRoot 'Packages'
New-Item -ItemType Directory -Path $includePackages -Force | Out-Null
foreach ($alias in @('com.vivid.render-pipelines', 'VividRP', 'com.af8a2a.vividrp')) {
    New-Item -ItemType Junction -Path (Join-Path $includePackages $alias) -Target $PackageRoot | Out-Null
}
New-Item -ItemType Junction -Path (Join-Path $includePackages 'com.unity.render-pipelines.core') -Target $CoreRoot | Out-Null
$compiler = (Get-Command $Dxc -ErrorAction Stop).Source
function Get-ShaderSnapshot {
    # Hash the complete include trees, but compile only the two requested shader files.
    $files = @(Get-ChildItem -LiteralPath (Join-Path $PackageRoot 'Shaders') -Recurse -File |
        Where-Object { $_.Extension -in @('.hlsl', '.compute', '.shader') })
    $files += @(Get-ChildItem -LiteralPath (Join-Path $CoreRoot 'ShaderLibrary') -Recurse -File |
        Where-Object { $_.Extension -in @('.hlsl', '.compute', '.shader') })
    $files += Get-Item -LiteralPath (Join-Path $PackageRoot $sources[1])
    @(foreach ($file in $files | Sort-Object FullName -Unique) {
        [ordered]@{ path = $file.FullName; sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash }
    })
}
$before = Get-ShaderSnapshot
$before | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'source-sha256-before.json') -Encoding utf8
$results = @(foreach ($entry in $entries) {
    $stem = [IO.Path]::GetFileNameWithoutExtension($entry.source) + '.' + $entry.kernel
    $log = Join-Path $OutputDirectory ($stem + '.log')
    $object = Join-Path $OutputDirectory ($stem + '.dxil')
    $arguments = @('-T', 'cs_6_2', '-E', $entry.kernel, '-D', 'SHADER_API_D3D11=1',
        '-D', 'UNITY_COMPILER_DXC=1', '-enable-16bit-types', '-Wno-conversion', '-I', $includeRoot, '-Fo', $object)
    foreach ($define in $entry.defines) { $arguments += @('-D', $define) }
    $arguments += Join-Path $PackageRoot $entry.source
    & $compiler @arguments *> $log
    $compilerExit = $LASTEXITCODE
    [ordered]@{
        source = $entry.source; kernel = $entry.kernel; defines = $entry.defines
        arguments = $arguments; exitCode = $compilerExit; log = $log
        dxilSha256 = $(if ($compilerExit -eq 0) { (Get-FileHash -LiteralPath $object -Algorithm SHA256).Hash } else { $null })
    }
})
$after = Get-ShaderSnapshot
$after | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'source-sha256-after.json') -Encoding utf8
$stable = ($before | ConvertTo-Json -Depth 4 -Compress) -ceq ($after | ConvertTo-Json -Depth 4 -Compress)
$report = [ordered]@{
    checkedUtc = [DateTime]::UtcNow.ToString('o'); packageRoot = $PackageRoot; coreRoot = $CoreRoot
    compiler = $compiler; compilerSha256 = (Get-FileHash -LiteralPath $compiler -Algorithm SHA256).Hash
    profile = 'cs_6_2'; shaderApi = 'SHADER_API_D3D11'; unityCompilerDxc = $true
    scope = 'All direct pragma kernel entries, including inline defines. Related receiver GPU tests are in VirtualShadowMapSamplingTests.compute.'
    sourceTreeStable = $stable; total = $results.Count
    passed = @($results | Where-Object { $_.exitCode -eq 0 }).Count; results = $results
    unityTestFrameworkRun = $false; gpuDispatchRun = $false
}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'dxc-validation.json') -Encoding utf8
$report | ConvertTo-Json -Depth 8
if (-not $stable -or @($results | Where-Object { $_.exitCode -ne 0 }).Count -ne 0) { exit 1 }
