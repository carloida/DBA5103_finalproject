"""Split the EDA poster at complete chart-card boundaries for phone sharing."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/citibike_eda/whatsapp'
OUT.mkdir(parents=True, exist_ok=True)
poster = Image.open(ROOT / 'output/pdf/CitiBike_EDA_WhatsApp_Poster.png').convert('RGB')
BG, INK, TEAL = '#edf3f7', '#132e43', '#75dacf'
font_dir = Path('C:/Windows/Fonts')
def font(size, bold=False):
    return ImageFont.truetype(str(font_dir / ('arialbd.ttf' if bold else 'arial.ttf')), size)

# This column stays clear of text and plots, so white runs locate complete cards.
runs = []
start = None
for y in range(poster.height):
    white = poster.getpixel((55, y)) == (255, 255, 255)
    if white and start is None:
        start = y
    if start is not None and (not white or y == poster.height - 1):
        if y - start > 200:
            runs.append((start - 16, y + 16))
        start = None
assert len(runs) == 13, runs
groups = [
    (0, 4, 'The data + how people ride', '106,617 September-start trips | 108 local origin stations'),
    (4, 8, 'Where the bikes end up', 'Trip duration, station balance, network boundaries + peak reversals'),
    (8, 11, 'Why timing matters', 'Hourly changes, inventory pressure + day-to-day variation'),
    (11, 13, 'What we can do with this', 'Popular routes, forecasting + inputs for our business case'),
]
for part, (first, last, title, subtitle) in enumerate(groups, 1):
    top = runs[first][0]
    bottom = runs[last - 1][1] if part < 4 else poster.height
    crop = poster.crop((0, top, poster.width, bottom))
    header_h = 320
    image = Image.new('RGB', (1200, crop.height + header_h + 80), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1200, header_h - 24), fill=INK)
    draw.text((54, 30), f'CITI BIKE EDA  /  {part} OF 4', font=font(30, True), fill=TEAL)
    draw.text((54, 88), title, font=font(54, True), fill='white')
    draw.text((54, 170), 'Jersey City + Hoboken | September 2026', font=font(34), fill='white')
    draw.text((54, 225), subtitle, font=font(28), fill='#c8d9e7')
    assert draw.textlength(subtitle, font=font(28)) < 1092
    image.paste(crop, (0, header_h))
    draw = ImageDraw.Draw(image)
    draw.text((54, image.height - 54), f'{part}/4  |  Local trip CSV + EDA tables  |  Charts {first+1:02}-{last:02}',
              font=font(26), fill=INK)
    image.save(OUT / f'CitiBike_EDA_{part}_of_4.png', optimize=True)
    print(f'Part {part}: {image.width} x {image.height}')
    preview = image.copy()
    preview.thumbnail((600, 2300))
    preview.save(ROOT / f'tmp/pdfs/citibike_poster/split_review_{part}.png')
