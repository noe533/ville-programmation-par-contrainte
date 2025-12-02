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

% Positions admissibles calculées à la volée
array[TYPES, 1..W, 1..H] of bool: allowedStart =
  array3d(TYPES, 1..W, 1..H, [
    let {
      int: sx = sizeX_type[t],
      int: sy = sizeY_type[t]
    } in
    x0 + sx - 1 <= W /\
    y0 + sy - 1 <= H /\
    allowedTerrain[category_type[t], terrain[y0, x0]] == 1 /\
    allowedTerrain[category_type[t], terrain[y0, x0 + sx - 1]] == 1 /\
    allowedTerrain[category_type[t], terrain[y0 + sy - 1, x0]] == 1 /\
    allowedTerrain[category_type[t], terrain[y0 + sy - 1, x0 + sx - 1]] == 1 /\
    allowedTerrain[category_type[t], terrain[y0 + sy div 2, x0 + sx div 2]] == 1 /\
    isRoad[y0, x0] = 0 /\
    isRoad[y0, x0 + sx - 1] = 0 /\
    isRoad[y0 + sy - 1, x0] = 0 /\
    isRoad[y0 + sy - 1, x0 + sx - 1] = 0 /\
    isRoad[y0 + sy div 2, x0 + sx div 2] = 0
    | t in TYPES, x0 in 1..W, y0 in 1..H
  ]);

constraint forall(b in BATIMENTS)(
  allowedStart[typeBat[b], x[b], y[b]]
);


constraint forall(b in BATIMENTS)(
  %4 coins
  allowedTerrain[category_type[typeBat[b]], terrain[y[b],x[b]]] == 1 /\
  allowedTerrain[category_type[typeBat[b]], terrain[y[b],x[b] + sizeX[b] - 1]] == 1 /\
  allowedTerrain[category_type[typeBat[b]], terrain[y[b] + sizeY[b] - 1,x[b]]] == 1 /\
  allowedTerrain[category_type[typeBat[b]], terrain[y[b] + sizeY[b] - 1,x[b] + sizeX[b] - 1]] == 1 /\

  %milieu
  allowedTerrain[category_type[typeBat[b]], terrain[y[b] + sizeY[b] div 2,x[b] + sizeX[b] div 2]] == 1 
  
);


constraint forall(b in BATIMENTS)(
  % 4 coins
  isRoad[y[b], x[b]] = 0 /\
  isRoad[y[b], x[b] + sizeX[b] - 1] = 0 /\
  isRoad[y[b] + sizeY[b] - 1, x[b]] = 0 /\
  isRoad[y[b] + sizeY[b] - 1, x[b] + sizeX[b] - 1] = 0 /\

  % milieu
  isRoad[y[b] + sizeY[b] div 2, x[b] + sizeX[b] div 2] = 0 
);

% bâtiment doit être collé à au moins une route 
constraint forall(b in BATIMENTS)(
   % gauche
  (x[b] > 1 /\ isRoad[ y[b] + sizeY[b] div 2, x[b] - 1 ] = 1)
  \/
  %  droit 
  (x[b] + sizeX[b] - 1 < W /\ isRoad[ y[b] + sizeY[b] div 2, x[b] + sizeX[b] ] = 1)
  \/
  %  bas
  (y[b] > 1 /\ isRoad[ y[b] - 1, x[b] + sizeX[b] div 2 ] = 1)
  \/
  %  haut
  ( y[b] + sizeY[b] - 1 < H /\ isRoad[ y[b] + sizeY[b], x[b] + sizeX[b] div 2 ] = 1));
  
solve satisfy;
/***********************
 * Sortie 
 ***********************/

output [
  "objective=" ++ "\n"
] ++
[
  "b=" ++ show(b)
   ++ " type=" ++ show(typeBat[b])
   ++ " x=" ++ show(x[b])
   ++ " y=" ++ show(y[b]) ++ "\n"
  | b in 1..NB_BUILDINGS
];
