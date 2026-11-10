// Huang A / 5-minute day-session research trade script
// ONLY backtest or XQ built-in futures SIM account. Never attach real broker.
// EnableTestOrders defaults 0 (no order even when loaded).
SetTotalBar(200);
Inputs: EnableTestOrders(0), StopPts(100), TargetPts(150);
Vars: D6(0), D13(0), K6(0), K13(0), PrevC(0), OpenToday(0), i(0), LongOK(false), ShortOK(false);
D6=0; D13=0;
for i=1 to 13 begin
 D13=D13+CloseD(i);
 if i<=6 then D6=D6+CloseD(i);
end;
D6=D6/6; D13=D13/13;
PrevC=CloseD(1);
OpenToday=OpenD(0);
K6=Average(Close,6); K13=Average(Close,13);
LongOK=PrevC>0 and D6>D13 and K6>K13 and OpenToday/PrevC-1>=0.00618 and Close>High[1];
ShortOK=PrevC>0 and D6<D13 and K6<K13 and OpenToday/PrevC-1<=-0.00618 and Close<Low[1];
if EnableTestOrders=1 then begin
 if Time>=133000 and Position<>0 then SetPosition(0);
 if Time<133000 and Position<>0 and Filled>0 and
    (Close<=FilledAvgPrice-StopPts or Close>=FilledAvgPrice+TargetPts) then SetPosition(0);
 if Time<133000 and Position<>0 and Filled<0 and
    (Close>=FilledAvgPrice+StopPts or Close<=FilledAvgPrice-TargetPts) then SetPosition(0);
 if Time>=090500 and Time<130000 and Position=0 and Filled=0 and CurrentBar>20 then begin
  if LongOK then SetPosition(1);
  if ShortOK then SetPosition(-1);
 end;
end;
