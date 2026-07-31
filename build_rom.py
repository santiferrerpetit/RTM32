#!/usr/bin/env python3
"""
Generador de ROM boot minima para STX4/RTM32 (binario RTM32-0.1.0, manual actualizado Jul 2026).

Codificacion verificada contra el simulador real (Tablas B.1/B.2 del manual, Cap. 6-7):
  - LCI  (opcode=00100, h=1) -> R[rt] = C16(simm, R[rs]): concatena simm en la mitad alta
  - XORI (opcode=00111, h=0) -> R[rt] = R[rs] ^ E16(simm,0): con $zero sirve de carga inmediata
  - SH   (opcode=01010)      -> M[R[rs] + imm] = R[rt][15:0]
  - J    (opcode=00001, so=00) -> PC = PC + 4 + 4*E25(elimm,S)

Registros fisicos (Tabla 3.1 del manual nuevo, YA NO requieren traduccion MIPS):
  $t0=14, $t1=15, $zero=0

Direccion UART verificada empiricamente en el simulador: 0xFFFFFF00 (escribir ahi
emite el byte bajo por la consola UART). No esta documentada en el manual (Cap. 9
"Entrada/Salida" figura como "PRONTO..." / no escrito todavia).

La ROM se ubica en 0x0000 de memoria de usuario y se inyecta palabra por palabra
via debugger (set [addr] word) porque:
  - 'load rom.bin exact' espera un formato snapshot interno (magic+version+arch), no un binario raw.
  - El flag '-r/--rom FILE' documentado en el manual para bootear desde el vector de
    reset real (0xF0000000) esta presente en '--help' pero NO tiene efecto en este build:
    probado con '-r rom.bin' y el log siempre reporta 'CPU PC initialized to 0x00000000'
    (el mensaje de la ruta sin ROM), nunca 'CPU anchored at reset vector'. Por eso se
    sigue arrancando en 0x0000 (RAM de usuario) en vez del vector de reset arquitectural.
"""

import struct
import os

MEM_SIZE = 64 * 1024  # 64 KB

T0 = 14   # registro puntero a UART (fisico, Tabla 3.1: $t0)
T1 = 15   # registro dato temporal ($t1)
ZERO = 0

UART_ADDR = 0xFFFFFF00
message = b"ROM OK\r\n"


def write_word(mem: bytearray, addr: int, word: int):
    if addr + 4 > MEM_SIZE:
        raise ValueError(f"Direccion 0x{addr:08X} fuera de rango")
    mem[addr:addr + 4] = struct.pack('<I', word & 0xFFFFFFFF)


def enc_i_ext(opcode: int, rs: int, rt: int, h: int, simm: int) -> int:
    """Formato I con inmediato extendido de 16 bits (fig. 6.3): opcode|rs|rt|h|simm."""
    return (opcode << 27) | (rs << 22) | (rt << 17) | (h << 16) | (simm & 0xFFFF)


def enc_i(opcode: int, rs: int, rt: int, imm: int) -> int:
    """Formato I basico de 17 bits de inmediato (fig. 6.2): opcode|rs|rt|imm."""
    return (opcode << 27) | (rs << 22) | (rt << 17) | (imm & 0x1FFFF)


def enc_j(opcode: int, so: int, elimm: int) -> int:
    """Formato J para J/JAL (fig. 6.7): opcode|so(2)|elimm(25)."""
    return (opcode << 27) | (so << 25) | (elimm & 0x1FFFFFF)


def build_rom() -> bytearray:
    mem = bytearray(MEM_SIZE)
    pc = 0x0000

    # 1. LCI $t0, $t0, 0xFFFF (h=1) -> R[t0] = C16(0xFFFF, R[t0]) = 0xFFFF0000 (t0 parte en 0 tras reset)
    write_word(mem, pc, enc_i_ext(0b00100, T0, T0, 1, 0xFFFF))
    pc += 4

    # 2. XORI $t0, $t0, 0xFF00 (h=0) -> R[t0] = 0xFFFF0000 ^ 0x0000FF00 = 0xFFFFFF00
    write_word(mem, pc, enc_i_ext(0b00111, T0, T0, 0, 0xFF00))
    pc += 4

    # 3. Por cada byte del mensaje: XORI $t1, $zero, byte (h=0); SH $t0, $t1, 0
    for byte in message:
        write_word(mem, pc, enc_i_ext(0b00111, ZERO, T1, 0, byte))
        pc += 4
        write_word(mem, pc, enc_i(0b01010, T0, T1, 0))
        pc += 4

    # 4. Loop infinito: J a la propia direccion (elimm = -1 palabras: PC+4+4*(-1) = PC)
    loop_addr = pc
    write_word(mem, pc, enc_j(0b00001, 0b00, -1))
    pc += 4

    # Datos de referencia en 0x0100 (no usados por la CPU, solo para debug/dump)
    for i, byte in enumerate(message):
        mem[0x0100 + i] = byte

    return mem


if __name__ == "__main__":
    rom = build_rom()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rom.bin")
    with open(out_path, "wb") as f:
        f.write(rom)
    print(f"Generado: {out_path} ({len(rom)} bytes)")
    print("\nDump de instrucciones de boot:")
    for addr in range(0x0, 0x60, 4):
        word = struct.unpack('<I', rom[addr:addr + 4])[0]
        if word != 0:
            print(f"  0x{addr:04X}: 0x{word:08X}")
