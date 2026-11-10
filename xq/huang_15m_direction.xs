// 黃老師 15 分鐘多方方向警示草稿，無下單語法
// 在 XQ XS 編輯器以「警示腳本」建立，設定 15 分鐘頻率
SetTotalBar(50);
Vars: MA6(0), MA13(0);
MA6 = Average(Close, 6);
MA13 = Average(Close, 13);
if CurrentBar > 13 and Close > MA6 and MA6 > MA13 and MA6 > MA6[1] then
    Ret = 1;
