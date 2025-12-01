import matplotlib.pyplot as plt
import numpy as np
import re
import matplotlib.patches as patches
import random

def random_color():
    return (random.random(), random.random(), random.random())

# ===============================================================
# 1) Lecteur du fichier des bâtiments
# ===============================================================

def read_buildings(filename):
    buildings = []
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("-"):
                continue

            # format :  b=1 type=0 x=96 y=3
            parts = line.split()
            b_id = int(parts[0].split("=")[1])
            t    = int(parts[1].split("=")[1])
            x    = int(parts[2].split("=")[1])
            y    = int(parts[3].split("=")[1])

            buildings.append((b_id, t, x, y))
    return buildings


# ===============================================================
# 2) Lecteur d’un fichier .dzn du terrain + auto-orientation
# ===============================================================

def read_dzn_terrain(filename, buildings=None, verbose=False):
    """
    Lit le .dzn et retourne W, H, terrain, isRoad.
    Si `buildings` (liste de tuples (bid,type,x,y)) est fourni, on choisit l'orientation
    (deux manières possibles d'interpréter l'array2d linéaire) qui minimise les conflits
    bâtiments <-> routes. Sinon on renvoie l'orientation A par défaut mais affiche
    des informations utiles si verbose=True.
    """
    with open(filename, "r") as f:
        data = f.read()

    # extrait W et H
    mW = re.search(r"int:\s*W\s*=\s*(\d+)", data)
    mH = re.search(r"int:\s*H\s*=\s*(\d+)", data)
    if not mW or not mH:
        raise ValueError("Impossible de trouver W et H dans " + filename)
    W = int(mW.group(1))
    H = int(mH.group(1))

    def extract_array(name):
        pat = rf"array\[1\.\.W, 1\.\.H\] of int: {name} = array2d\(1\.\.W, 1\.\.H,\s*\[(.*?)\]\);"
        m = re.search(pat, data, re.S)
        if not m:
            raise ValueError(f"Pas trouvé {name} dans {filename}")
        raw = m.group(1)
        vals = [int(x) for x in raw.replace("\n", " ").split(",") if x.strip()]
        if len(vals) != W * H:
            raise ValueError(f"Longueur inattendue pour {name} : {len(vals)} != {W}*{H}")
        return np.array(vals)

    terrain_vals = extract_array("terrain")
    isroad_vals  = extract_array("isRoad")

    # Deux interprétations possibles (produisant des tableaux shape (H,W))
    # A) reshape((W,H)).T  => équivalent à transposer la notion MiniZinc(x,y)
    # B) reshape((H,W))    => si l'ordre linéaire était déjà par lignes
    tA = terrain_vals.reshape((W, H)).T.copy()
    tB = terrain_vals.reshape((H, W)).copy()
    rA = isroad_vals.reshape((W, H)).T.copy()
    rB = isroad_vals.reshape((H, W)).copy()

    if verbose:
        print(f"[read_dzn_terrain] W={W}, H={H}")
        print(f"  isRoad: sum A={int(rA.sum())}, sum B={int(rB.sum())}")

    def count_conflicts(tarr, rarr):
        if buildings is None:
            # heuristique simple : choisir l'orientation avec le plus de routes non-null
            return int(rarr.sum())
        conflicts = 0
        for (bid, tpe, bx, by) in buildings:
            x0 = bx - 1; y0 = by - 1
            # safe: si types sizeX/sizeY inconnus on risque erreur; on compte hors-map comme conflit fort
            try:
                sx = sizeX[tpe]; sy = sizeY[tpe]
            except Exception:
                # si type inconnu, on ignore ce bâtiment dans le test
                continue
            x_start = max(0, x0); x_end = min(W, x0 + sx)
            y_start = max(0, y0); y_end = min(H, y0 + sy)
            if x_start >= x_end or y_start >= y_end:
                conflicts += 1000
                continue
            sub = rarr[y_start:y_end, x_start:x_end]
            conflicts += int(sub.sum())
        return conflicts

    # Si buildings fourni on minimise le nombre de cases route sous les bâtiments;
    # sinon on choisit orientation A (mais on affiche les deux si verbose)
    ca = count_conflicts(tA, rA)
    cb = count_conflicts(tB, rB)

    if buildings is not None:
        if ca <= cb:
            chosen_t, chosen_r, label = tA, rA, "A"
        else:
            chosen_t, chosen_r, label = tB, rB, "B"
        if verbose:
            print(f"[read_dzn_terrain] orientation choisie = {label} (conflits A={ca}, B={cb})")
    else:
        # pas de bâtiments fournis : on conserve A (raison : cohérence avec MiniZinc habituel)
        chosen_t, chosen_r, label = tA, rA, "A"
        if verbose:
            print("[read_dzn_terrain] aucun buildings fourni -> orientation A par défaut")

    return W, H, chosen_t, chosen_r


# ===============================================================
# Dimensions réelles des bâtiments (indexées par type)
# (garde exactement tes listes existantes)
# ===============================================================

sizeX = [
    14, # 0 Sky_big
    13, # 1 Sky_small
    18, # 2 House_01
    18, # 3 House_02
    16, # 4 Residential
    17, # 5 House_03
    16, # 6 Factory
    6,  # 7 Windmill
    18, # 8 Auto Service
    14, # 9 Bakery
    7,  # 10 Bar
    12, # 11 Books Shop
    11, # 12 Chicken Shop
    12, # 13 Clothing
    19, # 14 Coffee Shop
    11, # 15 Drug Store
    11, # 16 Fast Food
    12, # 17 Fruits Shop
    13, # 18 Gas Station
    11, # 19 Gift Shop
    24  # 20 Super Market
]

sizeY = [
    12, # 0 Sky_big
    13, # 1 Sky_small
    13, # 2 House_01
    13, # 3 House_02
    13, # 4 Residential
    14, # 5 House_03
    28, # 6 Factory
    2,  # 7 Windmill
    8,  # 8 Auto Service
    11, # 9 Bakery
    7,  # 10 Bar
    12, # 11 Books Shop
    10, # 12 Chicken Shop
    12, # 13 Clothing
    12, # 14 Coffee Shop
    11, # 15 Drug Store
    10, # 16 Fast Food
    12, # 17 Fruits Shop
    26, # 18 Gas Station
    11, # 19 Gift Shop
    13  # 20 Super Market
]


# couleurs terrain
terrain_colors = {
    0: [0.2, 0.4, 1.0],   # eau (bleu)
    1: [1.0, 0.9, 0.2],   # plaine (jaune)
    2: [0.2, 0.8, 0.2],   # forêt (vert)
    3: [0.7, 0.7, 0.7],   # montagne (gris clair)
}

road_color = [0.2, 0.2, 0.2]          # gris foncé
building_colors = {0: [1,0.4,0.4], 6: [0.8,0.2,1.0]}


# ===============================================================
# 4) Affichage final (mode debug disponible)
# ===============================================================

def draw_map(buildings, W, H, terrain, isRoad, debug=False):
    """
    Affiche la carte.
    Si debug=True : dessine le contour de chaque bâtiment (blanc) et en rouge
    ceux qui chevauchent des cases route. Retourne la liste des bâtiments en conflit.
    """
    img = np.zeros((H, W, 3))

    # Terrain + routes
    for y in range(H):
        for x in range(W):
            img[y, x] = terrain_colors.get(int(terrain[y, x]), [1, 0, 1])
            if int(isRoad[y, x]) == 1:
                img[y, x] = road_color

    if not debug:
        plt.figure(figsize=(8, 8))
        plt.imshow(img, origin='lower')
        plt.axis("off")
        plt.title("Carte générée")
        plt.show()
        return []

    # debug = True : on trace contours des batiments
    fig, ax = plt.subplots(figsize=(10,10))
    ax.imshow(img, origin='lower', interpolation='nearest')
    ax.set_axis_off()
    ax.set_title("Carte (debug) : bâtiments en contours, conflits en rouge")

    bad_buildings = []
    for (bid, tpe, bx, by) in buildings:
        # tailles par type
        sx = sizeX[tpe]
        sy = sizeY[tpe]

        # conversion 1-based (MiniZinc) -> 0-based (Python)
        x0 = bx - 1
        y0 = by - 1

        # bornes (clip pour rester dans l'image)
        x_start = max(0, x0)
        x_end   = min(W, x0 + sx)   # exclusive
        y_start = max(0, y0)
        y_end   = min(H, y0 + sy)   # exclusive

        # rectangle blanc pour tous les batiments
        rect = patches.Rectangle((x_start, y_start), x_end - x_start, y_end - y_start,
                                 linewidth=1.0, edgecolor='white', facecolor='none')
        ax.add_patch(rect)

        # vérif collisions route
        if x_start < x_end and y_start < y_end:
            sub = isRoad[y_start:y_end, x_start:x_end]
            if sub.sum() > 0:
                bad_buildings.append((bid, tpe, bx, by, int(sub.sum())))
                # rectangle rouge plus épais en cas de conflit
                rect_conf = patches.Rectangle((x_start, y_start), x_end - x_start, y_end - y_start,
                                              linewidth=1.5, edgecolor='red', facecolor='none')
                ax.add_patch(rect_conf)

        # remplissage visuel du bâtiment (couleur unique aléatoire)
        rand_color = (random.random(), random.random(), random.random(), 0.80)
        patch_fill = patches.Rectangle((x_start, y_start),
                                       x_end - x_start,
                                       y_end - y_start,
                                       linewidth=0,
                                       facecolor=rand_color)
        ax.add_patch(patch_fill)

    plt.show()

    return bad_buildings


# ===============================================================
# 5) EXECUTION (fichiers codés en dur)
# ===============================================================

if __name__ == "__main__":
    buildings_file = "minizinc/solutions/perlin_noise.dzn"
    terrain_file   = "terrain/data/perlin_noise.dzn"

    buildings = read_buildings(buildings_file)
    # on passe buildings pour aider read_dzn_terrain à choisir l'orientation qui correspond au MiniZinc
    W, H, terrain, isRoad = read_dzn_terrain(terrain_file, buildings=buildings, verbose=False)

    # debug=True pour voir contours et conflits
    conflicts = draw_map(buildings, W, H, terrain, isRoad, debug=True)

    # si tu veux un affichage simple sans debug, fais :
    # draw_map(buildings, W, H, terrain, isRoad, debug=False)
