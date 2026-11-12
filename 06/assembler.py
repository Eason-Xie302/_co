import os
import sys

# 預設符號表 (Predefined Symbols)
PREDEFINED_SYMBOLS = {
    "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
    "R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5, "R6": 6, "R7": 7,
    "R8": 8, "R9": 9, "R10": 10, "R11": 11, "R12": 12, "R13": 13, "R14": 14, "R15": 15,
    "SCREEN": 16384, "KBD": 24576
}

# C-instruction 的 comp 對照表
COMP_TABLE = {
    "0":   "0101010", "1":   "0111111", "-1":  "0111010",
    "D":   "0001100", "A":   "0110000", "!D":  "0001101",
    "!A":  "0110001", "-D":  "0001111", "-A":  "0110011",
    "D+1": "0011111", "A+1": "0110111", "D-1": "0001110",
    "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
    "A-D": "0000111", "D&A": "0000000", "D|A": "0010101",
    "M":   "1110000", "!M":  "1110001", "-M":  "1110011",
    "M+1": "1110111", "M-1": "1110010", "D+M": "1000010",
    "D-M": "1010011", "M-D": "1000111", "D&M": "1000000",
    "D|M": "1010101"
}

# C-instruction 的 dest 對照表
DEST_TABLE = {
    "":    "000", "M":   "001", "D":   "010", "MD":  "011",
    "A":   "100", "AM":  "101", "AD":  "110", "AMD": "111"
}

# C-instruction 的 jump 對照表
JUMP_TABLE = {
    "":    "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111"
}

def clean_lines(lines):
    """移除註解與空白行"""
    cleaned = []
    for line in lines:
        line = line.split("//")[0].strip()
        if line:
            cleaned.append(line)
    return cleaned

def first_pass(lines, symbols):
    """第一階段：掃描 (LABEL) 標籤並記錄對應的 ROM 位址"""
    rom_address = 0
    instructions = []
    for line in lines:
        if line.startswith("(") and line.endswith(")"):
            label = line[1:-1]
            symbols[label] = rom_address
        else:
            instructions.append(line)
            rom_address += 1
    return instructions

def second_pass(instructions, symbols):
    """第二階段：將 A 指令與 C 指令轉換為 16-bit 二進位機器碼"""
    ram_address = 16
    machine_code = []

    for inst in instructions:
        if inst.startswith("@"):
            # A-instruction
            symbol = inst[1:]
            if symbol.isdigit():
                address = int(symbol)
            else:
                if symbol not in symbols:
                    symbols[symbol] = ram_address
                    ram_address += 1
                address = symbols[symbol]
            machine_code.append(f"0{address:015b}")
        else:
            # C-instruction: dest=comp;jump
            dest, comp, jump = "", inst, ""
            if "=" in comp:
                dest, comp = comp.split("=")
            if ";" in comp:
                comp, jump = comp.split(";")
            
            code = "111" + COMP_TABLE[comp] + DEST_TABLE[dest] + JUMP_TABLE[jump]
            machine_code.append(code)

    return machine_code

def assemble_file(asm_path):
    """組譯單一 .asm 檔案並輸出 .hack 檔案"""
    with open(asm_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    symbols = PREDEFINED_SYMBOLS.copy()
    cleaned = clean_lines(raw_lines)
    instructions = first_pass(cleaned, symbols)
    binary_lines = second_pass(instructions, symbols)

    hack_path = os.path.splitext(asm_path)[0] + ".hack"
    with open(hack_path, "w", encoding="utf-8") as f:
        f.write("\n".join(binary_lines) + "\n")
    print(f"已成功組譯: {asm_path} -> {hack_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        assemble_file(sys.argv[1])
    else:
        # 自動尋找 06 資料夾底下所有的 .asm 檔案並轉換成 .hack
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".asm"):
                    assemble_file(os.path.join(root, file))