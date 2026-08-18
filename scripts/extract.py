#!/usr/bin/env python3
"""把 Google Slides API 回傳的簡報 JSON 攤平成 data/slides.json（版面座標 + 文字）"""
import json, os

RAW = "data/raw/deck.json"


def text_of(shape):
    txt = shape.get("text")
    if not txt:
        return ""
    return "".join(te.get("textRun", {}).get("content", "")
                   for te in txt.get("textElements", []))


def walk(elements, out, dx=0, dy=0, sx=1.0, sy=1.0):
    """遞迴展開群組，累積父層的位移與縮放"""
    for el in elements:
        tr = el.get("transform", {})
        ex = tr.get("translateX", 0) or 0
        ey = tr.get("translateY", 0) or 0
        esx = tr.get("scaleX", 1) or 1
        esy = tr.get("scaleY", 1) or 1
        x = dx + ex * sx
        y = dy + ey * sy
        nsx, nsy = sx * esx, sy * esy

        if "elementGroup" in el:
            walk(el["elementGroup"].get("children", []), out, x, y, nsx, nsy)
            continue

        size = el.get("size", {})
        w = abs((size.get("width", {}).get("magnitude", 0) or 0) * nsx)
        h = abs((size.get("height", {}).get("magnitude", 0) or 0) * nsy)

        if "shape" in el:
            t = text_of(el["shape"]).strip()
            if t:
                out.append({"y": int(y), "x": int(x), "w": int(w), "h": int(h), "t": t})
        elif "table" in el:
            for row in el["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    t = "".join(te.get("textRun", {}).get("content", "")
                                for te in cell.get("text", {}).get("textElements", [])).strip()
                    if t:
                        out.append({"y": int(y), "x": int(x), "w": int(w), "h": int(h), "t": t})


def main():
    doc = json.load(open(RAW, encoding="utf-8"))
    slides = []
    for i, s in enumerate(doc.get("slides", [])):
        boxes = []
        walk(s.get("pageElements", []), boxes)
        pics = sum(1 for el in s.get("pageElements", []) if "image" in el)
        boxes.sort(key=lambda b: (b["y"], b["x"]))
        slides.append({"i": i, "pics": pics, "boxes": boxes})

    os.makedirs("data", exist_ok=True)
    json.dump(slides, open("data/slides.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"攤平 {len(slides)} 頁，"
          f"文字框合計 {sum(len(s['boxes']) for s in slides)}，"
          f"無文字頁 {sum(1 for s in slides if not s['boxes'])}")


if __name__ == "__main__":
    main()
