# 第 6 章：組譯器 (Hack Assembler)

本專案以 Python 實作 Nand2Tetris 第 6 章之 Hack 組譯器（[assembler.py](./assembler.py)），可將 Hack 組合語言（.asm）自動組譯為 16-bit 二進位機器碼（.hack）。

## 1. 實作架構與兩階段組譯流程 (Two-Pass Assembly)

為了處理組合語言中的預定義符號、跳躍標籤（Label）與自訂變數，本組譯器採用標準的**兩階段掃描（Two-Pass）**架構：

* **前置處理 (clean_lines)**：讀取 .asm 原始碼，濾除單行註解（//）與前後空白字元、空行。
* **第一階段 (first_pass) — 建立標籤符號表**：
  * 初始載入 Hack 預設符號（SP, LCL, ARG, THIS, THAT, R0~R15, SCREEN, KBD）。
  * 逐行掃描指令並計算 ROM 位址（由 0 開始遞增）。若遇到 (LABEL) 宣告，則將該標籤名稱對應至當前的 ROM 位址存入符號表，且不佔用實際指令行數。
* **第二階段 (second_pass) — 產生 16-bit 機器碼**：
  * **A-Instruction (@value)**：若為純數字則直接轉為 0 開頭的 15-bit 二進位字串；若為符號且尚未存在於符號表中，則視為新變數，由 RAM 位址 16 開始依序配置並轉為二進位。
  * **C-Instruction (dest=comp;jump)**：將指令剖析為 dest、comp、jump 三個欄位，透過查表（COMP_TABLE、DEST_TABLE、JUMP_TABLE）組合為 111 + comp (7 bits) + dest (3 bits) + jump (3 bits) 之 16-bit 機器碼。

## 2. 執行方式與組譯結果

於專案根目錄開啟終端機執行，程式會自動遞迴搜尋 06 資料夾下所有 .asm 檔案並輸出對應之 .hack 檔案：

    python 06/assembler.py

### 執行輸出紀錄

    已成功組譯: 06\add\Add.asm -> 06\add\Add.hack
    已成功組譯: 06\max\Max.asm -> 06\max\Max.hack
    已成功組譯: 06\max\MaxL.asm -> 06\max\MaxL.hack
    已成功組譯: 06\pong\Pong.asm -> 06\pong\Pong.hack
    已成功組譯: 06\pong\PongL.asm -> 06\pong\PongL.hack
    已成功組譯: 06\rect\Rect.asm -> 06\rect\Rect.hack
    已成功組譯: 06\rect\RectL.asm -> 06\rect\RectL.hack

## 3. 產出檔案列表

| 測試項目 | 原始組合語言 | 組譯後機器碼 |
| :---: | :---: | :---: |
| Add | [Add.asm](./add/Add.asm) | [Add.hack](./add/Add.hack) |
| Max | [Max.asm](./max/Max.asm) / [MaxL.asm](./max/MaxL.asm) | [Max.hack](./max/Max.hack) / [MaxL.hack](./max/MaxL.hack) |
| Rect | [Rect.asm](./rect/Rect.asm) / [RectL.asm](./rect/RectL.asm) | [Rect.hack](./rect/Rect.hack) / [RectL.hack](./rect/RectL.hack) |
| Pong | [Pong.asm](./pong/Pong.asm) / [PongL.asm](./pong/PongL.asm) | [Pong.hack](./pong/Pong.hack) / [PongL.hack](./pong/PongL.hack) |

## 4. 聲明

本作業之 assembler.py 程式碼與說明文件係透過 AI 協作輔助完成，並於本地環境實際執行產生所有 .hack 機器碼檔案。   