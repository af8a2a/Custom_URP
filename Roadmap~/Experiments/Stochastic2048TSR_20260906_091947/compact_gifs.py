"""Small native-pixel version of the full-resolution VSM comparison replay."""
import json
import visualize_ab as v
from PIL import Image

descriptions = {}
for scenario in ('light_step', 'camera'):
    left, right, lf, rf = v.aligned_records(scenario)
    indices = list(range(12, 49)) if scenario == 'light_step' else list(range(0, 64, 2))
    duration = 100 if scenario == 'light_step' else 200
    frames = []
    for step in indices:
        a, b = lf[step], rf[step]
        im = Image.new('RGB', (816, 454), v.BG)
        v.draw_text(im, (10, 8), f'2048 VSM | {scenario} | step {step:02d}/95 ({a["phase"]}) | 1:1 pixels', 18)
        v.draw_text(im, (10, 36), 'Tent 3x3', 18)
        v.draw_text(im, (418, 36), 'Stochastic disk (9)', 18)
        for row, (kind, title) in enumerate((('shadow', 'Raw shadow [0,1]'), ('source', 'TSR input | fixed HDR preview'), ('output', 'TSR output | same fixed HDR preview'))):
            top = 64+row*108
            v.draw_text(im, (10, top), title, 16)
            for col, (directory, record) in enumerate(((left,a), (right,b))):
                data = v.crop(v.load(directory, record['prefix'], kind), v.REGIONS['ledge'])
                img = v.gray(data) if kind == 'shadow' else v.hdr_preview(data)
                im.paste(img, (10+col*408, top+24))
        sequence_label = 'Steps 12..48, every step; 100ms per frame.' if scenario == 'light_step' else 'Steps 0..62, every other step; 200ms per frame.'
        v.draw_text(im, (10, 389), sequence_label, 16, v.MUTED)
        v.draw_text(im, (10, 411), '6x vs nominal60Hz; offline replay, not runtime measurement.', 16, v.MUTED)
        v.draw_text(im, (10, 433), 'HDR: c/(1+c) then sRGB. Same mapping; fixed GIF palette, no dithering.', 16, v.MUTED)
        frames.append(im)
    samples = Image.new('RGB', (816*4, 454*((len(frames)+3)//4)))
    for i, frame in enumerate(frames):
        samples.paste(frame, ((i%4)*816, (i//4)*454))
    palette = samples.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    path = v.OUT / f'{scenario}_compact_6x.gif'
    indexed[0].save(path, save_all=True, append_images=indexed[1:], duration=duration, loop=0, optimize=False, disposal=2)
    descriptions[path.name] = {'native_pixel_scale': 1, 'crop': v.REGIONS['ledge'], 'displayed_steps': indices, 'frame_duration_ms': duration, 'frame_count': len(frames), 'rows': ['raw shadow', 'TSR input', 'TSR output'], 'bytes': path.stat().st_size}
    print(path, path.stat().st_size)

(v.OUT / 'compact-gif-method.json').write_text(json.dumps(descriptions, indent=2), encoding='utf-8')
