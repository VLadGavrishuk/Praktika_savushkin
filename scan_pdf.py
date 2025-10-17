import fitz  # PyMuPDF
import json
import os

INPUT_PDF = "input/pdfff.pdf"
OUTPUT_JSON = "output/element_locations.json"
OUTPUT_LINES = "output/line_segments.json"

def is_inside_title_block(x, y):
    return (
            y > 790 or y < 20 or
            x < 20 or x > 1140
    )


def extract_lines_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    all_lines = []

    for page_num, page in enumerate(doc):
        drawings = page.get_drawings()
        for item in drawings:
            for path in item["items"]:
                if path[0] == "l":
                    p1, p2 = path[1], path[2]

                    if is_inside_title_block(p1[0], p1[1]) and is_inside_title_block(p2[0], p2[1]):
                        continue

                    all_lines.append({
                        "page": page_num + 1,
                        "x1": round(p1[0], 2),
                        "y1": round(p1[1], 2),
                        "x2": round(p2[0], 2),
                        "y2": round(p2[1], 2)
                    })

    return all_lines


def is_valid_element(text):
    return any(char.isdigit() for char in text) and ('_' in text or '-' in text)


def extract_all_text_positions(pdf_path):
    doc = fitz.open(pdf_path)
    positions = {}

    for page_num, page in enumerate(doc):
        words = page.get_text("words")
        for word in words:
            text = word[4]
            if is_valid_element(text):
                x0, y0, x1, y1 = word[:4]
                center_x = (x0 + x1) / 2
                center_y = (y0 + y1) / 2

                if is_inside_title_block(center_x, center_y):
                    continue

                positions.setdefault(text, []).append({
                    "page": page_num + 1,
                    "x": round(center_x, 2),
                    "y": round(center_y, 2)
                })
    return positions


def main():
    print("🔎 Сканирование PDF на предмет всех объектов...")
    positions = extract_all_text_positions(INPUT_PDF)

    os.makedirs("output", exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(positions, f, indent=2, ensure_ascii=False)

    print(f"✅ Найдено {len(positions)} уникальных объекта(-ов).")
    print(f"💾 Координаты сохранены в {OUTPUT_JSON}")

    print("📐 Извлечение линий из PDF...")
    lines = extract_lines_from_pdf(INPUT_PDF)
    with open(OUTPUT_LINES, "w", encoding="utf-8") as f:
        json.dump(lines, f, indent=2, ensure_ascii=False)
    print(f"✅ Найдено {len(lines)} графических линий. Сохранено в {OUTPUT_LINES}")


if __name__ == "__main__":
    main()
