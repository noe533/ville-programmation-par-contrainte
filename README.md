# Projet de Placement de Bâtiments sur Terrain

Ce projet permet de générer un terrain à partir d’une image, d’appliquer un algorithme de programmation par contraintes avec MiniZinc pour placer des bâtiments, et de visualiser le résultat.

---

## 📁 Arborescence des dossiers

projet/
│
├── images/
│ ├── input/ # Images d’origine (Perlin, photos, etc.)
│ └── processed/ # Images pixelisées ou prétraitées
│
├── terrain/
│ ├── generator/ # Scripts Python pour générer terrain.dzn
│ └── data/ # Fichiers .dzn représentant le terrain
│
├── minizinc/
│ ├── models/ # Modèles MiniZinc (.mzn)
│ ├── data/ # Données supplémentaires (.dzn, bâtiments, paramètres)
│ └── solutions/ # Solutions produites par MiniZinc (.dzn)
│
├── visualisation/
│ ├── python/ # Scripts Python pour générer des images finales
│ └── output/ # Images finales avec les bâtiments placés
│
├── run_pipeline.sh # Script pour exécuter tout le pipeline sur une image
├── Makefile # Pour automatiser toutes les étapes
└── README.md


---

## ⚡ Pipeline du projet

1. **Images d’entrée**  
   Placer vos images dans `images/input/`.

2. **Génération du terrain**  
   Le script Python `terrain/generator/generate_terrain.py` convertit l’image en fichier `.dzn` et l’enregistre dans `terrain/data/`.

3. **Placement des bâtiments avec MiniZinc**  
   Les modèles `.mzn` dans `minizinc/models/` utilisent les données terrain pour générer une solution `.dzn` dans `minizinc/solutions/`.

4. **Visualisation**  
   Le script `visualisation/python/render_solution.py` prend la solution MiniZinc et produit une image finale dans `visualisation/output/`.

---

## 🛠 Utilisation

### Avec Makefile
```bash
# Exécuter tout le pipeline pour une image spécifique
make all

# Nettoyer les fichiers générés
make clean
