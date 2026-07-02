#!/usr/bin/env python3
"""Genera testsuite.bin: dump de memoria STX4 (64KB) con instrucciones y datos de prueba."""
import struct, sys, os

# Importar las funciones de encoding del script de pruebas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_tests import build_tests

MEM_SIZE = 64 * 1024  # 64KB

# Crear memoria limpia
mem = bytearray(MEM_SIZE)

def write_word(addr: int, word: int):
    """Escribe una palabra de 32 bits en little-endian en la dirección addr."""
    if addr + 4 > MEM_SIZE:
        raise ValueError(f"Dirección 0x{addr:08X} fuera de rango")
    mem[addr:addr+4] = struct.pack('<I', word)

# Reconstruir todos los tests y poblar memoria
tests = build_tests()
for t in tests:
    # Instrucción principal
    write_word(t.instr_addr, t.instr_word)
    # Setup: memoria de datos y verificaciones
    for cmd in t.setup_cmds:
        kind = cmd[0]
        if kind == "mem":
            write_word(cmd[1], cmd[2])

out_path = "/Users/santiferrerpetit/Documents/SimuladorCoba/testsuite.bin"
with open(out_path, "wb") as f:
    f.write(mem)

print(f"Generado: {out_path} ({MEM_SIZE} bytes)")
print(f"Instrucciones escritas: {len(tests)}")
print(f"Última instrucción en: 0x{tests[-1].instr_addr:08X}")

# Verificar cabecera con hexdump de las primeras 4 instrucciones
print("\nPrimeras palabras (hexdump little-endian):")
for t in tests[:4]:
    b = mem[t.instr_addr:t.instr_addr+4]
    print(f"  0x{t.instr_addr:08X}: {' '.join(f'{x:02X}' for x in b)}  <-- {t.instr_str}")
