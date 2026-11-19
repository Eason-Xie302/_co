# 第 8 章：虛擬機轉譯器（VM Translator）

## 1. 轉譯器程式
- [vm_translator.py](./vm_translator.py)（完整實作第 7 章堆疊算術與記憶體存取、第 8 章分支控制、函式呼叫與 Bootstrap 啟動碼，支援單檔/資料夾轉譯及無參數一鍵批次轉譯）

## 2. 執行方式與轉譯結果

```powershell
py 08\vm_translator.py
```

### 執行輸出紀錄
```text
已成功轉譯: 07\StackArithmetic\SimpleAdd\SimpleAdd.vm -> 07\StackArithmetic\SimpleAdd\SimpleAdd.asm
已成功轉譯: 07\StackArithmetic\StackTest\StackTest.vm -> 07\StackArithmetic\StackTest\StackTest.asm
已成功轉譯: 07\MemoryAccess\BasicTest\BasicTest.vm -> 07\MemoryAccess\BasicTest\BasicTest.asm
已成功轉譯: 07\MemoryAccess\PointerTest\PointerTest.vm -> 07\MemoryAccess\PointerTest\PointerTest.asm
已成功轉譯: 07\MemoryAccess\StaticTest\StaticTest.vm -> 07\MemoryAccess\StaticTest\StaticTest.asm
已成功轉譯: 08\ProgramFlow\BasicLoop\BasicLoop.vm -> 08\ProgramFlow\BasicLoop\BasicLoop.asm
已成功轉譯: 08\ProgramFlow\FibonacciSeries\FibonacciSeries.vm -> 08\ProgramFlow\FibonacciSeries\FibonacciSeries.asm
已成功轉譯: 08\FunctionCalls\SimpleFunction\SimpleFunction.vm -> 08\FunctionCalls\SimpleFunction\SimpleFunction.asm
已成功轉譯: 08\FunctionCalls\NestedCall -> 08\FunctionCalls\NestedCall\NestedCall.asm
已成功轉譯: 08\FunctionCalls\FibonacciElement -> 08\FunctionCalls\FibonacciElement\FibonacciElement.asm
已成功轉譯: 08\FunctionCalls\StaticsTest -> 08\FunctionCalls\StaticsTest\StaticsTest.asm
```

## 3. 產出檔案列表

| 章節 | 測試項目 | 原始虛擬機碼 | 轉譯後組合語言 |
| :--- | :--- | :--- | :--- |
| 第 7 章 | SimpleAdd | [SimpleAdd.vm](../07/StackArithmetic/SimpleAdd/SimpleAdd.vm) | [SimpleAdd.asm](../07/StackArithmetic/SimpleAdd/SimpleAdd.asm) |
| 第 7 章 | StackTest | [StackTest.vm](../07/StackArithmetic/StackTest/StackTest.vm) | [StackTest.asm](../07/StackArithmetic/StackTest/StackTest.asm) |
| 第 7 章 | BasicTest | [BasicTest.vm](../07/MemoryAccess/BasicTest/BasicTest.vm) | [BasicTest.asm](../07/MemoryAccess/BasicTest/BasicTest.asm) |
| 第 7 章 | PointerTest | [PointerTest.vm](../07/MemoryAccess/PointerTest/PointerTest.vm) | [PointerTest.asm](../07/MemoryAccess/PointerTest/PointerTest.asm) |
| 第 7 章 | StaticTest | [StaticTest.vm](../07/MemoryAccess/StaticTest/StaticTest.vm) | [StaticTest.asm](../07/MemoryAccess/StaticTest/StaticTest.asm) |
| 第 8 章 | BasicLoop | [BasicLoop.vm](./ProgramFlow/BasicLoop/BasicLoop.vm) | [BasicLoop.asm](./ProgramFlow/BasicLoop/BasicLoop.asm) |
| 第 8 章 | FibonacciSeries | [FibonacciSeries.vm](./ProgramFlow/FibonacciSeries/FibonacciSeries.vm) | [FibonacciSeries.asm](./ProgramFlow/FibonacciSeries/FibonacciSeries.asm) |
| 第 8 章 | SimpleFunction | [SimpleFunction.vm](./FunctionCalls/SimpleFunction/SimpleFunction.vm) | [SimpleFunction.asm](./FunctionCalls/SimpleFunction/SimpleFunction.asm) |
| 第 8 章 | NestedCall | [Sys.vm](./FunctionCalls/NestedCall/Sys.vm) | [NestedCall.asm](./FunctionCalls/NestedCall/NestedCall.asm) |
| 第 8 章 | FibonacciElement | [Main.vm](./FunctionCalls/FibonacciElement/Main.vm) / [Sys.vm](./FunctionCalls/FibonacciElement/Sys.vm) | [FibonacciElement.asm](./FunctionCalls/FibonacciElement/FibonacciElement.asm) |
| 第 8 章 | StaticsTest | [Class1.vm](./FunctionCalls/StaticsTest/Class1.vm) / [Class2.vm](./FunctionCalls/StaticsTest/Class2.vm) / [Sys.vm](./FunctionCalls/StaticsTest/Sys.vm) | [StaticsTest.asm](./FunctionCalls/StaticsTest/StaticsTest.asm) |

## 4. 聲明

本作業之 `vm_translator.py` 程式碼與說明文件係透過 AI 協作輔助完成，並於本地環境實際執行產生所有 `.asm` 組合語言檔案。