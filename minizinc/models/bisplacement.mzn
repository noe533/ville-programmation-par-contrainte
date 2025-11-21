include "../../terrain/data/perlin_noise.dzn";
include "../data/buildings.dzn";
include "globals.mzn";
include "diffn.mzn";

/*
  Convention terrain (doit matcher le Python) :
  0 = eau
  1 = plaine
  2 = forêt
  3 = montagne
*/
int: EAU = 0;
int: PLAINE = 1;
int: FORET = 2;
int: MONT = 3;
set of int: TERRAINS = {EAU, PLAINE, FORET, MONT};

set of int: BATIMENTS = 1..NB_BUILDINGS;

array[TYPES, TERRAINS] of int: allowedTerrain =
  array2d(TYPES, TERRAINS, [
    % eau plaine forêt mont.
       0, 1,    1,    0,   % 0 maison
       0, 1,    1,    0,   % 1 commerce
       0, 1,    1,    0,   % 2 école
       0, 1,    1,    0,   % 3 église
       0, 1,    1,    0,   % 4 parc
       0, 1,    1,    0,   % 5 hôpital
       0, 1,    1,    0,   % 6 mairie
       0, 1,    0,    0    % 7 usine
  ]);


/***********************
 * Variables décisionnelles
 ***********************/

% Position de chaque bâtiment (coin en bas à gauche je crois)
array[1..NB_BUILDINGS] of var 1..W: x;
array[1..NB_BUILDINGS] of var 1..H: y;


% Non chevauchement des batiments
constraint diffn(x, y, rayon, rayon);

% Batiments sur le terrain (contrainte de bord)
constraint forall(b in BATIMENTS)(
    x[b] + rayon[b] -1 <= W /\
    y[b] + rayon[b] -1 <= H
);

% Chaque case occupée par le bâtiment doit être sur terrain autorisé
constraint forall(b in BATIMENTS)(
  forall(dx in 0..rayon[b]-1, dy in 0..rayon[b]-1)(
    allowedTerrain[typeBat[b], terrain[y[b]+dy, x[b]+dx]] == 1
  )
);

%% Variable à minimiser : rayon englobant de la ville
%% Bounding box de la ville
%var int: min_x = min(b in BATIMENTS)(x[b]);
%var int: min_y = min(b in BATIMENTS)(y[b]);
%var int: max_x = max(b in BATIMENTS)(x[b] + rayon[b]);
%var int: max_y = max(b in BATIMENTS)(y[b] + rayon[b]);
%
%% Dimensions du rectangle englobant
%var int: largeur_ville = max_x - min_x;
%var int: hauteur_ville = max_y - min_y;
%
%/***********************
% * Stratégie de résolution
% ***********************/
%
%solve minimize largeur_ville + hauteur_ville;
%
solve satisfy;
/***********************
 * Sortie 
 ***********************/

output [
  "b=" ++ show(b)
   ++ " type=" ++ show(typeBat[b])
   ++ " x=" ++ show(x[b])
   ++ " y=" ++ show(y[b])
   ++ " r=" ++ show(rayon[b]) ++ "\n"
  | b in 1..NB_BUILDINGS
];