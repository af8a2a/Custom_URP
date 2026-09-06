"""Build the disposable 1024-comparison receiver reference from shipping sources."""
from hashlib import sha256
from pathlib import Path
import json
import re

package = Path('E:/VividRP_Reborn/Packages/VividRP')
source_path = package / 'Shaders/Core/Private/CSMShadowResolve.compute'
debug_path = package / 'Shaders/Core/Private/VSMReceiverDebug.hlsl'
output_path = package / 'Shaders/Core/Private/VSMStochasticReference.compute'
source_bytes = source_path.read_bytes()
debug_bytes = debug_path.read_bytes()
source = source_bytes.decode('utf-8-sig').replace('\r\n', '\n')
debug = debug_bytes.decode('utf-8-sig').replace('\r\n', '\n')

def replace_once(text, old, new):
    assert text.count(old) == 1, (old[:100], text.count(old))
    return text.replace(old, new, 1)

source, count = re.subn(r'^#pragma kernel .+\n', '', source, flags=re.MULTILINE)
assert count == 22, count
source = '#pragma kernel VSMReceiverDebug VIVID_VSM_RECEIVER_DEBUG\n' + source
old = '''        uint seed = GetVSMStochasticSeed(pixel, (uint)_CSMFrameIndex);
        float stochasticSum = 0.0;
        [unroll]
        for (uint sampleIndex = 0u; sampleIndex < 9u; sampleIndex++)
        {
            float2 sampleOffset = VSMStochasticDiskSample(seed, sampleIndex);'''
new = '''        // Probe only: deterministic 32 x 32 equal-area polar midpoint reference.
        float stochasticSum = 0.0;
        [loop]
        for (uint sampleIndex = 0u; sampleIndex < 1024u; sampleIndex++)
        {
            float radius = sqrt(((float)(sampleIndex / 32u) + 0.5) * (1.0 / 32.0));
            float angle = ((float)(sampleIndex % 32u) + 0.5) * (kPCSSTwoPi / 32.0);
            float sine, cosine;
            sincos(angle, sine, cosine);
            float2 sampleOffset = radius * float2(cosine, sine);'''
source = replace_once(source, old, new)
source = replace_once(source, 'shadow = stochasticSum * (1.0 / 9.0);',
                      'shadow = stochasticSum * (1.0 / 1024.0);')
debug = replace_once(debug, 'int _VSMReceiverDebugMode;',
                     'int _VSMReceiverDebugMode;\nint2 _VSMReferenceOffset;')
debug = replace_once(debug,
    '''    if (id.x >= (uint)_CSMOutputWidth || id.y >= (uint)_CSMOutputHeight) return;
    uint2 pixel = id.xy;''',
    '''    int2 pixelCoord = int2(id.xy);
    pixelCoord += _VSMReferenceOffset.xy;
    if (any(pixelCoord < 0) || pixelCoord.x >= _CSMOutputWidth
        || pixelCoord.y >= _CSMOutputHeight) return;
    uint2 pixel = (uint2)pixelCoord;''')
source = replace_once(source, '#include "VSMReceiverDebug.hlsl"', debug.rstrip())
output_path.write_text(source, encoding='utf-8', newline='\n')
manifest = {
    'production_sha256': sha256(source_bytes).hexdigest(),
    'debug_sha256': sha256(debug_bytes).hexdigest(),
    'reference_sha256': sha256(output_path.read_bytes()).hexdigest(),
    'reference_path': str(output_path),
    'kernel': 'VSMReceiverDebug',
    'sample_count': 1024,
    'sampling': '32 equal-area radial bands x 32 angular sectors, midpoint',
    'uniform': '_VSMReferenceOffset int2, native screen pixels',
    'output_dimensions': 'Keep _CSMOutputWidth/Height and textures at actual full dimensions.',
    'dispatch': 'ceil(roiWidth/8), ceil(roiHeight/8), 1; crop rounded-up workgroup fringe.',
}
manifest_path = Path(__file__).with_name('reference-manifest.json')
manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
