# IC 設計 EDA 與 veryl2chip 虛擬 FPGA 實作報告

- **完成工具**：Gemini（AI 輔助整理與撰寫）
- **日期**：2026-10-29
- **參考連結**：
  - [veryl2chip IDE](https://ccc-eda.github.io/veryl2chip/web/dist/index.html)
  - [nand2tetris HDL 模擬器](https://ccc-js.github.io/hack-computer/dist/hdl.html)
  - [Cornell ECE 5745 Handouts](https://www.csl.cornell.edu/courses/ece5745/handouts.html)
  - [veryl2chip GitHub](https://github.com/ccc-eda/veryl2chip/)
  - [hack-computer GitHub](https://github.com/ccc-js/hack-computer)

---

## 摘要

本報告先說明 IC 設計中 EDA（Electronic Design Automation，電子設計自動化）的核心角色與標準流程，再以瀏覽器端開源 EDA 工具 `veryl2chip` 走過一次「撰寫 RTL → 模擬驗證 → 邏輯合成 → 佈局繞線 → 靜態時序分析 → 燒錄至虛擬 FPGA 板」的完整流程，最後在虛擬 iCEBreaker 開發板的 RISC-V 系統上執行內建的 C 語言互動程式 **「C：開關 (`switches.c`)」**，透過切換外部 PMOD 開關觀察 LED 狀態與 USB 終端機的即時數值轉換，記錄操作過程並整理學習心得。報告同時對照 `nand2tetris` HDL 模擬器與 Cornell ECE 5745 的課程教材，說明這些工具在學習數位 IC 設計時各自扮演的角色。

本報告由 Gemini 協助整理與撰寫。

---

## 1. IC 設計中的 EDA 是什麼？

### 1.1 從一個想法到一顆晶片
一顆現代數位 IC 動輒包含數千萬至數十億個電晶體，已經不可能靠人工畫出每個邏輯閘與每條金屬連線。數位 IC 設計的典型流程如下：

1. **規格制定（Specification）**：決定晶片的功能需求、目標效能、功耗預算與面積限制。
2. **架構設計（Architecture）**：將系統切割成 CPU 核心、記憶體（SRAM / Block RAM）、匯流排與周邊介面（如 UART、GPIO）等區塊。
3. **RTL 設計（Register-Transfer Level）**：使用 Verilog、SystemVerilog、VHDL 或 Veryl 等硬體描述語言描述暫存器轉移與組合邏輯行為。
4. **功能驗證（Verification）**：撰寫 testbench、跑模擬並比對波形，確認設計在各種輸入下皆符合規格。
5. **邏輯合成（Synthesis）**：把抽象的 RTL 程式碼轉譯並化簡成邏輯閘層級的網表（Gate-level Netlist）。
6. **可測試性設計（DFT）**：插入掃描鏈（Scan Chain）或內建自我測試（BIST）等電路，方便晶片製造後進行實體測試。
7. **實體設計（Physical Design）**：包含元件佈局（Placement）、時脈樹合成（CTS）與金屬繞線（Routing）。
8. **靜態時序分析（STA）**：檢查各路徑是否滿足 setup time 與 hold time 要求，並計算最高操作頻率 Fmax。
9. **實體驗證（Signoff）**：執行設計規則檢查（DRC）、電路與佈局比對（LVS）、壓降（IR-drop）與功耗分析。
10. **Tape-out 與製造**：將最終的 GDSII 版圖檔交給晶圓廠製造、封裝與測試，或產生位元流（Bitstream）燒錄至 FPGA。

### 1.2 EDA 的角色
**EDA 是把上述所有設計與驗證流程自動化的軟體工具集合。** 它就像是硬體工程師的編譯器與自動化產線，讓工程師能用高階硬體描述語言設計電路，再由工具負責化簡布林邏輯、對應到標準元件或 FPGA 資源、安排實體位置、自動拉線、計算訊號延遲與功耗，最後產生可製造或可燒錄的檔案。沒有 EDA 工具鏈，現代複雜處理器與 SoC 的設計根本無法完成。

EDA 工具依階段大致可分為：

| 設計階段 | 工作內容 | 代表性工具 |
| :--- | :--- | :--- |
| **RTL 模擬** | 驗證電路功能、產生與檢視波形 | Verilator、ModelSim、VCS、veryl-sim |
| **邏輯合成** | RTL 轉閘級 netlist、面積與邏輯最佳化 | Yosys、Design Compiler、Genus、veryl-eda |
| **閘級模擬** | 確認合成前後的網表與 RTL 行為一致 | Verilator、ModelSim、veryl-eda gatesim |
| **佈局繞線** | 決定元件實體位置與金屬導線連接 | nextpnr、Innovus、IC Compiler、veryl-eda P&R |
| **時序分析** | 計算關鍵路徑延遲、檢查違規與計算 Fmax | OpenSTA、PrimeTime、Tempus |
| **實體驗證** | DRC、LVS、功耗分析、IR-drop 檢查 | KLayout、Calibre、RedHawk |
| **FPGA 流程** | LUT 查找表對應、佈局繞線與位元流產生 | Yosys、nextpnr、IceStorm、veryl-eda |

### 1.3 FPGA 與 ASIC 的差異
- **FPGA（現場可程式化邏輯閘陣列）**：晶片內部在出廠時就已經預先配置好大量可程式化的查找表（LUT）、正反器（Flip-Flop）、Block RAM 與繞線開關。EDA 工具負責將設計對應到這些現有資源並產生位元流（bitstream），可以反覆燒錄與修改，除錯成本極低，非常適合教學實驗與系統原型驗證。
- **ASIC（特殊應用積體電路）**：針對特定功能量身訂製的晶片，使用製程廠提供的標準元件庫（Standard Cell）或全訂製電路進行設計。EDA 流程更長且嚴謹，需要深入考慮製程變異、寄生電容、時脈樹平衡、功耗與良率，雖然投片成本高昂，但在量產時能取得最佳的效能、面積與低功耗表現。

`veryl2chip` 同時提供了 FPGA（Lattice iCE40UP5K）與 ASIC（vlib、SKY130）兩種後端流程，讓使用者可以在同一個介面中觀察同一份 RTL 設計在兩種不同實現方式下的差異。

### 1.4 為什麼 EDA 很重要
- **處理龐大規模**：人類無法手工排列與檢查數千萬至數十億個邏輯閘的連線。
- **確保功能正確性**：透過多層次的模擬、形式驗證與閘級比對，能在昂貴的硬體製造前抓出邏輯與合成錯誤。
- **最佳化效能與功耗**：合成與實體設計階段的每一個演算法決策，都會直接決定晶片的最高頻率（Fmax）、面積大小與耗電量。
- **降低開發風險與成本**：一次先進製程的 ASIC 投片費用動輒數百萬美元，完善的 EDA 驗證是避免投片失敗的唯一防線。

---

## 2. 參考資料與工具介紹

### 2.1 veryl2chip IDE
`veryl2chip` 是一套以 Rust 與 WebAssembly 實作的開源 EDA 工具鏈，開啟瀏覽器即可直接執行（背景載入僅需約 194 ms），完全不需在本地端安裝龐大的商業軟體。其首頁將學習路徑規劃為「學 Veryl（34 個範例）」、「做電路，放上開發板（17 個範例）」、「開一台電腦，寫程式（8 個範例）」與「看電路變成晶片（42 個範例）」四大主題，主要支援：

- **Veryl 語言開發**：提供硬體描述語言的即時編輯、語法檢查與快速模擬。
- **完整 FPGA 流程**：RTL → Logic Netlist → 技術無關最佳化 → LUT4 對應 → 佈局（Placement） → 繞線（Routing） → 靜態時序分析（STA） → 產生位元流。
- **完整 ASIC 流程**：標準元件對應 → 列式佈局 → 時脈樹合成（CTS）與全域繞線 → 細部繞線 → STA → 功耗與 IR-drop 分析。
- **全面驗證機制**：使用同一組 testbench 分別對 RTL、通用閘、iCE40 FPGA 與 ASIC 四種層級的實作進行模擬，確保轉換過程完全等價。
- **虛擬 iCEBreaker 開發板**：在瀏覽器中模擬真實的開發板與周邊，包含 LED、按鈕、8 位元指撥開關、USB 終端機、七段顯示器、蜂鳴器、VGA 與麵包板。

這套工具將原本分散在數套昂貴商業軟體中的前後端流程濃縮進單一網頁，非常適合用來建立對 EDA 全貌的直觀理解。

### 2.2 nand2tetris HDL 模擬器
`nand2tetris`（`hack-computer`）的網頁版 HDL 模擬器從最底層的 `Nand` 閘出發，引導學習者依序打造出 `And`、`Or`、`Xor`、加法器、`ALU`、暫存器與記憶體，最終組裝出能執行 Hack 組合語言的 CPU。它強調「從邏輯閘到電腦」的層層抽象建構，與 `veryl2chip` 的「從高階 RTL 到實體晶片」剛好形成互補：

- **nand2tetris**：由下而上（Bottom-Up）理解計算機硬體如何由基本邏輯閘組合而成。
- **veryl2chip**：由上而下（Top-Down）體驗真實工業界 EDA 流程如何將程式碼合成、佈局並落地為實體晶片。

### 2.3 Cornell ECE 5745
Cornell ECE 5745「Complex Digital ASIC Design」的課程講義提供了扎實的晶片設計理論基礎，內容涵蓋：
- HDL 與 Verilog 硬化設計規範。
- CMOS 電晶體特性、標準元件庫與全訂製設計方法。
- 自動化設計流程以及 ASIC 與 Custom 設計之間的效能取捨。
- 晶片封裝、電源網路、時脈分配與 I/O 電路。
- 系統測試與多層次驗證方法。
- 邏輯合成演算法與實體設計（Placement & Routing）自動化演算法。
- 商業 ASIC 前後端工具與 OpenLANE 開源晶片設計流程。

這些學術理論正好能與 `veryl2chip` 中實際看到的合成網表、模擬退火佈局、繞線與 STA 報表互相印證。

---

## 3. 實際操作：從 Veryl 到虛擬 FPGA

以下操作先以 `veryl2chip` 教學區的第 1 課 **「Blinky 閃爍 LED」** 走過一次完整的硬體合成與驗證流程。該專案包含描述硬體邏輯的 `blinky.veryl` 與定義晶片實體腳位對應的 `pins.pcf`：

1. **開啟範例與快速測試**：在左側專案欄選擇「第 1 課 Blinky 閃爍 LED」，點擊執行測試。系統透過 `TestBlinky` 測試平台以小型計數器驗證溢位與 LED 狀態變化，僅花費 `0.01 s` 即顯示 `1 個測試通過 (PASS)`。
2. **全面驗證**：執行「全面驗證」功能，系統以同一套 testbench 分別跑過 RTL、通用邏輯閘、iCE40 原生元件與 ASIC 標準元件四種實作，四者輸出波形與結果完全一致。
3. **觀察邏輯合成階段**：
   - **RTL → Logic**：解析 Veryl 語法、展開參數並攤平模組階層。
   - **Logic Netlist**：將計數器邏輯轉換為 24 個 D 型正反器（DFF）與加一進位邏輯。
   - **技術無關最佳化**：執行常數傳播、消除重複與未使用的冗餘邏輯。
   - **LUT4 對應（Technology Mapping）**：將邏輯對應到 iCE40 FPGA 的硬體資源，共使用約 33 個 `SB_LUT4`（四輸入查找表）與 24 個 `SB_DFFR`。
4. **佈局與繞線（P&R）**：切換至 Placement 視圖觀察演算法如何將相關聯的 LUT 與正反器集中配置在相鄰區塊；切換至 Routing 視圖觀察邏輯區塊之間的實際導線連接。
5. **靜態時序分析（STA）**：在 Timing 視圖中檢視關鍵路徑（Critical Path），延遲約為 29.68 ns，換算最高可運作頻率 Fmax 約 33.7 MHz。由於 iCEBreaker 開發板的系統時脈為 12 MHz（週期約 83.33 ns），時序擁有充足的餘裕（Positive Slack）。
6. **燒進虛擬板與產生位元流**：切換到「虛擬板」即可看到板載 LED 依二進位計數閃爍，按住 `BTN_N` 可觸發硬體重置；同時也能下載 `.bin` 位元流檔案燒入實體開發板。

透過這個過程，可以清楚看到短短幾行硬體描述語言如何一步步轉化為查找表、正反器、晶片座標與實體導線。

---

## 4. 實作與互動紀錄：C 程式「開關 (`switches.c`)」

### 4.1 程式來源與硬體架構
在 `veryl2chip` 範例庫的「C 程式」分類中，提供了一系列運行於 RISC-V 系統單晶片（`RvSoc`）上的嵌入式 C 語言範例。本次實作選擇 **「C：開關 (`switches.c`)」** 進行測試。

該環境的硬體底層是一顆由 Veryl 撰寫的 RISC-V CPU，並透過 `pins.pcf` 將 `iCE40UP5K (SG48)` 晶片的實體腳位與外部周邊連接：
- **系統時脈與重置**：`CLK -> i_clk`、`BTN_N -> i_rst`
- **UART 序列通訊**：`RX -> i_rx`、`TX -> o_tx`（連接至畫面右側的 USB 終端機，鮑率設為 `115200`）
- **PMOD1A（8 顆輸出 LED）**：腳位 `P1A1 ~ P1A10` 對應至硬體輸出訊號 `o_led[0] ~ o_led[7]`
- **PMOD1B（8 個輸入開關）**：腳位 `P1B1 ~ P1B10` 對應至硬體輸入訊號 `i_sw[0] ~ i_sw[7]`

`switches.c` 的功能是持續透過記憶體映射輸出入（MMIO）讀取 `PMOD1B` 上 8 個開關的狀態，同步點亮 `PMOD1A` 上對應位置的 LED，並在開關狀態改變時，將目前的 8-bit 數值同時以**二進位、十六進位與十進位**三種格式透過 UART 印到 USB 終端機上。

### 4.2 操作方式與執行效能
1. 在左側範例庫選擇「C 程式 → C：開關 (`switches.c`)」。
2. 點擊上方「① 虛擬板」，系統會自動將 C 程式碼編譯為 RISC-V 機器碼（大小為 **2248 位元組**），並直接寫入虛擬板的 **Block RAM** 中。
3. 勾選開啟「USB 終端機」（鮑率 115200），並顯示 `PMOD1A (8 顆 LED)` 與 `PMOD1B (8 個開關)` 面板。
4. 在瀏覽器的 `RvBoard` CPU 模擬模式下，系統模擬速度達到 **11.80 MHz（約為真實 12 MHz 硬體的 0.98 倍）**，幾乎等同真實硬體的即時反應。
5. 使用滑鼠點擊右下角 `PMOD1B` 的 0~7 號開關，觀察 LED 變化與終端機輸出。

由於只替換 C 語言軟體時不需要重新對 RISC-V CPU 進行邏輯合成與佈局繞線，工具只需把 2248 bytes 的機器碼重新填入 Block RAM 即可立即執行，直接體現了 SoC「硬體固定、軟體彈性更新」的架構優勢。

### 4.3 互動測試紀錄
剛啟動虛擬開發板時，`PMOD1B` 的 8 個開關（0~7）皆處於未按下的關閉狀態，`PMOD1A` 的 8 顆 LED 全滅，USB 終端機立即輸出一行初始狀態：

```text
switches 00000000 = 0x00 = 0
```

接著依序用滑鼠點擊切換右下角 `PMOD1B` 的不同開關組合（從單一開關、多開關組合到全開），`PMOD1A` 的橘色 LED 會即時亮起對應位元，同時 USB 終端機同步印出每一次狀態改變的數值紀錄：

```text
switches 00000000 = 0x00 = 0
switches 00000001 = 0x01 = 1
switches 00000101 = 0x05 = 5
switches 00010101 = 0x15 = 21
switches 01010101 = 0x55 = 85
switches 11010101 = 0xd5 = 213
switches 11111111 = 0xff = 255
```

### 4.4 訊號與數值轉換分析
- **位元映射關係**：`PMOD1B` 的第 $n$ 號開關對應到二進位的第 $n$ 個 bit（權重為 $2^n$）。當只開啟第 0 與第 2 號開關時，輸入二進位為 `00000101`，C 程式讀取後換算為十六進位 `0x05` 與十進位 $2^2 + 2^0 = 5$。
- **全開邊界測試**：當將 0~7 號開關全部點亮時，`PMOD1A` 的 8 顆 LED 全數亮起，二進位為 `11111111`，對應無號 8-bit 整數的最大值 `0xff`（十進位 255）。
- **輪詢（Polling）與狀態偵測**：程式在無窮迴圈中不斷讀取 GPIO 輸入暫存器，並與上一次的狀態值比對；只有當偵測到開關狀態發生變化（`sw != last_sw`）時，才會觸發 UART 字串格式化與傳送，避免終端機被重複的訊息洗版。

### 4.5 從開關實驗看到的 EDA 與 SoC 觀念
這個看似簡單的 I/O 實驗，背後其實串聯了完整的軟硬體與晶片設計鏈：
1. **實體腳位約束（Pin Constraint）**：透過 `pins.pcf` 將晶片封裝腳位（如 `P1A1~P1A10`、`P1B1~P1B10`）與 RTL 模組的輸出入埠綁定。
2. **硬體平台合成**：RISC-V CPU、記憶體控制器、GPIO 與 UART 模組由 Veryl 撰寫，經過 EDA 合成與佈局繞線成為 FPGA 硬體電路。
3. **軟體編譯與載入**：`switches.c` 由內建編譯器轉為 2248 bytes 的機器碼並載入 Block RAM。
4. **系統級整合驗證**：當點擊虛擬開關能正確點亮 LED 並在終端機印出數值，就同時驗證了外部腳位輸入、匯流排讀寫、CPU 指令執行、GPIO 輸出以及 UART 鮑率時序皆運作正常。

---

## 5. 心得

### 5.1 EDA 是把抽象程式碼層層落地的橋樑
以前寫軟體程式時，變數賦值與迴圈就只是抽象的邏輯敘述；但在 `veryl2chip` 裡，一段簡單的計數或狀態控制邏輯，會經過合成變成具體的 24 個正反器與 33 個 LUT4，最後被放到晶片上的實體座標並拉好導線。EDA 的價值就在於替工程師自動化處理這些龐雜的底層轉換，同時透過各階段的網表、佈局圖與時序報表，讓工程師能精確掌握硬體實現的結果。

### 5.2 多層次驗證是硬體設計的命脈
在操作過程中，「全面驗證」功能用同一組 testbench 同時跑過 RTL、通用邏輯閘、FPGA 與 ASIC 四種模型。這讓我理解為什麼在 IC 設計產業中，驗證往往占據大半的開發時間：因為從高階語言轉換到實體邏輯閘的過程中，任何合成規則或腳位定義的落差都可能導致晶片失效，唯有在每個階段持續比對驗證，才能確保最終投片的正確性。

### 5.3 時序與實體限制是硬體與軟體最大的分水嶺
在 `nand2tetris` 或一般軟體開發中，我們很少關心一個加法或邏輯判斷需要花費多少奈秒（ns）；但在 `veryl2chip` 的 STA 時序分析中，清楚標示出關鍵路徑延遲（29.68 ns）與最高操作頻率（33.7 MHz）。這讓我體會到「邏輯正確」只是硬體設計的第一步，電路還必須在目標時脈週期內完成訊號傳遞，才能在實體晶片上穩定運作。

### 5.4 軟硬體協同設計（HW/SW Co-design）的威力
透過 `switches.c` 的實驗，可以清楚看到同一個系統中硬體（`RvSoc`）與軟體（C 程式）如何完美分工。如果要用純硬體狀態機去實作二進位、十六進位與十進位的字串轉換並透過 UART 印出，不僅 RTL 會寫得非常複雜，每次改格式都要重新合成；但有了 RISC-V 硬體平台後，只要修改 C 程式並花不到一秒把 2248 bytes 寫進 Block RAM 就能立刻測試，充分展現了軟硬體協同設計的高效率。

### 5.5 開源 Web EDA 的高度教育價值
過去要接觸 FPGA 或 ASIC 設計，往往得安裝動輒數十 GB 的商業軟體並購買實體開發板，門檻相當高。`veryl2chip` 利用 WebAssembly 將模擬、合成、佈局繞線、STA 與高達 0.98 倍真實速度的虛擬開發板全部放進瀏覽器中，對照 `nand2tetris` 的底層邏輯建構與 Cornell ECE 5745 的理論教材，剛好補上了最關鍵的「親手走過一次真實 EDA 流程」的實作拼圖。

### 5.6 限制與未來可探索方向
- 瀏覽器內的合成與佈局繞線演算法為了兼顧網頁回應速度，模型較商業級工具有所簡化，適合教學與概念驗證，但大型複雜設計仍需依賴完整工具鏈。
- 虛擬開發板的指令集模擬模式（`RvBoard`）速度極快，但若切換至逐週期解碼位元流的真實閘級模擬模式，速度會隨電路規模明顯下降。
- 未來若能進一步嘗試修改 Veryl 硬體周邊（例如自己新增一個硬體 PWM 或硬體加速器模組），再由 C 語言透過記憶體映射去呼叫它，將能更完整體驗自訂 SoC 的樂趣。

---

## 6. 結論

IC 設計的 EDA 是一整套將高階硬體描述語言自動轉換為可製造晶片或 FPGA 位元流的軟體工具鏈，涵蓋了功能模擬、邏輯合成、佈局繞線、靜態時序分析與實體驗證。透過本次作業實際操作 `veryl2chip`，我不僅觀察了 `Blinky` 電路從 Veryl 程式碼一路轉化為 LUT4、正反器與實體走線的過程，也在虛擬 iCEBreaker 開發板上執行了 `switches.c`，親手驗證了外部指撥開關輸入、LED 輸出與 UART 終端機通訊的軟硬體整合運作。結合 `nand2tetris` 與 Cornell ECE 5745 的教材內容，讓我對數位 IC 設計的抽象層次與 EDA 自動化流程有了比課本更具體且深入的認識。

---

## 7. 使用工具聲明

- 本報告由 Gemini 協助蒐集資料、整理流程與撰寫。
- 操作過程與硬體數據（如 2248 bytes Block RAM、11.80 MHz 模擬速度、腳位映射與合成資源）皆依據實際操作 `veryl2chip` 官方 IDE、教學文件與 `switches.c` 範例程式之結果整理。
- 參考資料：
  - veryl2chip：https://ccc-eda.github.io/veryl2chip/web/dist/index.html
  - nand2tetris HDL 模擬器：https://ccc-js.github.io/hack-computer/dist/hdl.html
  - Cornell ECE 5745：https://www.csl.cornell.edu/courses/ece5745/handouts.html
  - veryl2chip GitHub：https://github.com/ccc-eda/veryl2chip/
  - hack-computer GitHub：https://github.com/ccc-js/hack-computerg