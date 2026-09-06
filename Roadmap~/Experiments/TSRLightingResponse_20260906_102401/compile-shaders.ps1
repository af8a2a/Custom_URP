param(
    [string]$PackageRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path,
    [string]$CoreRoot = 'E:/VividRP_Reborn/Packages/CoreRP'
)
$ErrorActionPreference = 'Stop'
$outputDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ('tsr-lighting-dxc-' + [Guid]::NewGuid().ToString('N'))
$includePackages = Join-Path $outputDirectory 'Packages'
New-Item -ItemType Directory -Path $includePackages -Force | Out-Null
New-Item -ItemType Junction -Path (Join-Path $includePackages 'com.vivid.render-pipelines') -Target $PackageRoot | Out-Null
New-Item -ItemType Junction -Path (Join-Path $includePackages 'com.unity.render-pipelines.core') -Target $CoreRoot | Out-Null
$results = foreach ($shaderName in @('TSRRejectShading','TSRUpdateHistory','TSRReprojectHistory')) {
    $sourcePath = Join-Path $PackageRoot ('Shaders/Core/Private/TSR/' + $shaderName + '.compute')
    foreach ($wave in 0,1) { foreach ($half in 0,1) {
        $name = $shaderName + '_wave' + $wave + '_half' + $half
        $arguments = @('-T','cs_6_2','-E','CS','-D','SHADER_API_D3D11=1','-D','UNITY_COMPILER_DXC=1','-enable-16bit-types','-Wno-conversion','-I',$outputDirectory,'-Fo',(Join-Path $outputDirectory ($name+'.dxil')))
        if ($wave) { $arguments += @('-D','VIVID_TSR_WAVE_OPS=1') }
        if ($half) { $arguments += @('-D','UNITY_DEVICE_SUPPORTS_NATIVE_16BIT=1') }
        & dxc @arguments $sourcePath *> (Join-Path $outputDirectory ($name+'.log'))
        [ordered]@{ variant = $name; exitCode = $LASTEXITCODE; sourceSha256 = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash }
    } }
}
[ordered]@{ checkedUtc = [DateTime]::UtcNow.ToString('o'); outputDirectory = $outputDirectory; results = @($results) } |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'dxc-validation.json') -Encoding utf8
$results | ConvertTo-Json -Depth 3
if (@($results | Where-Object { $_.exitCode -ne 0 }).Count -ne 0) { exit 1 }
