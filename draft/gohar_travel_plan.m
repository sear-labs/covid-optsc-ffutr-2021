%%%% Travel Plan for Covid Vaccine Distribution %%%%

%%% This code serves the purpose of selecting best optimized travel plan. 
%%% C    -- Input distance of different zipcodes in Houston
%%% Zip  -- Contains information of all zipcodes
%%% T    -- Contains latitude and longtitude coordinates of each zipcode
%%% n    -- Number of zipcodes
%%% Plan -- Contains the index  order of visiting Zipcodes 



%% Input data
C = [0	30	41	32	28	34	37	17	27	23	27	23
    30	0	30	16	20	29	27	15	10	13	16	20
    41	30	0	15	24	24	10	25	35	24	23	18
    32	16	15	0	16	17	12	16	20	15	14	9.2
    28	20	24	16	0	9.3	20	5.5	17	12	12	6.9
    34	29	24	17	9.3	0	15	15	26	15	14	9
    37	27	10	12	20	15	0	20	30	20	18	14
    17	15	25	16	5.5	15	20	0	12	6.5	11	7.1
    27	10	35	20	17	26	30	12	0	11	11	17
    23	13	24	15	12	15	20	6.5	11	0	4.3	6.8
    27	16	23	14	12	14	18	11	11	4.3	0	6.3
    23	20	18	9.2	6.9	9	14	7.1	17	6.8	6.3	0];
Zip = [77386	77357	77535	77336	77396	77044	77532	77338 ...
    77365	77339	77345	77346 ];

T = readtable('coordinate.xlsx');
T(end + 1,:) = T(1,:);

n = size(C,1);
%% Solver 

cvx_begin
cvx_solver mosek            %%% For Gurboi, replace mosek with gurobi

variable X(n,n) binary      %%% Xij in {0,1}
variable u(n)               %%% variable to avoid subtours

minimize(sum(sum(C.*X)))    %%% Objective function 

subject to 

    sum(X,1) == 1;         %%% This constraint make sure that we enter each exactly once
    sum(X,2) == 1;         %%% This constraint make sure taht we leave each exactly once
    diag(X)  == 0;         %%% Constraint to avoid the same city computation

    %%% Subtour Elimination MTZ formulation
    for i = 2:n
        for j = 2:n
            if (j ~= i)            
            u(i) - u(j) + 1 <= n*(1 - X(i,j));
            end                
        end
    end
    

cvx_end
%% 

%% Find Index of next optimal Destination
id = 1;
for i = 1:12   
   Plan(i) = id;
   id = find(X(id,:));   
end
%% 


%% Plot Travel Plan on Geographic Coordinates and record video 
v = VideoWriter('travel_plan.mp4');
open(v);
     
figure(1)
for i = 1:12
  geoplot(T.Lon(i:i+1), T.Lat(i:i+1),'LineStyle','-.', 'MarkerSize',10,'Marker', 'o', 'LineWidth', 4,...
       'MarkerFaceColor',[.49 1 .63],'MarkerEdgeColor','k') 
   
   destination = num2str(Zip(Plan(i)));
   text(T.Lon(i), T.Lat(i), destination, 'Color','red','FontSize',28)

  hold on
  pause(2)
  geobasemap streets
  frame = getframe(gcf);
  writeVideo(v,frame);
end
close(v);
%% 




%% Display Travel Plan in Command Window
for i = 1:12
fprintf('%d-->',Zip(Plan(i)))

end
fprintf('%d',Zip(Plan(1)))

disp(' ')
%% 



