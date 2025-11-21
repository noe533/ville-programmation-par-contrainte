include "../../terrain/data/perlin_noise.dzn";
include "../data/buildings.dzn";
include "globals.mzn";

/*
  Convention terrain (doit matcher le Python) :
  0 = eau
  1 = plaine
  2 = forêt
  3 = montagne
*/
int: EAU      = 0;
int: PLAINE   = 1;
int: FORET    = 2;
int: MONTAGNE = 3;

/***********************
 * Variables décisionnelles
 ***********************/

% Position du centre de chaque bâtiment (en cases)
array[1..NB_BUILDINGS] of var 1..W: x;
array[1..NB_BUILDINGS] of var 1..H: y;

% occ[b,xx,yy] = vrai si le bâtiment b occupe la case (xx,yy)
% -> modèle case par case, style "Manhattan"
array[1..NB_BUILDINGS, 1..W, 1..H] of var bool: occ;

/***********************
 * Paramètres de terrain autorisé
 ***********************/

% allowedTerrain[t, g] = 1 si le type de bâtiment t peut aller sur un terrain g
% Index des types de bâtiments : 0..7
% Index des types de terrain : 0..3  (EAU, PLAINE, FORET, MONTAGNE)
array[1..NB_TYPES, 1..NB] of int: allowedTerrain =
  array2d(0..7, 0..3, [
    %              eau plaine forêt mont.
       0, 1, 1, 0,   % 0 maison
       0, 1, 1, 0,   % 1 commerce
       0, 1, 1, 0,   % 2 école
       0, 1, 1, 0,   % 3 église
       0, 1, 1, 0,   % 4 parc
       0, 1, 1, 0,   % 5 hôpital
       0, 1, 1, 0,   % 6 mairie
       0, 1, 0, 0    % 7 usine : pas en forêt
  ]);

/***********************
 * Lien centre ↔ occupation case par case
 ***********************/

% Un bâtiment b occupe un petit "bloc Manhattan" autour de son centre :
% rayon[b] = demi-taille (en cases) dans chaque direction
constraint
  forall(b in 1..NB_BUILDINGS, xx in 1..W, yy in 1..H)(
    occ[b,xx,yy] <->
      ( abs(xx - x[b]) <= rayon[b] /\
        abs(yy - y[b]) <= rayon[b] )
  );


/***********************
 * Non-chevauchement des bâtiments (case par case)
 ***********************/

% Sur chaque case (xx,yy), au plus un bâtiment
constraint
  forall(xx in 1..W, yy in 1..H)(
    sum(b in 1..NB_BUILDINGS)( bool2int(occ[b,xx,yy]) ) <= 1
  );

/***********************
 * Contraintes de terrain et de distance
 ***********************/

% 1) Terrain autorisé : chaque case occupée par un bâtiment doit être d'un type compatible
constraint
  forall(b in 1..NB_BUILDINGS, xx in 1..W, yy in 1..H)(
    occ[b,xx,yy] ->
      allowedTerrain[typeBat[b], terrain[xx,yy]] = 1
  );

% 3) Types "ville" à rapprocher des ressources eau + forêt (via les centres)
set of int: CITY_TYPES = {0,1,2,3,4,5,6};  % maison, commerce, école, église, parc, hôpital, mairie

int: MAX_WATER_DIST  = 8;
int: MAX_FOREST_DIST = 8;

constraint
  forall(b in 1..NB_BUILDINGS where typeBat[b] in CITY_TYPES)(
    distWater[x[b], y[b]]  <= MAX_WATER_DIST /\
    distForest[x[b], y[b]] <= MAX_FOREST_DIST
  );
  
  

/***********************
 * Stratégie de résolution
 ***********************/

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