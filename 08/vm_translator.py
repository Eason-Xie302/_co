import os
import sys


class VMTranslator:
    def __init__(self):
        self.output = []
        self.current_file = ""
        self.current_func = ""
        self.label_id = 0
        self.call_id = 0

    def emit(self, lines):
        if isinstance(lines, list):
            self.output.extend(lines)
        else:
            self.output.append(lines)

    def write_bootstrap(self):
        self.emit([
            "// Bootstrap code",
            "@256",
            "D=A",
            "@SP",
            "M=D",
        ])
        self.write_call("Sys.init", 0)

    def write_arithmetic(self, cmd):
        self.emit(f"// {cmd}")
        if cmd == "add":
            self.emit(["@SP", "AM=M-1", "D=M", "A=A-1", "M=M+D"])
        elif cmd == "sub":
            self.emit(["@SP", "AM=M-1", "D=M", "A=A-1", "M=M-D"])
        elif cmd == "neg":
            self.emit(["@SP", "A=M-1", "M=-M"])
        elif cmd == "and":
            self.emit(["@SP", "AM=M-1", "D=M", "A=A-1", "M=M&D"])
        elif cmd == "or":
            self.emit(["@SP", "AM=M-1", "D=M", "A=A-1", "M=M|D"])
        elif cmd == "not":
            self.emit(["@SP", "A=M-1", "M=!M"])
        elif cmd in ("eq", "gt", "lt"):
            idx = self.label_id
            self.label_id += 1
            jmp = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[cmd]
            self.emit([
                "@SP", "AM=M-1", "D=M", "A=A-1", "D=M-D",
                f"@COMP_TRUE_{idx}", f"D;{jmp}",
                "@SP", "A=M-1", "M=0",
                f"@COMP_END_{idx}", "0;JMP",
                f"(COMP_TRUE_{idx})",
                "@SP", "A=M-1", "M=-1",
                f"(COMP_END_{idx})",
            ])

    def write_push_pop(self, cmd, segment, index):
        self.emit(f"// {cmd} {segment} {index}")
        seg_map = {"local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}

        if cmd == "push":
            if segment == "constant":
                self.emit([f"@{index}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1"])
            elif segment in seg_map:
                self.emit([
                    f"@{index}", "D=A", f"@{seg_map[segment]}", "A=M+D", "D=M",
                    "@SP", "A=M", "M=D", "@SP", "M=M+1",
                ])
            elif segment == "temp":
                self.emit([f"@{5 + index}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])
            elif segment == "pointer":
                ptr = "THIS" if index == 0 else "THAT"
                self.emit([f"@{ptr}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])
            elif segment == "static":
                self.emit([f"@{self.current_file}.{index}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])

        elif cmd == "pop":
            if segment in seg_map:
                self.emit([
                    f"@{index}", "D=A", f"@{seg_map[segment]}", "D=M+D",
                    "@R13", "M=D", "@SP", "AM=M-1", "D=M", "@R13", "A=M", "M=D",
                ])
            elif segment == "temp":
                self.emit(["@SP", "AM=M-1", "D=M", f"@{5 + index}", "M=D"])
            elif segment == "pointer":
                ptr = "THIS" if index == 0 else "THAT"
                self.emit(["@SP", "AM=M-1", "D=M", f"@{ptr}", "M=D"])
            elif segment == "static":
                self.emit(["@SP", "AM=M-1", "D=M", f"@{self.current_file}.{index}", "M=D"])

    def format_label(self, label):
        return f"{self.current_func}${label}" if self.current_func else label

    def write_label(self, label):
        self.emit(f"({self.format_label(label)})")

    def write_goto(self, label):
        self.emit([f"@{self.format_label(label)}", "0;JMP"])

    def write_if(self, label):
        self.emit(["@SP", "AM=M-1", "D=M", f"@{self.format_label(label)}", "D;JNE"])

    def write_function(self, func_name, n_vars):
        self.current_func = func_name
        self.emit([f"// function {func_name} {n_vars}", f"({func_name})"])
        for _ in range(n_vars):
            self.emit(["@SP", "A=M", "M=0", "@SP", "M=M+1"])

    def write_call(self, func_name, n_args):
        ret_label = f"{self.current_func or 'BOOTSTRAP'}$ret.{self.call_id}"
        self.call_id += 1
        self.emit([
            f"// call {func_name} {n_args}",
            f"@{ret_label}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1",
        ])
        for seg in ("LCL", "ARG", "THIS", "THAT"):
            self.emit([f"@{seg}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])
        self.emit([
            "@SP", "D=M", f"@{5 + n_args}", "D=D-A", "@ARG", "M=D",
            "@SP", "D=M", "@LCL", "M=D",
            f"@{func_name}", "0;JMP",
            f"({ret_label})",
        ])

    def write_return(self):
        self.emit([
            "// return",
            "@LCL", "D=M", "@R13", "M=D",
            "@5", "A=D-A", "D=M", "@R14", "M=D",
            "@SP", "AM=M-1", "D=M", "@ARG", "A=M", "M=D",
            "@ARG", "D=M+1", "@SP", "M=D",
            "@R13", "AM=M-1", "D=M", "@THAT", "M=D",
            "@R13", "AM=M-1", "D=M", "@THIS", "M=D",
            "@R13", "AM=M-1", "D=M", "@ARG", "M=D",
            "@R13", "AM=M-1", "D=M", "@LCL", "M=D",
            "@R14", "A=M", "0;JMP",
        ])

    def parse_file(self, filepath):
        self.current_file = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.split("//")[0].strip()
                if not line:
                    continue
                parts = line.split()
                cmd = parts[0]
                if cmd in ("add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"):
                    self.write_arithmetic(cmd)
                elif cmd in ("push", "pop"):
                    self.write_push_pop(cmd, parts[1], int(parts[2]))
                elif cmd == "label":
                    self.write_label(parts[1])
                elif cmd == "goto":
                    self.write_goto(parts[1])
                elif cmd == "if-goto":
                    self.write_if(parts[1])
                elif cmd == "function":
                    self.write_function(parts[1], int(parts[2]))
                elif cmd == "call":
                    self.write_call(parts[1], int(parts[2]))
                elif cmd == "return":
                    self.write_return()


def translate_target(target, base_dir=None):
    target = target.rstrip("\\/")
    if not os.path.exists(target):
        print(f"找不到路徑: {target}")
        return

    translator = VMTranslator()
    if os.path.isdir(target):
        vm_files = sorted(
            os.path.join(target, f) for f in os.listdir(target) if f.endswith(".vm")
        )
        if any(os.path.basename(f) == "Sys.vm" for f in vm_files):
            translator.write_bootstrap()
        for vf in vm_files:
            translator.parse_file(vf)
        out_path = os.path.join(target, f"{os.path.basename(target)}.asm")
    else:
        translator.parse_file(target)
        out_path = os.path.splitext(target)[0] + ".asm"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(translator.output) + "\n")

    display_in = os.path.relpath(target, base_dir) if base_dir else target
    display_out = os.path.relpath(out_path, base_dir) if base_dir else out_path
    print(f"已成功轉譯: {display_in} -> {display_out}")


def main():
    if len(sys.argv) >= 2:
        for arg in sys.argv[1:]:
            translate_target(arg)
        return

    # 無參數執行時，自動批次轉譯 07 與 08 全部測資
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_targets = [
        os.path.join("07", "StackArithmetic", "SimpleAdd", "SimpleAdd.vm"),
        os.path.join("07", "StackArithmetic", "StackTest", "StackTest.vm"),
        os.path.join("07", "MemoryAccess", "BasicTest", "BasicTest.vm"),
        os.path.join("07", "MemoryAccess", "PointerTest", "PointerTest.vm"),
        os.path.join("07", "MemoryAccess", "StaticTest", "StaticTest.vm"),
        os.path.join("08", "ProgramFlow", "BasicLoop", "BasicLoop.vm"),
        os.path.join("08", "ProgramFlow", "FibonacciSeries", "FibonacciSeries.vm"),
        os.path.join("08", "FunctionCalls", "SimpleFunction", "SimpleFunction.vm"),
        os.path.join("08", "FunctionCalls", "NestedCall"),
        os.path.join("08", "FunctionCalls", "FibonacciElement"),
        os.path.join("08", "FunctionCalls", "StaticsTest"),
    ]

    for rel_path in default_targets:
        translate_target(os.path.join(base_dir, rel_path), base_dir)


if __name__ == "__main__":
    main()