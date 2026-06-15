import re
import sys
import os
import subprocess

class RootTranspiler:
    def __init__(self):
        self.filename = ""
        self.c_code = []

    def transpile(self, filename: str):
        self.filename = filename
        if not os.path.exists(filename):
            print(f"root# Linker Error: File '{filename}' not found.")
            sys.exit(1)

        with open(filename, 'r') as f:
            source = f.read()

        lines = source.split('\n')
        
        # Core C Headers & Win32 Boilerplate setup
        self.c_code.append("// root# Native Output Backend Compiler Target")
        self.c_code.append("#include <windows.h>")
        self.c_code.append("#include <stdio.h>")
        self.c_code.append("#include <stdint.h>\n")
        
        # Global simulated memory mapping registers
        self.c_code.append("int32_t win_config[6] = {0, 0, 0, 0, 0, 0};\n")

        # Win32 Event Processing Pipeline
        self.c_code.append("""
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch(msg) {
        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hwnd, &ps);
            HBRUSH brush = CreateSolidBrush(RGB(win_config[2], win_config[3], win_config[4]));
            RECT rect;
            GetClientRect(hwnd, &rect);
            FillRect(hdc, &rect, brush);
            DeleteObject(brush);
            EndPaint(hwnd, &ps);
            break;
        }
        case WM_CLOSE:
            win_config[5] = 1; // Flag layout bit register high
            DestroyWindow(hwnd);
            break;
        case WM_DESTROY:
            PostQuitMessage(0);
            break;
        default:
            return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    return 0;
}

HWND native_hwnd = NULL;
void init_surface_native() {
    WNDCLASS wc = {0};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = GetModuleHandle(NULL);
    wc.lpszClassName = "RootNativeWindowClass";
    wc.hbrBackground = (HBRUSH)(COLOR_BACKGROUND);
    
    RegisterClass(&wc);
    native_hwnd = CreateWindowEx(
        0, "RootNativeWindowClass", "root# True Native Window",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT, win_config[0], win_config[1],
        NULL, NULL, GetModuleHandle(NULL), NULL
    );
}

void update_surface_native() {
    MSG msg;
    while(PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    InvalidateRect(native_hwnd, NULL, FALSE);
    UpdateWindow(native_hwnd);
    Sleep(16); 
}
""")

        # Track bracket balancing inside the transpiler block loop
        bracket_stack = []

        for line in lines:
            if '//' in line:
                line = line.split('//', 1)[0]
            line = line.strip()
            if not line or line.startswith("include "):
                continue
                
            if line.startswith("fn main() {"):
                self.c_code.append("int main() {")
                bracket_stack.append("main")
                continue
            
            if line == "unsafe {":
                self.c_code.append("    // --- ENTERING UNSAFE SPACE ---")
                bracket_stack.append("unsafe")
                continue

            if line == "}":
                if bracket_stack:
                    context = bracket_stack.pop()
                    if context == "unsafe":
                        self.c_code.append("    // --- EXITING UNSAFE SPACE ---")
                    elif context in ["while", "if", "main"]:
                        self.c_code.append("}")
                continue

            self.parse_line(line, bracket_stack)

        # Write out to native compilation layer
        c_filename = "build_out.c"
        with open(c_filename, 'w') as f:
            f.write("\n".join(self.c_code))

        exe_filename = filename.replace(".root", ".exe")
        print(f"[Compiler Linker]: Compiling native output architecture executable binary target...")
        
        compile_cmd = f"gcc {c_filename} -o {exe_filename} -lgdi32 -luser32"
        result = subprocess.run(compile_cmd, shell=True)

        if result.returncode == 0:
            print(f"[Compilation Success]: Transpiled assembly successfully bound to binary -> {exe_filename}")
            if os.path.exists(c_filename):
                os.remove(c_filename)
        else:
            print("[Compilation Error]: Native C generation layer failed to compile down to machine binary.")

    def parse_line(self, line: str, bracket_stack: list):
        # Variable layout declaration bindings mapping directly into standard C datatypes
        let_match = re.match(r"^let\s+(mut\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*);?$", line)
        if let_match:
            var_name = let_match.group(2)
            expr = let_match.group(3).rstrip(';').strip()
            cleaned_expr = self.translate_expr(expr)
            self.c_code.append(f"    int32_t {var_name} = {cleaned_expr};")
            return

        # Dereferencing Pointer Memory Mutations (*(win_config + 1) = val;)
        if line.startswith("*") and "=" in line:
            parts = line.split("=", 1)
            ptr_expr = parts[0].strip()
            val_expr = parts[1].rstrip(';').strip()
            self.c_code.append(f"    {ptr_expr} = {self.translate_expr(val_expr)};")
            return

        # Handle variable updates (is_running = 0;)
        assign_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*);?$", line)
        if assign_match:
            var_name = assign_match.group(1)
            expr = assign_match.group(2).rstrip(';').strip()
            self.c_code.append(f"    {var_name} = {self.translate_expr(expr)};")
            return

        # Map built runtime custom functions directly onto Win32 wrappers
        if "init_surface(" in line:
            self.c_code.append("    init_surface_native();")
            return
            
        if "update_surface(" in line:
            self.c_code.append("    update_surface_native();")
            return

        # Control Structures
        if line.startswith("while ") and line.endswith("{"):
            condition = line.replace("while ", "").rstrip("{").strip()
            self.c_code.append(f"    while ({self.translate_expr(condition)}) {{")
            bracket_stack.append("while")
            return

        if line.startswith("if ") and line.endswith("{"):
            condition = line.replace("if ", "").rstrip("{").strip()
            self.c_code.append(f"    if ({self.translate_expr(condition)}) {{")
            bracket_stack.append("if")
            return

        # Basic Native STDOUT print formatting bindings
        if line.startswith("print(") and line.endswith(");"):
            content = line[6:-2].strip()
            if content.startswith('"') and content.endswith('"'):
                self.c_code.append(f'    printf("%s\\n", {content});')
            else:
                self.c_code.append(f'    printf("%d\\n", {self.translate_expr(content)});')
            return

    def translate_expr(self, expr: str) -> str:
        return expr.rstrip(';')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python root_compiler.py <filename.root>")
        sys.exit(1)
    transpiler = RootTranspiler()
    transpiler.transpile(sys.argv[1])
