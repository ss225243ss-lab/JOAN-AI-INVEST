// 黃老師 5 分鐘多方候選警示草稿，無下單語法
// 設定 5 分鐘頻率；15 分方向須另行人工確認
// GetField 跨頻率的對位需在 XQ 編輯器回測核實
SetTotalBar(100);
Vars: PrevClose(0), TodayOpen(0), Day6(0), Day13(0),
      Intraday6(0), Intraday13(0), i(0);
PrevClose = GetField("收盤價", "D")[1];
TodayOpen = GetField("開盤價", "D");
Day6 = 0;
Day13 = 0;
for i = 1 to 13 begin
    Day13 = Day13 + GetField("收盤價", "D")[i];
    if i <= 6 then Day6 = Day6 + GetField("收盤價", "D")[i];
end;
Day6 = Day6 / 6;
Day13 = Day13 / 13;
Intraday6 = Average(Close, 6);
Intraday13 = Average(Close, 13);
if CurrentBar > 20 and PrevClose > 0 and
   TodayOpen / PrevClose - 1 >= 0.00618 and
   Day6 > Day13 and Intraday6 > Intraday13 and
   Close > High[1] and Close > Intraday6 then
    Ret = 1;
