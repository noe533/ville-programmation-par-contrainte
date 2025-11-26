from PIL import Image
import argparse
import numpy as np
import heapq
from collections import deque



BLOCK_SPACING = 60         # distance (px) entre rues secondaires majeures
BUILDABLE_RADIUS = 15       # tolérance (px) pour considérer qu’une zone est assez large/plate
CITY_EXPAND_RADIUS = 6     # expansion (px) des zones larges avant de placer un quartier
CITY_MIN_SIZE = 200        # nombre de pixels min pour transformer une composante en quartier
COAST_TOLERANCE = 2        # épaisseur (px) autorisant une route collée à l’eau/relief
COAST_COST = 30.0          # coût des cellules côtières
INF = 1e9
ROAD = 1
LOCAL_STREET_SPACING = 44  # distance (px) des rues internes pour garder de la place aux bâtiments
LOCAL_INSET = 6            # marge (px) pour ne pas coller ces rues internes aux bords du quartier
ROAD_THICKEN = 2           # rayon de dilation pour épaissir les routes (0 pour garder fin)

parser = argparse.ArgumentParser()
parser.add_argument("--input", "-i", required=True)
parser.add_argument("--output", "-o", required=True)
args = parser.parse_args()

# Lecture et discretisation
data = np.array(Image.open(args.input).convert("L"))
H, W = data.shape
terrain = np.zeros_like(data, dtype=int)
q1, q2, q3 = np.quantile(data, [0.15, 0.5, 0.6])
terrain[data < q1] = 0
terrain[(data >= q1) & (data < q2)] = 1
terrain[(data >= q2) & (data < q3)] = 2
terrain[data >= q3] = 3
passable = (terrain == 1) | (terrain == 2)


def neighbors(y, x):
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W:
            yield ny, nx


def compute_wide_buildable(mask, radius):
    wide = np.zeros_like(mask, dtype=bool)
    for y in range(H):
        y0, y1 = max(0, y - radius), min(H - 1, y + radius)
        for x in range(W):
            x0, x1 = max(0, x - radius), min(W - 1, x + radius)
            block = mask[y0:y1 + 1, x0:x1 + 1]
            if np.all(block):
                wide[y, x] = True
    return wide


def dilate(mask, radius):
    out = np.zeros_like(mask, dtype=bool)
    for y in range(H):
        y0, y1 = max(0, y - radius), min(H - 1, y + radius)
        for x in range(W):
            x0, x1 = max(0, x - radius), min(W - 1, x + radius)
            if mask[y0:y1 + 1, x0:x1 + 1].any():
                out[y, x] = True
    return out


def build_cost(terrain, passable, wide_mask):
    cost = np.full_like(terrain, INF, dtype=float)
    cost[passable] = np.where(terrain[passable] == 1, 8.0, 12.0)
    cost[(wide_mask) & (terrain == 1)] = 1.5
    cost[(wide_mask) & (terrain == 2)] = 3.5
    cost[(~wide_mask) & passable] *= 2.5
    near_passable = np.zeros_like(passable, dtype=bool)
    for y in range(H):
        for x in range(W):
            if passable[y, x]:
                continue
            for dy in range(-COAST_TOLERANCE, COAST_TOLERANCE + 1):
                for dx in range(-COAST_TOLERANCE, COAST_TOLERANCE + 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and passable[ny, nx]:
                        near_passable[y, x] = True
                        break
                if near_passable[y, x]:
                    break
    coastal = near_passable & (cost >= INF)
    cost[coastal] = COAST_COST
    roadable = passable | coastal
    return cost, roadable


def astar(cost, start, goal):
    if cost[start] >= INF or cost[goal] >= INF:
        return []
    sy, sx = start
    gy, gx = goal
    open_set = []
    gscore = {(sy, sx): 0.0}

    def heuristic(y, x):
        return abs(y - gy) + abs(x - gx)

    heapq.heappush(open_set, (heuristic(sy, sx), sy, sx))
    came_from = {}

    while open_set:
        _, y, x = heapq.heappop(open_set)
        if (y, x) == (gy, gx):
            path = [(y, x)]
            while (y, x) in came_from:
                y, x = came_from[(y, x)]
                path.append((y, x))
            return list(reversed(path))
        for ny, nx in neighbors(y, x):
            if cost[ny, nx] >= INF:
                continue
            g_new = gscore[(y, x)] + cost[ny, nx]
            if (ny, nx) not in gscore or g_new < gscore[(ny, nx)]:
                gscore[(ny, nx)] = g_new
                came_from[(ny, nx)] = (y, x)
                heapq.heappush(open_set, (g_new + heuristic(ny, nx), ny, nx))
    return []

def draw_grid(road, mask, y0, y1, x0, x1, spacing):
    for x in range(x0, x1 + 1):
        if mask[y0, x]:
            road[y0, x] = ROAD
        if mask[y1, x]:
            road[y1, x] = ROAD
    for y in range(y0, y1 + 1):
        if mask[y, x0]:
            road[y, x0] = ROAD
        if mask[y, x1]:
            road[y, x1] = ROAD
    x = x0 + spacing
    while x < x1:
        for y in range(y0, y1 + 1):
            if mask[y, x]:
                road[y, x] = ROAD
        x += spacing
    y = y0 + spacing
    while y < y1:
        for x in range(x0, x1 + 1):
            if mask[y, x]:
                road[y, x] = ROAD
        y += spacing


def find_components(mask):
    visited = np.zeros_like(mask, dtype=bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if not mask[y, x] or visited[y, x]:
                continue
            q = deque([(y, x)])
            visited[y, x] = True
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for ny, nx in neighbors(cy, cx):
                    if mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        q.append((ny, nx))
            comps.append(cells)
    return comps


def add_city_grids(road, mask, spacing):
    centers = []
    for cells in find_components(mask):
        if len(cells) < CITY_MIN_SIZE:
            continue
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        centers.append((sum(ys) // len(ys), sum(xs) // len(xs)))
    return centers


def add_local_streets(road, mask, spacing, inset):
    for cells in find_components(mask):
        if len(cells) < CITY_MIN_SIZE:
            continue
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1 = min(ys) + inset, max(ys) - inset
        x0, x1 = min(xs) + inset, max(xs) - inset
        if y1 - y0 < spacing or x1 - x0 < spacing:
            continue
        draw_grid(road, mask, y0, y1, x0, x1, spacing)


def connect_mst(road, centers, cost):
    if len(centers) < 2:
        return
    connected = {0}
    while len(connected) < len(centers):
        best = None
        for i in connected:
            for j in range(len(centers)):
                if j in connected:
                    continue
                d = abs(centers[i][0] - centers[j][0]) + abs(centers[i][1] - centers[j][1])
                if best is None or d < best[0]:
                    best = (d, i, j)
        _, i, j = best
        for y, x in astar(cost, centers[i], centers[j]):
            road[y, x] = ROAD
        connected.add(j)


def connect_to_network(road, centers, seeds, cost):
    network = list(seeds)
    for c in centers:
        if any(c == s for s in network):
            continue
        nearest = min(network, key=lambda s: abs(c[0] - s[0]) + abs(c[1] - s[1]))
        for y, x in astar(cost, c, nearest):
            road[y, x] = ROAD
        network.append(c)


def best_edge_candidate(cost, side, margin):
    best = None
    for y in range(H):
        for d in range(margin):
            x = d if side == "left" else W - 1 - d
            if cost[y, x] >= INF:
                continue
            score = cost[y, x] + d * 0.5
            if best is None or score < best[0]:
                best = (score, y, x)
    return best


def thicken_mask(mask, radius, limit_mask=None):
    if radius <= 0:
        return mask
    thick = mask.copy()
    for _ in range(radius):
        expanded = thick.copy()
        for y in range(H):
            for x in range(W):
                if thick[y, x]:
                    continue
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and thick[ny, nx]:
                        expanded[y, x] = True
                        break
        thick = expanded
    if limit_mask is not None:
        thick &= limit_mask
    return thick


# Construction des masques et coûts
wide_mask = compute_wide_buildable(passable, BUILDABLE_RADIUS)
city_mask = dilate(wide_mask, CITY_EXPAND_RADIUS) & passable
cost, roadable_mask = build_cost(terrain, passable, wide_mask)
road = np.zeros_like(terrain, dtype=int)

# Route principale gauche-droite
main_road = []
lb = best_edge_candidate(cost, "left", margin=5)
rb = best_edge_candidate(cost, "right", margin=5)
if lb and rb:
    main_road = astar(cost, (lb[1], lb[2]), (rb[1], rb[2]))
    for y, x in main_road:
        road[y, x] = ROAD

# Grilles de ville + connexions
city_centers = add_city_grids(road, city_mask, BLOCK_SPACING)
connect_mst(road, city_centers, cost)
seeds = main_road if main_road else city_centers[:1]
connect_to_network(road, city_centers, seeds, cost)
# Rues internes moins denses pour laisser la place aux bâtiments
add_local_streets(road, city_mask, LOCAL_STREET_SPACING, LOCAL_INSET)

# Clamp + épaississement optionnel
road[~roadable_mask] = 0
if ROAD_THICKEN > 0:
    road = thicken_mask(road.astype(bool), ROAD_THICKEN, limit_mask=roadable_mask).astype(int)

# Export MiniZinc
vals_terrain = ", ".join(str(int(v)) for v in terrain.flatten())
vals_road = ", ".join(str(int(v)) for v in road.flatten())
with open(args.output, "w") as f:
    f.write(f"int: W = {W};\nint: H = {H};\n\n")
    f.write("array[1..W, 1..H] of int: terrain = array2d(1..W, 1..H,\n[\n")
    f.write("  " + vals_terrain + "\n]);\n\n")
    f.write("array[1..W, 1..H] of int: isRoad = array2d(1..W, 1..H,\n[\n")
    f.write("  " + vals_road + "\n]);\n")

# Image debug
colors = {0: (10, 10, 10), 1: (80, 80, 80), 2: (90, 90, 90), 3: (240, 240, 240)}
img_dbg = np.zeros((H, W, 3), dtype=np.uint8)
for y in range(H):
    for x in range(W):
        img_dbg[y, x] = colors[int(terrain[y, x])]
        if road[y, x] == ROAD:
            img_dbg[y, x] = (255, 0, 0)
Image.fromarray(img_dbg).save("images/processed/terrain_colored.png")
