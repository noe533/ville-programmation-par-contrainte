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


% Variables décisionnelles


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


constraint forall(b in BATIMENTS)(
  let {
    var int: cx = x[b] + sizeX[b] div 2;
    var int: cy = y[b] + sizeY[b] div 2;
    var int: xMax = x[b] + sizeX[b] - 1;
    var int: yMax = y[b] + sizeY[b] - 1;
    % Points à mi-distance entre le centre et chaque coin
    var int: midLeft = (x[b] + cx) div 2;
    var int: midRight = (xMax + cx) div 2;
    var int: midBottom = (y[b] + cy) div 2;
    var int: midTop = (yMax + cy) div 2
  } in
    % 4 coins
    allowedTerrain[category_type[typeBat[b]], terrain[y[b], x[b]]] == 1 /\
    allowedTerrain[category_type[typeBat[b]], terrain[y[b], xMax]] == 1 /\
    allowedTerrain[category_type[typeBat[b]], terrain[yMax, x[b]]] == 1 /\
    allowedTerrain[category_type[typeBat[b]], terrain[yMax, xMax]] == 1 /\

    % milieu
    allowedTerrain[category_type[typeBat[b]], terrain[cy, cx]] == 1 /\

    % points intermédiaires coin-centre
    allowedTerrain[category_type[typeBat[b]], terrain[midBottom, midLeft]] == 1 /\
    allowedTerrain[category_type[typeBat[b]], terrain[midBottom, midRight]] == 1 /\
    allowedTerrain[category_type[typeBat[b]], terrain[midTop, midLeft]] == 1 /\
    allowedTerrain[category_type[typeBat[b]], terrain[midTop, midRight]] == 1
);


constraint forall(b in BATIMENTS)(
  let {
    var int: cx = x[b] + sizeX[b] div 2;
    var int: cy = y[b] + sizeY[b] div 2;
    var int: xMax = x[b] + sizeX[b] - 1;
    var int: yMax = y[b] + sizeY[b] - 1;
    var int: midLeft = (x[b] + cx) div 2;
    var int: midRight = (xMax + cx) div 2;
    var int: midBottom = (y[b] + cy) div 2;
    var int: midTop = (yMax + cy) div 2
  } in
    % 4 coins
    isRoad[y[b], x[b]] = 0 /\
    isRoad[y[b], xMax] = 0 /\
    isRoad[yMax, x[b]] = 0 /\
    isRoad[yMax, xMax] = 0 /\

    % milieu
    isRoad[cy, cx] = 0 /\

    % points intermédiaires coin-centre
    isRoad[midBottom, midLeft] = 0 /\
    isRoad[midBottom, midRight] = 0 /\
    isRoad[midTop, midLeft] = 0 /\
    isRoad[midTop, midRight] = 0
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
%sortie 

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
