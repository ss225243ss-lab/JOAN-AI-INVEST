// Huang B / 15-minute 1-3 trading day research script
// Only XQ backtest or SIM account. Never connect real broker.
// EnableTestOrders defaults 0. Day count is an approximation tied to bar Date.
SetTotalBar(200);
Inputs: EnableTestOrders(0), StopPts(300), TargetPts(450), MaxHoldDays(3);
Vars: D6(0), D13(0), i(0), BullSignal(false), BearSignal(false),
      HoldDays(0), LastDate(0), K6(0), K13(0);
D6=0; D13=0;
for i=1 to 13 begin
 D13=D13+CloseD(i);
 if i<=6 then D6=D6+CloseD(i);
end;
D6=D6/6; D13=D13/13;
K6=Average(Close,6); K13=Average(Close,13);
BullSignal=CloseD(2)<OpenD(2) and CloseD(1)>OpenD(2) and D6>D13 and K6>K13 and Close>High[1];
BearSignal=CloseD(2)>OpenD(2) and CloseD(1)<OpenD(2) and D6<D13 and K6<K13 and Close<Low[1];
if Date<>LastDate then begin
 if Filled<>0 then HoldDays=HoldDays+1;
 LastDate=Date;
end;
if Position=0 and Filled=0 then HoldDays=0;
if EnableTestOrders=1 then begin
 if Position<>0 and Filled>0 and
    (Close<=FilledAvgPrice-StopPts or Close>=FilledAvgPrice+TargetPts or HoldDays>=MaxHoldDays) then SetPosition(0);
 if Position<>0 and Filled<0 and
    (Close>=FilledAvgPrice+StopPts or Close<=FilledAvgPrice-TargetPts or HoldDays>=MaxHoldDays) then SetPosition(0);
 if Time>=090000 and Time<130000 and Position=0 and Filled=0 and CurrentBar>20 then begin
  if BullSignal then SetPosition(1);
  if BearSignal then SetPosition(-1);
 end;
end;
