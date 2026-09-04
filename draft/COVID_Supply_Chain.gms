* Erick Jones
* Graduate Program in Operations Research and Industrial Engineering
* The University of Texas at Austin

* Water_Energy run file

* Load database



*$set nin indata2

$call GDXXRW input=gamsinputcovid.xlsx output=indatamod.gdx index=index!A1

*Multipliers that Can be Modified

Scalar h holding costs /0.1/;

Scalar s safety stock /10/;

Scalar a required service level /100/;

Scalar CostPerMile cost per mile /1/;



set Manufacturers / 1*2 /;
alias (m,MANU,Manufacturers);

set Warehouses /1*8/;
alias(w,WARE,Warehouses);

set Patients /1*32/;
alias(p,PATI,Patients);

*Loading Sets from Excel

*Distance between Manufactuer and Warehouse
Parameter  TransportDistanceAB(MANU, WARE);

$GDXIN indatamod.gdx
$LOAD TransportDistanceAB
$GDXIN

*Distance between  Warehouse and Patient
Parameter  TransportDistanceBJ(WARE, PATI);

$GDXIN indatamod.gdx
$LOAD TransportDistanceBJ
$GDXIN

*Patient Demand
Parameter  Demand(PATI);

$GDXIN indatamod.gdx
$LOAD Demand
$GDXIN



*Variables

Positive Variables
     ImmunizationsToWarehouse(MANU,WARE)
     ImmunizationsToPatient(WARE,PATI);


Variables
z
z1
z2
z3
z4
z5;


Equations

cost1
cost2
cost3
cost4
cost5
cost  ;


* Objective Function


cost1..         z1 =e= sum( (MANU,WARE),TransportDistanceAB(MANU,WARE)*CostPerMile*ImmunizationsToWarehouse(MANU,WARE) );
cost2..         z2 =e= sum( (WARE,PATI),TransportDistanceBJ(WARE,PATI)*CostPerMile*ImmunizationsToPatient(WARE,PATI) );
cost3..         z3 =e= sum( (MANU,WARE),TransportDistanceAB(MANU,WARE)/2 + s)*h;
cost4..         z4 =e= sum( (MANU,WARE),TransportDistanceAB(MANU,WARE))*h/( (1-a)*sum(PATI,Demand(PATI)) );

cost5..         z5 =e= z1+z2;

cost..          z  =e= z5;

* Constraints

*Demand Constraints
equation DemandConstraints(PATI);
DemandConstraints(PATI)..   sum(WARE, ImmunizationsToPatient(WARE,PATI)) =g= Demand(PATI);

*Supply Constraints
equation SupplyConstraints(WARE);
SupplyConstraints(WARE)..    sum(MANU, ImmunizationsToWarehouse(MANU,WARE)) =g= sum(PATI, ImmunizationsToPatient(WARE,PATI));





Model program / all /;


option solprint=on, resLim=100000, lp = cplex, threads = 6 ;


solve program using lp min z;


