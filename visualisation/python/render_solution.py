#!/usr/bin/env python3
import argparse
import json
from PIL import Image, ImageDraw

def parse_solution(solution_path):
    buildings = []
    with open(solution_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            # on attend: ["b=1", "type=0", "x=12", "y=7", "r=2"]
            if len(parts) < 5:
                continue
            try:
                b_type = int(parts[1].split('=')[1])
                x = int(parts[2].split('=')[1])
                y = int(parts[3].split('=')[1])
                r_cp = int(parts[4].split('=')[1])  # rayon du CP
                buildings.append((x, y, b_type, r_cp))
            except (IndexError, ValueError):
                continue
    return buildings


# ---------- export JSON pour Houdini ----------
 

def save_json(buildings, json_path):
    data = []
    for i, (x, y, b_type, r_cp) in enumerate(buildings):
        data.append({
            "id": i,
            "type_id": b_type,
            "x": x,
            "y": y,
            "radius": r_cp,
        })

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

# ---------- rendu image  ----------

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

    for (x, y, b_type, r_cp) in buildings:
        # coordonnées sur l'image upscalée
        px = int((x - 1) * scale)
        py = int((y - 1) * scale)

        # rayon visuel en pixels : lié au rayon CP
        r = max(1, int(r_cp * scale))  # * scale pour garder la même échelle que la grille

        color = type_color.get(b_type, (255, 0, 255))
        bbox = (px, py, px + r, py + r)
        draw.rectangle(bbox, outline=color, fill=color)

    img.save(output_path)
    print(f"Image sauvegardée dans {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Rendu de la solution MiniZinc sur la carte couleur + export JSON"
    )
    parser.add_argument("--input", "-i", required=True,
                        help="Fichier solution MiniZinc (.dzn/.txt)")
    parser.add_argument("--output", "-o", required=True,
                        help="Image de sortie (.png)")
    parser.add_argument("--json-output", "-j",
                        help="(Optionnel) Fichier JSON de sortie pour Houdini")
    args = parser.parse_args()

    buildings = parse_solution(args.input)
    print(f"{len(buildings)} bâtiments lus depuis {args.input}")

    # nouveau : JSON si demandé
    if args.json_output is not None:
        save_json(buildings, args.json_output)

    # rendu image comme avant
    draw_solution(buildings, args.output)


if __name__ == "__main__":
    main()
