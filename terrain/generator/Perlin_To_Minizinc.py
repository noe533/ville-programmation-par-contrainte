from PIL import Image
import argparse
import numpy as np
from collections import deque

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
q1, q2, q3 = np.quantile(data, [0.1, 0.55, 0.9])

terrain[data < q1] = 0          # eau
terrain[(data >= q1) & (data < q2)] = 1   # plaine
terrain[(data >= q2) & (data < q3)] = 2   # forêt
terrain[data >= q3] = 3         # montagne

# 3) BFS générique pour calculer la distance Manhattan à un type de cases
def bfs_distance(mask):
    INF = H + W
    dist = np.full((H, W), INF, dtype=int)
    q = deque()

    # cases de départ : les cellules qui matchent le mask
    for y in range(H):
        for x in range(W):
            if mask[y, x]:
                dist[y, x] = 0
                q.append((y, x))

    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    while q:
        y, x = q.popleft()
        for dy, dx in dirs:
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W:
                if dist[ny, nx] > dist[y, x] + 1:
                    dist[ny, nx] = dist[y, x] + 1
                    q.append((ny, nx))
    return dist

# 4) Distances aux ressources importantes : eau et forêt
# après avoir calculé terrain, H, W et défini bfs_distance(...)

is_water    = (terrain == 0)
is_forest   = (terrain == 2)
is_mountain = (terrain == 3)

distWater  = bfs_distance(is_water)
distForest = bfs_distance(is_forest)

# distance "to bad" = distance jusqu'à une case eau OU montagne
bad_mask      = (terrain == 0) | (terrain == 3)
distanceToBad = bfs_distance(bad_mask)


# 5) Écrire le .dzn (terrain + distWater + distForest)
vals_terrain = ", ".join(str(int(v)) for v in terrain.flatten())
vals_water   = ", ".join(str(int(v)) for v in distWater.flatten())
vals_forest  = ", ".join(str(int(v)) for v in distForest.flatten())
vals_bad     = ", ".join(str(int(v)) for v in distanceToBad.flatten())

with open(args.output, "w") as f:
    f.write(f"int: W = {W};\n")
    f.write(f"int: H = {H};\n\n")

    f.write("array[1..W, 1..H] of int: terrain = array2d(1..W, 1..H,\n[\n")
    f.write("  " + vals_terrain + "\n]);\n\n")

    f.write("array[1..W, 1..H] of int: distWater = array2d(1..W, 1..H,\n[\n")
    f.write("  " + vals_water + "\n]);\n\n")

    f.write("array[1..W, 1..H] of int: distForest = array2d(1..W, 1..H,\n[\n")
    f.write("  " + vals_forest + "\n]);\n\n")

    f.write("array[1..W, 1..H] of int: distanceToBad = array2d(1..W, 1..H,\n[\n")
    f.write("  " + vals_bad + "\n]);\n")

# 6) Image couleur pour debug
colors = {
    0: (10, 10, 10),     # eau
    1: (80, 80, 80),     # plaine
    2: (90, 90, 90),  # forêt
    3: (240, 240, 240),  # montagne
}

img_dbg = np.zeros((H, W, 3), dtype=np.uint8)
for y in range(H):
    for x in range(W):
        img_dbg[y, x] = colors[int(terrain[y, x])]

Image.fromarray(img_dbg).save("images/processed/terrain_colored.png")
