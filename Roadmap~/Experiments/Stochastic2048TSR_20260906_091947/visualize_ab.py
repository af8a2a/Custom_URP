"""Exact-pixel VSM A/B previews. No retouching or per-image normalization."""
from pathlib import Path
import gzip
import json
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'visuals'
OUT.mkdir(exist_ok=True)
ROI = (700, 170, 420, 410)
REGIONS = {'roof': (735, 190, 380, 70), 'ledge': (715, 485, 390, 80)}
BG = (17, 21, 27)
FG = (229, 234, 241)
MUTED = (170, 181, 196)
FONT = 'C:/Windows/Fonts/segoeui.ttf'
FONTS = {s: ImageFont.truetype(FONT, s) for s in (16, 18, 21, 25)}
SCALE = 2


def frames(variant, scenario):
    directory = ROOT / (variant + '_' + scenario)
    status = (directory / 'status.txt').read_text().strip()
    assert status.startswith('complete'), (directory, status)
    records = [json.loads(line) for line in (directory / 'frames.jsonl').read_text().splitlines() if line.strip()]
    return directory, records


def load(directory, prefix, name):
    channels = 1 if name in ('shadow', 'accept') else 4
    dtype = '<f4' if name.startswith('debug') or name == 'reference' else '<f2'
    raw = gzip.decompress((directory / f'{prefix}_{name}.bin.gz').read_bytes())
    a = np.frombuffer(raw, dtype=dtype).reshape(ROI[3], ROI[2], channels)
    return a[::-1].astype(np.float32)


def crop(a, region):
    x, y, w, h = region
    return a[y-ROI[1]:y-ROI[1]+h, x-ROI[0]:x-ROI[0]+w]


def gray(a):
    a = np.repeat(a[..., :1], 3, axis=-1)
    return Image.fromarray(np.round(np.clip(a, 0, 1) * 255).astype(np.uint8))


def hdr_preview(a):
    # One fixed mapping for every variant, buffer and frame; no fitted exposure.
    rgb = np.maximum(np.nan_to_num(a[..., :3]), 0)
    rgb = rgb / (1 + rgb)
    rgb = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * rgb ** (1/2.4) - 0.055)
    return Image.fromarray(np.round(np.clip(rgb, 0, 1) * 255).astype(np.uint8))


def draw_text(image, xy, label, size=18, color=FG):
    ImageDraw.Draw(image).text(xy, label, font=FONTS[size], fill=color)


def aligned_records(scenario):
    left, lf = frames('tent', scenario)
    right, rf = frames('stochastic9', scenario)
    assert len(lf) == len(rf)
    for a, b in zip(lf, rf):
        for key in ('step', 'phase', 'jitter', 'cameraPosition', 'cameraEuler', 'lightEuler'):
            assert a[key] == b[key], (scenario, a['step'], key, a[key], b[key])
    return left, right, lf, rf


def static_panels():
    left, right, lf, rf = aligned_records('static')
    images = []
    for directory, records in ((left, lf), (right, rf)):
        last = records[-1]['prefix']
        accum = np.zeros((ROI[3], ROI[2], 1), np.float32)
        for frame in records:
            accum += load(directory, frame['prefix'], 'shadow')
        images.append({
            'raw': load(directory, last, 'shadow'),
            'mean': accum / len(records),
            'source': load(directory, last, 'source'),
            'output': load(directory, last, 'output'),
            'screen': Image.open(directory / 'last.png').convert('RGB'),
        })

    for name, region in REGIONS.items():
        x, y, w, h = region
        cell_w, cell_h = w*SCALE, h*SCALE
        gap, border, row_header = 16, 16, 30
        width = cell_w*2 + gap + border*2
        row_span = cell_h + row_header + 10
        canvas = Image.new('RGB', (width, 118 + 5*row_span + 52), BG)
        draw_text(canvas, (border, 12), f'2048 VSM | {name} | native ({x},{y}) {w}x{h} | 2x nearest-neighbor', 25)
        draw_text(canvas, (border, 49), 'Tent 3x3 continuous weights', 21)
        draw_text(canvas, (border+cell_w+gap, 49), 'Stochastic disk | 9 comparisons', 21)
        draw_text(canvas, (border, 83), 'Same camera, light and jitter phase at each step; PCF + density + NativeAA TSR enabled.', 16, MUTED)
        labels = [
            ('raw', 'Raw shadow | single frame 47 | grayscale 0..1'),
            ('mean', 'Raw shadow | mean of 48 screen frames | camera jitter retained'),
            ('source', 'TSR input | frame 47 | fixed HDR preview mapping'),
            ('output', 'TSR output | frame 47 | same fixed HDR preview mapping'),
            ('screen', 'Actual final screenshot | last.png | original display colors'),
        ]
        for row, (key, label) in enumerate(labels):
            top = 118 + row*row_span
            draw_text(canvas, (border, top), label, 18)
            for column, data in enumerate(images):
                if key == 'screen':
                    im = data[key].crop((x, y, x+w, y+h))
                elif key in ('raw', 'mean'):
                    im = gray(crop(data[key], region))
                else:
                    im = hdr_preview(crop(data[key], region))
                canvas.paste(im.resize((cell_w, cell_h), Image.Resampling.NEAREST), (border+column*(cell_w+gap), top+row_header))
        draw_text(canvas, (border, canvas.height-44), 'HDR preview: max(c,0)/(1+max(c,0)), then sRGB. Shared fixed mapping, no exposure/contrast fitting.', 16, MUTED)
        draw_text(canvas, (border, canvas.height-23), 'Raw shadow: 0=shadow, 1=lit. The 48-frame screen mean is a temporal visualization, not a ground-truth reference.', 16, MUTED)
        canvas.save(OUT / f'static_{name}.png', optimize=True)

    # Context is an original screenshot crop, not an HDR reconstruction.
    canvas = Image.new('RGB', (1712, 930), BG)
    draw_text(canvas, (16, 12), '2048 VSM | actual final screenshot ROI | 2x nearest-neighbor', 25)
    for column, (data, title) in enumerate(zip(images, ('Tent', 'Stochastic 9'))):
        xpos = 16 + column*848
        draw_text(canvas, (xpos, 50), title, 21)
        im = data['screen'].crop((ROI[0], ROI[1], ROI[0]+ROI[2], ROI[1]+ROI[3])).resize((840, 820), Image.Resampling.NEAREST)
        canvas.paste(im, (xpos, 86))
        painter = ImageDraw.Draw(canvas)
        for label, (x, y, w, h) in REGIONS.items():
            rect = (xpos+(x-ROI[0])*2, 86+(y-ROI[1])*2, xpos+(x-ROI[0]+w)*2-1, 86+(y-ROI[1]+h)*2-1)
            painter.rectangle(rect, outline=(244, 186, 78), width=2)
            draw_text(canvas, (rect[0]+4, rect[1]+3), label, 16, (255,220,135))
    canvas.save(OUT / 'static_context.png', optimize=True)


def temporal_gif(scenario):
    left, right, lf, rf = aligned_records(scenario)
    region = REGIONS['ledge']
    x, y, w, h = region
    cell_w, cell_h = w*SCALE, h*SCALE
    gap, border, row_header = 16, 16, 28
    width = cell_w*2+gap+border*2
    height = 122+3*(cell_h+row_header+8)+50
    rendered = []
    for step, (a, b) in enumerate(zip(lf, rf)):
        canvas = Image.new('RGB', (width, height), BG)
        draw_text(canvas, (border, 10), f'2048 VSM | {scenario} | step {step:02d}/{len(lf)-1} | {a["phase"]} | ledge 2x', 25)
        draw_text(canvas, (border, 46), 'Tent 3x3', 21)
        draw_text(canvas, (border+cell_w+gap, 46), 'Stochastic disk | 9 comparisons', 21)
        draw_text(canvas, (border, 79), '100 ms per captured step; 6x slower than nominal 60 Hz. Offline replay, not measured runtime.', 18, MUTED)
        for row, (key, label) in enumerate((('shadow', 'Raw shadow | fixed grayscale 0..1'), ('source', 'TSR input | fixed HDR preview'), ('output', 'TSR output | same fixed HDR preview'))):
            top = 118+row*(cell_h+row_header+8)
            draw_text(canvas, (border, top), label, 18)
            for column, (directory, record) in enumerate(((left, a), (right, b))):
                arr = crop(load(directory, record['prefix'], key), region)
                im = gray(arr) if key == 'shadow' else hdr_preview(arr)
                canvas.paste(im.resize((cell_w, cell_h), Image.Resampling.NEAREST), (border+column*(cell_w+gap), top+row_header))
        draw_text(canvas, (border, height-41), 'HDR: max(c,0)/(1+max(c,0)), then sRGB; identical mapping throughout. GIF uses one shared palette; no dithering.', 16, MUTED)
        draw_text(canvas, (border, height-21), 'Matched discrete camera/light steps and camera jitter. Motion/lighting sequence is replayed from captured buffers.', 16, MUTED)
        rendered.append(canvas)
    # One palette across all frames prevents an adaptive palette from adding temporal changes.
    thumb_w, thumb_h = 400, max(1, int(height*400/width))
    palette_source = Image.new('RGB', (thumb_w*8, thumb_h*((len(rendered)+7)//8)), BG)
    for i, frame in enumerate(rendered):
        palette_source.paste(frame.resize((thumb_w, thumb_h), Image.Resampling.NEAREST), ((i%8)*thumb_w, (i//8)*thumb_h))
    palette = palette_source.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    sequence = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in rendered]
    sequence[0].save(OUT / f'{scenario}_ledge_6x.gif', save_all=True, append_images=sequence[1:], duration=100, loop=0, optimize=False, disposal=2)
    # Lossless PNG anchors let the reviewer check any apparent GIF-palette changes.
    for index in ([15,16,17,24,63,95] if scenario == 'light_step' else [0,31,63,64,95]):
        rendered[index].save(OUT / f'{scenario}_step_{index:02d}.png', optimize=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--static-only', action='store_true')
    args = parser.parse_args()
    static_panels()
    if not args.static_only:
        temporal_gif('light_step')
        temporal_gif('camera')
    description = {
        'roi': ROI,
        'regions': REGIONS,
        'format': 'little-endian half or float, gzip, flipped vertically per layout.txt',
        'raw_shadow_mapping': 'linear grayscale [0,1], no range fitting',
        'hdr_preview_mapping': 'max(c,0)/(1+max(c,0)), then standard sRGB; fixed for all images and frames',
        'final_screenshot': 'original last.png RGB crop, no color transform',
        'spatial_scaling': '2x nearest-neighbor, no smoothing or sharpening',
        'temporal_scaling': 'one 100ms GIF frame per captured discrete step; 6x versus nominal60Hz, not timing evidence',
        'gif_palette': 'single shared 256-color palette across all frames, dithering disabled; PNG anchors are lossless',
        'alignment_checked': 'same step, phase, camera position/euler, light euler and camera jitter in both variants',
        'static_mean': '48 raw screen frames, camera jitter retained; not a high-sample reference',
    }
    (OUT/'visualization-method.json').write_text(json.dumps(description, indent=2), encoding='utf-8')
    print('\n'.join(str(path) for path in sorted(OUT.iterdir())))


if __name__ == '__main__':
    main()
