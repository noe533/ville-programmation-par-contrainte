# ===========================
# Variables
# ===========================
PYTHON=python3
MINIZINC=minizinc

MODEL=minizinc/models/bisplacement.mzn
BUILDINGS=minizinc/data/buildings.dzn


SCALE_SCRIPT=terrain/generator/taille_image.py


RAW_IMAGE := $(firstword $(wildcard images/input/*.png))

ifeq ($(RAW_IMAGE),)
$(error Aucune image .png trouvée dans images/input/)
endif

# Image réduite (processed) avec le même nom de base
PROCESSED_IMAGE = images/processed/$(notdir $(RAW_IMAGE))

# Nom de base (sans dossier ni extension)
NAME := $(basename $(notdir $(RAW_IMAGE)))

TERRAIN=terrain/data/$(NAME).dzn
SOLUTION=minizinc/solutions/$(NAME).dzn
OUTPUT=visualisation/output/solution.png
JSON_OUTPUT=visualisation/output/solution.json

TEMPS=10000

# ===========================
# Règles principales
# ===========================

all: $(OUTPUT)

# 0) Réduction de l'image d'entrée -> image "processed"
$(PROCESSED_IMAGE): $(RAW_IMAGE)
	mkdir -p $(dir $@)
	$(PYTHON) $(SCALE_SCRIPT) --input $(RAW_IMAGE) --output $(PROCESSED_IMAGE)

# 1) Génération du terrain .dzn à partir de l'image processed
$(TERRAIN): $(PROCESSED_IMAGE)
	mkdir -p $(dir $@)
	$(PYTHON) terrain/generator/Perlin_To_Minizinc.py --input $(PROCESSED_IMAGE) --output $(TERRAIN)

# 2) Exécution MiniZinc
$(SOLUTION): $(TERRAIN) $(BUILDINGS) $(MODEL)
	$(MINIZINC) --time-limit $(TEMPS) $(MODEL) > $(SOLUTION)

$(OUTPUT): $(SOLUTION)
	mkdir -p $(dir $@)
	$(PYTHON) visualisation/python/render_solution.py \
	    --input $(SOLUTION) \
	    --output $(OUTPUT) \
	    --json-output $(JSON_OUTPUT)

# Nettoyage des fichiers générés
clean:
	rm -f terrain/data/*.dzn minizinc/solutions/*.dzn visualisation/output/solution.png images/processed/*.png visualisation/output/solution.json
