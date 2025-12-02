import argparse
import json
from PIL import Image, ImageDraw
from affichage2D import sizeX, sizeY

def parse_solution(solution_path):
    last_block = []
    current_block = []

    with open(solution_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            
            if line.startswith("----------") or line.startswith("====="):
                if current_block:
                    last_block = current_block
                    current_block = []
                continue

            if not line.startswith("b="):
                continue

            parts = line.split()
            if len(parts) < 4:
                continue

            try:
                b_type = int(parts[1].split('=')[1])
                x = int(parts[2].split('=')[1])
                y = int(parts[3].split('=')[1])
                current_block.append((x, y, b_type))
            except (IndexError, ValueError):
                continue

    if current_block:
        last_block = current_block

    return last_block



def save_json(buildings, json_path):
    data = []
    for i, (x, y, b_type) in enumerate(buildings):
        w = sizeX[b_type]
        h = sizeY[b_type]

        center_x = x + w / 2.0 - 0.5
        center_y = y + h / 2.0 - 0.5

        data.append({
            "id": i,
            "type_id": b_type,
            "x": center_x,
            "y": center_y
        })

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)



def draw_solution(buildings, output_path,
                  terrain_image="images/processed/terrain_colored.png",
                  final_size=800):
    base_img = Image.open(terrain_image).convert("RGB")
    w0, h0 = base_img.size
    scale = final_size / max(w0, h0)
    new_width = int(w0 * scale)
    new_height = int(h0 * scale)

    img = base_img.resize((new_width, new_height), Image.NEAREST)
    draw = ImageDraw.Draw(img)

    type_color = {
        0: (255, 0, 0),
        1: (255, 255, 255),
        2: (0, 0, 0),
    }

    for (x, y, b_type) in buildings:
        
        px = int((x - 1) * scale)
        py = int((y - 1) * scale)

        
        r = max(1, int(2 * scale))

        color = type_color.get(b_type, (255, 0, 255))
        bbox = (px - r, py - r, px + r, py + r)
        draw.rectangle(bbox, outline=color, fill=color)

    img.save(output_path)
    print(f"Image sauvegardée dans {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Rendu de la solution MiniZinc sur la carte couleur + export JSON"
    )
    parser.add_argument("--input", "-i", required=False,
                        help="Fichier solution MiniZinc (.dzn/.txt)")
    parser.add_argument("--output", "-o", required=False,
                        help="Image de sortie (.png)")
    parser.add_argument("--json-output", "-j",
                        help="(Optionnel) Fichier JSON de sortie pour Houdini")
    args = parser.parse_args()

    buildings = parse_solution(args.input)

    if args.json_output is not None:
        save_json(buildings, args.json_output)

    if args.output is not None:
        draw_solution(buildings, args.output)

if __name__ == "__main__":
    main()
