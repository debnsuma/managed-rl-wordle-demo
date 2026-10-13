"""Generate a QR code SVG for the preview sign-up link (or any link).

    uv run --no-project --with "qrcode[pil]==8.2" python tools/make_qr.py https://example.com/preview
    uv run --no-project --with "qrcode[pil]==8.2" python tools/make_qr.py https://example.com/preview --name qr-preview

Writes assets/<name>.svg (default qr-preview). Then put the same URL in config.js as previewUrl.
"""
import argparse, pathlib
import qrcode, qrcode.image.svg

p = argparse.ArgumentParser(); p.add_argument("url"); p.add_argument("--name", default="qr-preview")
a = p.parse_args()
out = pathlib.Path(__file__).resolve().parents[1] / "assets" / f"{a.name}.svg"
qrcode.make(a.url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M).save(str(out))
print("wrote", out, "->", a.url)
