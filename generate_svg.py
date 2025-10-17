import os
import json

INPUT_POSITIONS = "output/element_locations.json"
INPUT_LINES = "output/line_segments.json"
PARSED_LUA_FILE = "output/parsed_lua.json"
OUTPUT_SVG = "output/controls_overview.svg"
ASSETS_DIR = "assets"

OFFSET_X = 200
OFFSET_Y = 200

SVG_HEADER = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="1600" height="1600" xmlns="http://www.w3.org/2000/svg" version="1.1">
  <rect width="100%" height="100%" fill="white"/>
'''

SVG_FOOTER = '</svg>'


def detect_type(name):
    name = name.upper()
    if "_IN" in name:
        return "input"
    elif "_OUT" in name:
        return "output"
    elif name.startswith("M") or "-M" in name:
        return "pump"
    elif name.startswith("V") or "-V" in name:
        return "valve"
    elif any(prefix in name for prefix in ["LS", "PS", "TS"]) or "-LS" in name:
        return "sensor"
    elif name.startswith("-") and name[1:].isdigit():
        return "line_id"
    elif any(word in name for word in ["WASH", "МОЙКА", "FLUSH", "CLEAN"]):
        return "wash"
    else:
        return "generic"


def load_svg_icon(type_name):
    filepath = os.path.join(ASSETS_DIR, f"{type_name}.svg")
    if not os.path.exists(filepath):
        print(f"⚠️  SVG-файл для '{type_name}' не найден: {filepath}")
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    inner = content.replace("\n", "")
    inner = inner.split(">", 1)[1].rsplit("</svg>", 1)[0]
    return inner


def draw_legend():
    lines = [
        '<g transform="translate(20, 20)">',
        '<text x="0" y="0" font-size="16" font-weight="bold">Обозначения:</text>'
    ]
    y_offset = 25
    legend_items = [
        ("input", "Вход (Input)"),
        ("output", "Выход (Output)"),
        ("pump", "Насос (Pump)"),
        ("valve", "Клапан (Valve)"),
        ("sensor", "Датчик (Sensor)"),
        ("line_id", "Линия/номер (Line ID)"),
        ("wash", "Мойка/Очистка (Wash)"),
        ("generic", "Общее / Неопределено (Generic)"),
    ]

    for type_id, label in legend_items:
        icon = load_svg_icon(type_id)
        if icon:
            lines.append(f'<g transform="translate(0, {y_offset})">')
            lines.append(f'<g transform="scale(0.5)">{icon}</g>')
            lines.append(f'<text x="60" y="25" font-size="12">{label}</text>')
            lines.append('</g>')
            y_offset += 55

    lines.append('</g>')
    return "\n".join(lines)


def build_descr_index(lua_data):
    index = {}
    for _block_name, value in lua_data.items():
        items = value if isinstance(value, list) else [value]
        for props in items:
            if not isinstance(props, dict):
                continue
            descr = props.get("descr")
            if not descr:
                continue
            key = str(descr).upper()
            index.setdefault(key, []).append(props)
    return index


def _pick_type_from_props_list(props_list, fallback_name):
    for props in reversed(props_list):
        t = props.get("type")
        if t:
            return t
    return detect_type(fallback_name)


def _collect_values(props_list, key):
    seen = set()
    out = []
    for p in props_list:
        if not isinstance(p, dict):
            continue
        if key in p and p[key] is not None:
            val = str(p[key])
            if val not in seen:
                seen.add(val)
                out.append(val)
    return " | ".join(out)


def create_svg(positions, line_segments, lua_data):
    svg_parts = [SVG_HEADER]
    svg_parts.append(draw_legend())

    descr_index = build_descr_index(lua_data)
    unclassified = []
    EXCLUDE_NAMES = {"BR1-МСА6"}

    print("🔍 Отображаемые объекты в SVG:")
    for name, coords_list in positions.items():
        if name in EXCLUDE_NAMES:
            print(f"  ⏩ Пропускаем {name} (исключено из отображения)")
            continue

        if not coords_list:
            print(f"  ⚠️  {name} координаты не найдены")
            continue

        lua_infos = descr_index.get(name.upper(), [])

        if lua_infos:
            el_type = _pick_type_from_props_list(lua_infos, name)
        else:
            el_type = detect_type(name)

        icon_svg = load_svg_icon(el_type)

        tooltip_parts = [f"Тип: {el_type}"]
        if lua_infos:
            for key in ["port", "tag", "unit", "id"]:
                v = _collect_values(lua_infos, key)
                if v:
                    tooltip_parts.append(f"{key}: {v}")
            if len(lua_infos) > 1:
                tooltip_parts.append(f"совпадений: {len(lua_infos)}")
        tooltip = " • ".join(tooltip_parts)

        if el_type == "generic":
            unclassified.append(name)

        for coords in coords_list:
            x = coords["x"] + OFFSET_X
            y = coords["y"] + OFFSET_Y

            if icon_svg:
                svg_parts.append(f'<g transform="translate({x},{y}) scale(0.5)">')
                svg_parts.append(f'<title>{tooltip}</title>')
                svg_parts.append(icon_svg)
                svg_parts.append('</g>')
            else:
                # Если нет SVG-иконки
                svg_parts.append(f'<circle cx="{x}" cy="{y}" r="10" fill="gray" stroke="black">')
                svg_parts.append(f'<title>{tooltip}</title>')
                svg_parts.append('</circle>')

            svg_parts.append(f'<text x="{x + 25}" y="{y - 5}" font-size="14">{name}</text>')
            print(f"  ✅ {name} → ({x}, {y}) [{el_type}]")

    if unclassified:
        print(f"\n⚠️ Найдено {len(unclassified)} объектов типа 'generic':")
        for u in unclassified:
            print(f"   - {u}")

    for line in line_segments:
        x1 = line["x1"] + OFFSET_X
        y1 = line["y1"] + OFFSET_Y
        x2 = line["x2"] + OFFSET_X
        y2 = line["y2"] + OFFSET_Y
        svg_parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="#888" stroke-width="1"/>'
        )

    svg_parts.append(SVG_FOOTER)
    return "\n".join(svg_parts)


def main():
    with open(INPUT_POSITIONS, "r", encoding="utf-8") as f:
        positions = json.load(f)

    with open(INPUT_LINES, "r", encoding="utf-8") as f:
        line_segments = json.load(f)

    with open(PARSED_LUA_FILE, "r", encoding="utf-8") as f:
        lua_data = json.load(f)

    os.makedirs("output", exist_ok=True)
    print("🖼 Генерация SVG с иконками и данными из Lua...")

    svg_content = create_svg(positions, line_segments, lua_data)

    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"✅ SVG сохранён в {OUTPUT_SVG}")


if __name__ == "__main__":
    main()
