import os
import json
import argparse
try:
    import numpy as np
    import cv2
except Exception:
    np = None
    cv2 = None
    print("Warning: OpenCV (cv2) or numpy not available; auto ROI detection disabled.")
from PIL import Image


"""
Hough-based grid cropping
------------------------------------------
Purpose
- Robustly detect an icon grid in a screenshot page and crop it into rows×cols tiles (mostly 7x12).

Method (OpenCV primitives)
- Preprocess: convert RGB to grayscale and apply a light Gaussian blur to stabilize edges.
- Edge detection: run Canny to extract potential straight-line edges.
- Line detection: use Probabilistic Hough Transform (HoughLinesP) to detect line segments.
- Classification: separate near-horizontal vs near-vertical segments by slope.
- Position sets: sort and de-duplicate positions into ordered lists of horizontal (cy) and vertical (cx) line coordinates.
- Even-spacing window: select a continuous window of rows+1 horizontals and cols+1 verticals whose adjacent spacings have minimal variance (regular grid assumption).
- ROI: define top/bottom from the chosen horizontals and left/right from the chosen verticals; apply small horizontal padding.
"""

def _detect_roi_hough(img: Image.Image, rows: int, cols: int) -> tuple[int, int, int, int] | None:
    # Preprocess: stabilize edges
    if cv2 is None or np is None:
        return None
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    h, w = gray.shape
    # Edge detection + probabilistic Hough lines
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180.0, threshold=90, minLineLength=max(40, w // 10), maxLineGap=8)
    if lines is None or len(lines) == 0:
        return None
    # Separate near-vertical and near-horizontal segments by slope
    xs = []
    ys = []
    for l in lines[:, 0, :]:
        x1, y1, x2, y2 = int(l[0]), int(l[1]), int(l[2]), int(l[3])
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        if dx < dy * 0.2:
            xs.append(x1)
            xs.append(x2)
        if dy < dx * 0.2:
            ys.append(y1)
            ys.append(y2)
    # Sort and de-duplicate positions
    xs.sort()
    ys.sort()
    xtol = max(4, int(w * 0.01))
    ytol = max(4, int(h * 0.01))
    cx = []
    for v in xs:
        if not cx or abs(v - cx[-1]) > xtol:
            cx.append(v)
    cy = []
    for v in ys:
        if not cy or abs(v - cy[-1]) > ytol:
            cy.append(v)
    if len(cy) < 2 or len(cx) < 2:
        return None
    # Pick evenly spaced window of lines (rows+1 / cols+1)
    def _best_window(vals, need):
        # In an ordered line-position array, find a continuous window of length (need+1)
        # whose adjacent spacing variance is minimal — closest to an evenly spaced grid
        if len(vals) < need + 1:
            return None
        best = None
        for i in range(0, len(vals) - need):
            seg = vals[i:i + need + 1]
            diffs = [seg[k + 1] - seg[k] for k in range(len(seg) - 1)]
            m = np.mean(diffs)
            v = np.var(diffs)
            best = (v, m, i) if best is None or v < best[0] else best
        return best
    hy = _best_window(cy, rows)
    hx = _best_window(cx, cols)
    # Compute ROI from selected windows
    if hy is not None:
        idx_h = hy[2]
        top = cy[idx_h]
        bottom = min(cy[idx_h + rows], h)
        m_h = max(1, int(round((bottom - top) / rows)))
    else:
        m_h = int(np.median([cy[i + 1] - cy[i] for i in range(len(cy) - 1)]))
        top = min(cy)
        bottom = min(top + rows * max(1, m_h), h)
    if hx is not None:
        idx_x = hx[2]
        left = cx[idx_x]
        right = min(cx[idx_x + cols], w)
        m_w = max(1, int(round((right - left) / cols)))
    else:
        m_w = int(np.median([cx[i + 1] - cx[i] for i in range(len(cx) - 1)]))
        left = min(cx)
        right = min(left + cols * max(1, m_w), w)
    # Small horizontal padding
    pad_x = max(2, int(w * 0.005))
    left = max(0, left - pad_x)
    right = min(w, right + pad_x)
    return left, top, right, bottom


def crop_grid(image_path: str, rows: int, cols: int, out_dir: str, page: int | None = None, margin: int = 4, auto_roi: bool = True, save_roi_preview: bool = True):
    img = Image.open(image_path).convert("RGB")
    if auto_roi:
        roi_h = _detect_roi_hough(img, rows, cols)
        if roi_h is None:
            raise RuntimeError("Hough ROI detection failed (cv2/np missing or insufficient lines)")
        rx0, ry0, rx1, ry1 = roi_h
        img_roi = img.crop((rx0, ry0, rx1, ry1))
        base_x, base_y = rx0, ry0
    else:
        img_roi = img
        base_x, base_y = 0, 0
    if save_roi_preview:
        os.makedirs(out_dir, exist_ok=True)
        img_roi.save(os.path.join(out_dir, "roi_preview.png"))
    w, h = img_roi.size
    cell_w = w // cols
    cell_h = h // rows
    os.makedirs(out_dir, exist_ok=True)
    meta = {"image": image_path, "rows": rows, "cols": cols, "page": page, "roi": [base_x, base_y, base_x + w, base_y + h], "tiles": []}
    for r in range(rows):
        for c in range(cols):
            x0 = max(c * cell_w - margin, 0)
            y0 = max(r * cell_h - margin, 0)
            x1 = min((c + 1) * cell_w + margin, w)
            y1 = min((r + 1) * cell_h + margin, h)
            tile = img_roi.crop((x0, y0, x1, y1))
            fname = f"tile_r{r}_c{c}.png"
            tile.save(os.path.join(out_dir, fname))
            bx0, by0, bx1, by1 = base_x + x0, base_y + y0, base_x + x1, base_y + y1
            meta["tiles"].append({"row": r, "col": c, "bbox": [bx0, by0, bx1, by1], "file": fname})
    with open(os.path.join(out_dir, "tiles_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("image")
    p.add_argument("--rows", type=int, default=7)
    p.add_argument("--cols", type=int, default=12)
    p.add_argument("--out")
    p.add_argument("--page", type=int)
    p.add_argument("--margin", type=int, default=4)
    args = p.parse_args()
    out_dir = args.out
    if not out_dir or out_dir.strip() == "":
        base_dir = os.path.dirname(os.path.abspath(args.image))
        base_name = os.path.splitext(os.path.basename(args.image))[0]
        out_dir = os.path.join(base_dir, f"{base_name}_crops_hough")
    crop_grid(args.image, args.rows, args.cols, out_dir, args.page, args.margin, auto_roi=True, save_roi_preview=True)
    print("Saved to", out_dir)


if __name__ == "__main__":
    main()
