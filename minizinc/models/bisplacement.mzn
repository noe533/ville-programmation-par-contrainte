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

array[CATS, TERRAINS] of int: allowedTerrain =
  array2d(CATS, TERRAINS, [
    % eau plaine forêt mont.
       0, 1,  1,  0,   % 0 road     
       0, 1,  1,  0,   % 1 house    
       0, 1,  0,  0,   % 2energie      
       0, 1,  1,  0    % 3commerce
  ]);


/***********************
 * Variables décisionnelles
 ***********************/

% Position de chaque bâtiment (coin en bas à gauche je crois)
array[1..NB_BUILDINGS] of var 1..W: x;
array[1..NB_BUILDINGS] of var 1..H: y;


% Non chevauchement des batiments
constraint diffn(x, y, sizeX, sizeY);

% Batiments sur le terrain (contrainte de bord)
constraint forall(b in BATIMENTS)(
    x[b] + sizeX[b] -1 <= W /\
    y[b] + sizeY[b] -1 <= H
);


constraint forall(b in BATIMENTS)(allowedTerrain[category_type[typeBat[b]], terrain[y[b], x[b]]] == 1);
constraint forall(b in BATIMENTS)(allowedTerrain[category_type[typeBat[b]], terrain[y[b] + sizeY[b], x[b]]] == 1);
constraint forall(b in BATIMENTS)(allowedTerrain[category_type[typeBat[b]], terrain[y[b], x[b] + sizeX[b]]] == 1);
constraint forall(b in BATIMENTS)(allowedTerrain[category_type[typeBat[b]], terrain[y[b] + sizeY[b], x[b] + sizeX[b]]] == 1);
% Chaque case occupée par le bâtiment doit être sur terrain autorisé
%constraint forall(b in BATIMENTS)(
%  forall(dx in 0..sizeX[b]-1, dy in 0..sizeY[b]-1)(
%    allowedTerrain[category_type[typeBat[b]], terrain[y[b]+dy, x[b]+dx]] == 1
%  )
%);

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
   ++ " y=" ++ show(y[b]) ++ "\n"
  | b in 1..NB_BUILDINGS
];