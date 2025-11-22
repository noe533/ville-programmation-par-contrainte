from PIL import Image
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", required=True)
parser.add_argument("--output", "-o", required=True)
args = parser.parse_args()

# 1) Lire l'image réduite (grayscale)
img = Image.open(args.input).convert("L")
data = np.array(img)
H, W = data.shape

# 2) Discrétiser en types de terrain
# 0 = eau, 1 = plaine, 2 = forêt, 3 = montagne
terrain = np.zeros_like(data, dtype=int)
q1, q2, q3 = np.quantile(data, [0.15, 0.5, 0.6])

terrain[data < q1] = 0                          # eau
terrain[(data >= q1) & (data < q2)] = 1         # plaine
terrain[(data >= q2) & (data < q3)] = 2         # forêt
terrain[data >= q3] = 3                         # montagne

# 3) Écrire le .dzn (terrain seulement)
vals_terrain = ", ".join(str(int(v)) for v in terrain.flatten())

with open(args.output, "w") as f:
    f.write(f"int: W = {W};\n")
    f.write(f"int: H = {H};\n\n")

    f.write("array[1..W, 1..H] of int: terrain = array2d(1..W, 1..H,\n[\n")
    f.write("  " + vals_terrain + "\n]);\n")

# 4) Image grayscale pour Houdini (heightmap 8-bit)
colors = {
    0: (10, 10, 10),      # eau  (très bas)
    1: (80, 80, 80),      # plaine
    2: (90, 90, 90),      # forêt (un peu plus haut)
    3: (240, 240, 240),   # montagne (très haut)
}

img_dbg = np.zeros((H, W, 3), dtype=np.uint8)
for y in range(H):
    for x in range(W):
        img_dbg[y, x] = colors[int(terrain[y, x])]

Image.fromarray(img_dbg).save("images/processed/terrain_colored.png")
