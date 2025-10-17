import os
import re
import json

INPUT_DIR = "input"
OUTPUT_FILE = "parsed_lua.json"


def parse_lua_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    block_pattern = re.compile(r"(\w+)\s*=\s*\{(.*?)\}", re.DOTALL)
    prop_pattern = re.compile(r'(\w+)\s*=\s*(?:"(.*?)"|([^\s,]+))')

    blocks = {}

    for match in block_pattern.finditer(content):
        block_name = match.group(1)
        body = match.group(2)

        props = {}
        for key, val1, val2 in prop_pattern.findall(body):
            value = val1 if val1 else val2
            props[key] = try_convert(value)

        if block_name in blocks:
            if isinstance(blocks[block_name], list):
                blocks[block_name].append(props)
            else:
                blocks[block_name] = [blocks[block_name], props]
        else:
            blocks[block_name] = props

    return blocks


def try_convert(val):
    if val.isdigit():
        return int(val)
    try:
        return float(val)
    except ValueError:
        return val


def parse_all_lua(input_dir):
    all_blocks = {}
    for fname in os.listdir(input_dir):
        if fname.endswith(".lua"):
            path = os.path.join(input_dir, fname)
            blocks = parse_lua_file(path)

            for key, val in blocks.items():
                if key in all_blocks:
                    if isinstance(all_blocks[key], list):
                        if isinstance(val, list):
                            all_blocks[key].extend(val)
                        else:
                            all_blocks[key].append(val)
                    else:
                        if isinstance(val, list):
                            all_blocks[key] = [all_blocks[key]] + val
                        else:
                            all_blocks[key] = [all_blocks[key], val]
                else:
                    all_blocks[key] = val

    return all_blocks


def main():
    blocks = parse_all_lua(INPUT_DIR)
    os.makedirs("output", exist_ok=True)
    with open(os.path.join("output", OUTPUT_FILE), "w", encoding="utf-8") as f:
        json.dump(blocks, f, indent=2, ensure_ascii=False)
    print(f"✅ Разобрано {len(blocks)} уникальных блоков. Результат сохранен в output/{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
