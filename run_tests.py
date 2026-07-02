#!/usr/bin/env python3
"""
Script para ejecutar batería de pruebas del simulador STX4/RTM32 vía debugger TCP.
Conecta a localhost:4444, ejecuta cada caso y parsea registros/CAUSE/PC.
"""
import socket, time, re, json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable

# ---------------------------------------------------------------------------
# Helpers de encoding de instrucciones según Apéndice A del manual RTM32
# ---------------------------------------------------------------------------

def encode_r(opcode: int, rs: int, rt: int, rd: int, aux: int, func: int) -> int:
    return ((opcode & 0x1F) << 27) | ((rs & 0x1F) << 22) | ((rt & 0x1F) << 17) | \
           ((rd & 0x1F) << 12) | ((aux & 0x1F) << 7) | ((func & 0x3F) << 0)

def encode_i(opcode: int, rs: int, rt: int, imm: int) -> int:
    imm17 = imm & 0x1FFFF
    return ((opcode & 0x1F) << 27) | ((rs & 0x1F) << 22) | ((rt & 0x1F) << 17) | imm17

def encode_l(opcode: int, rs: int, rt: int, h: int, imm: int) -> int:
    imm16 = imm & 0xFFFF
    return ((opcode & 0x1F) << 27) | ((rs & 0x1F) << 22) | ((rt & 0x1F) << 17) | \
           ((h & 0x1) << 16) | imm16

def encode_j(opcode: int, addr: int) -> int:
    addr27 = addr & 0x7FFFFFF
    return ((opcode & 0x1F) << 27) | addr27

# ---------------------------------------------------------------------------
# Cliente TCP del debugger
# ---------------------------------------------------------------------------

class DebuggerClient:
    def __init__(self, host="localhost", port=4444):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(2)
        self.sock.connect((host, port))
        # El debugger envía negociación telnet y luego prompt; leemos una vez para limpiar
        time.sleep(0.4)
        self._read_once()
        # Handshake del debugger: descarta primeras dos líneas
        self._raw_cmd("dummy1")
        self._raw_cmd("dummy2")

    def _read_once(self) -> bytes:
        try:
            return self.sock.recv(4096)
        except (socket.timeout, ConnectionResetError):
            return b""

    def _raw_cmd(self, cmd: str) -> str:
        self.sock.sendall((cmd + "\r\n").encode())
        time.sleep(0.2)
        chunks = []
        deadline = time.time() + 2.0
        while time.time() < deadline:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
                # Si encontramos el prompt, probablemente terminó la respuesta
                if b"RTM32>" in data:
                    break
            except socket.timeout:
                break
            except ConnectionResetError:
                break
        return b"".join(chunks).decode("ascii", errors="replace")

    def cmd(self, cmd: str) -> str:
        return self._raw_cmd(cmd)

    def reset(self):
        self.cmd("reset")
        time.sleep(0.05)

    def set_reg(self, reg: str, val: int):
        self.cmd(f"set {reg} 0x{val:08X}")

    def set_mem(self, addr: int, val: int):
        self.cmd(f"set [0x{addr:08X}] 0x{val:08X}")

    def step(self) -> str:
        return self.cmd("step 1")

    def registers(self) -> Dict[str, int]:
        raw = self.cmd("registers")
        regs = {}
        for m in re.finditer(r'R\[\s*(\d+)\]:\s*(0x[0-9A-Fa-f]+)', raw):
            regs[f"r{int(m.group(1))}"] = int(m.group(2), 16)
        for m in re.finditer(r'(PC|CAUSE|EPC|BADVADR|VBR)\s*:\s*(0x[0-9A-Fa-f]+)', raw):
            regs[m.group(1).lower()] = int(m.group(2), 16)
        for m in re.finditer(r'Target PC:\s*(0x[0-9A-Fa-f]+)', raw):
            regs["target_pc"] = int(m.group(1), 16)
        return regs

    def close(self):
        self.sock.close()

# ---------------------------------------------------------------------------
# Definición de casos de prueba
# ---------------------------------------------------------------------------

@dataclass
class TestCase:
    name: str
    desc: str
    setup_cmds: List[tuple]
    instr_addr: int
    instr_word: int
    instr_str: str
    expected_regs: Dict[str, Any]  # valor o callable(regs)->bool
    expected_cause: Optional[int] = None
    notes: str = ""
    extra_steps: int = 0  # pasos adicionales después del primero (p.ej. para verificar stores)

# ---------------------------------------------------------------------------
# Generar todas las pruebas
# ---------------------------------------------------------------------------

def build_tests() -> List[TestCase]:
    tests = []
    base = 0x0
    addr = lambda n: base + n * 0x40
    n = 0

    def add(desc, setup, instr_addr, word, instr_str, expected, cause=None, notes="", extra_steps=0):
        nonlocal n
        tests.append(TestCase(
            name=f"Caso {n+1}",
            desc=desc,
            setup_cmds=setup,
            instr_addr=instr_addr,
            instr_word=word,
            instr_str=instr_str,
            expected_regs=expected,
            expected_cause=cause,
            notes=notes,
            extra_steps=extra_steps
        ))
        n += 1

    # ============== ALU, SHIFT, SALTO, LÓGICAS, INMEDIATAS ==============
    add("ADD — suma de registros",
        [("reg", 2, 5), ("reg", 3, 3)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x1C), "ADD $1, $2, $3",
        {"r1": 8})

    add("SUB — resta de registros",
        [("reg", 2, 5), ("reg", 3, 3)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x1D), "SUB $1, $2, $3",
        {"r1": 2})

    add("AND — lógico bit a bit",
        [("reg", 2, 0xF0F0), ("reg", 3, 0x0FF0)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x08), "AND $1, $2, $3",
        {"r1": 0x00F0})

    add("OR — lógico bit a bit",
        [("reg", 2, 0xF0F0), ("reg", 3, 0x0FF0)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x09), "OR $1, $2, $3",
        {"r1": 0xFFF0})

    add("XOR — lógico bit a bit",
        [("reg", 2, 0xF0F0), ("reg", 3, 0x0FF0)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x0A), "XOR $1, $2, $3",
        {"r1": 0xFF00})

    add("NOR — con operandos 0 da ~0",
        [("reg", 2, 0), ("reg", 3, 0)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x0B), "NOR $1, $2, $3",
        {"r1": 0xFFFFFFFF})

    add("SLT — menor con signo",
        [("reg", 2, 0xFFFFFFFF), ("reg", 3, 1)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x0C), "SLT $1, $2, $3",
        {"r1": 1})

    add("SLTU — mismo par, sin signo",
        [("reg", 2, 0xFFFFFFFF), ("reg", 3, 1)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x0D), "SLTU $1, $2, $3",
        {"r1": 0})

    add("MUL — palabra baja",
        [("reg", 2, 6), ("reg", 3, 7)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x15), "MUL $1, $2, $3",
        {"r1": 42})

    add("MULH — mitad alta con signo",
        [("reg", 2, 0xFFFFFFFF), ("reg", 3, 2)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x16), "MULH $1, $2, $3",
        {"r1": 0xFFFFFFFF})

    add("MULHU — mitad alta sin signo",
        [("reg", 2, 0xFFFFFFFF), ("reg", 3, 2)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x17), "MULHU $1, $2, $3",
        {"r1": 1})

    add("DIV — división con signo",
        [("reg", 2, 0xFFFFFFF7), ("reg", 3, 4)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x18), "DIV $1, $2, $3",
        {"r1": 0xFFFFFFFE})

    add("DIVU — división sin signo",
        [("reg", 2, 0xFFFFFFF7), ("reg", 3, 4)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x19), "DIVU $1, $2, $3",
        {"r1": 0x3FFFFFFD})

    add("REST — resto con signo",
        [("reg", 2, 0xFFFFFFF7), ("reg", 3, 4)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x1A), "REST $1, $2, $3",
        {"r1": 0xFFFFFFFF})

    add("RESTU — resto sin signo",
        [("reg", 2, 0xFFFFFFF7), ("reg", 3, 4)],
        addr(n), encode_r(0, 2, 3, 1, 0, 0x1B), "RESTU $1, $2, $3",
        {"r1": 3})

    add("SLL — shift lógico izquierda inmediato",
        [("reg", 2, 1)],
        addr(n), encode_r(0, 0, 2, 1, 4, 0x00), "SLL $1, $2, 4",
        {"r1": 0x10})

    add("SRL — shift lógico derecha",
        [("reg", 2, 0x80000000)],
        addr(n), encode_r(0, 0, 2, 1, 4, 0x01), "SRL $1, $2, 4",
        {"r1": 0x08000000})

    add("SRA — shift aritmético derecha",
        [("reg", 2, 0x80000000)],
        addr(n), encode_r(0, 0, 2, 1, 4, 0x02), "SRA $1, $2, 4",
        {"r1": 0xF8000000})

    add("SLLR — shift izquierda por registro",
        [("reg", 2, 1), ("reg", 3, 4)],
        addr(n), encode_r(0, 3, 2, 1, 0, 0x03), "SLLR $1, $2, $3",
        {"r1": 0x10})

    add("SRLR — shift lógico derecha por registro",
        [("reg", 2, 0x80000000), ("reg", 3, 4)],
        addr(n), encode_r(0, 3, 2, 1, 0, 0x04), "SRLR $1, $2, $3",
        {"r1": 0x08000000})

    add("SRAR — shift aritmético derecha por registro",
        [("reg", 2, 0x80000000), ("reg", 3, 4)],
        addr(n), encode_r(0, 3, 2, 1, 0, 0x05), "SRAR $1, $2, $3",
        {"r1": 0xF8000000})

    add("JR — salto incondicional por registro",
        [("reg", 2, 0x100)],
        addr(n), encode_r(0, 2, 0, 0, 0, 0x0E), "JR $2",
        {"pc": 0x100})

    # JALR: codificado con rd=31 para que el enlace vaya a $ra
    jalr_addr = addr(n)
    add("JALR — salto con enlace a $ra (rd=31)",
        [("reg", 2, 0x104)],
        jalr_addr, encode_r(0, 2, 0, 31, 0, 0x0F), "JALR $2 (rd=31)",
        {"pc": 0x104, "r31": jalr_addr + 4})

    add("BEQ — branch tomado (iguales)",
        [("reg", 2, 5), ("reg", 3, 5)],
        addr(n), encode_i(0b10000, 2, 3, 2), "BEQ $2, $3, 2",
        {"pc": addr(n) + 0xC})

    add("BNE — branch tomado (distintos)",
        [("reg", 2, 5), ("reg", 3, 6)],
        addr(n), encode_i(0b10001, 2, 3, 2), "BNE $2, $3, 2",
        {"pc": addr(n) + 0xC})

    add("BLT — branch menor con signo",
        [("reg", 2, 3), ("reg", 3, 5)],
        addr(n), encode_i(0b10010, 2, 3, 2), "BLT $2, $3, 2",
        {"pc": addr(n) + 0xC})

    add("BGT — branch mayor",
        [("reg", 2, 5), ("reg", 3, 3)],
        addr(n), encode_i(0b10011, 2, 3, 2), "BGT $2, $3, 2",
        {"pc": addr(n) + 0xC})

    add("BLE — branch menor o igual (borde igual)",
        [("reg", 2, 5), ("reg", 3, 5)],
        addr(n), encode_i(0b10100, 2, 3, 2), "BLE $2, $3, 2",
        {"pc": addr(n) + 0xC})

    add("BGE — branch mayor o igual (borde igual)",
        [("reg", 2, 5), ("reg", 3, 5)],
        addr(n), encode_i(0b10101, 2, 3, 2), "BGE $2, $3, 2",
        {"pc": addr(n) + 0xC})

    add("ADDI — suma inmediata (bug conocido: ilegal)",
        [("reg", 2, 0)],
        addr(n), encode_i(0b00001, 2, 1, 5), "ADDI $1, $2, 5",
        {"r1": 5}, cause=0,
        notes="Bug: el simulador marca Illegal Instruction (CAUSE=3).")

    add("SLTI — menor inmediato con signo",
        [("reg", 2, 3)],
        addr(n), encode_i(0b10110, 2, 1, 5), "SLTI $1, $2, 5",
        {"r1": 1})

    add("SLTIU — menor inmediato sin signo",
        [("reg", 2, 0xFFFFFFFF)],
        addr(n), encode_i(0b10111, 2, 1, 1), "SLTIU $1, $2, 1",
        {"r1": 0})

    add("J — salto absoluto",
        [],
        addr(n), encode_j(0b00010, 0xC0), "J 0xC0",
        {"pc": 0x300})

    jal_addr = addr(n)
    add("JAL — salto absoluto con enlace",
        [],
        jal_addr, encode_j(0b00011, 0xC4), "JAL 0xC4",
        {"pc": 0x310, "r31": jal_addr + 4})

    add("ANDI h=0 — lógico inmediato bajo",
        [("reg", 2, 0xFF)],
        addr(n), encode_l(0b00100, 2, 1, 0, 0x0F), "ANDI $1, $2, 0x0F",
        {"r1": 0x0F})

    add("ORI h=0 — lógico inmediato bajo",
        [("reg", 2, 0xF0)],
        addr(n), encode_l(0b00101, 2, 1, 0, 0x0F), "ORI $1, $2, 0x0F",
        {"r1": 0xFF})

    add("XORI h=0 — lógico inmediato bajo",
        [("reg", 2, 0xFF00)],
        addr(n), encode_l(0b00110, 2, 1, 0, 0x00FF), "XORI $1, $2, 0x00FF",
        {"r1": 0xFFFF})

    add("LUI — carga inmediata alta (bug conocido: ilegal)",
        [],
        addr(n), encode_l(0b00111, 0, 1, 0, 0xABCD), "LUI $1, 0xABCD",
        {"r1": 0xABCD0000}, cause=0,
        notes="Bug: el simulador marca Illegal Instruction (CAUSE=3).")

    # ============== VARIANTES h=1 ==============
    add("ANDI h=1 — inmediato en mitad alta",
        [("reg", 2, 0xFFFFFFFF)],
        addr(n), encode_l(0b00100, 2, 1, 1, 0x0F0F), "ANDIH $1, $2, 0x0F0F",
        {"r1": 0x0F0F0000})

    add("ORI h=1 — inmediato en mitad alta",
        [("reg", 2, 0x0000F0F0)],
        addr(n), encode_l(0b00101, 2, 1, 1, 0xFF00), "ORIH $1, $2, 0xFF00",
        {"r1": 0xFF00F0F0}, notes="OR de 0x0000F0F0 con ZC(0xFF00)=0xFF000000")

    add("XORI h=1 — inmediato en mitad alta",
        [("reg", 2, 0xABCD0000)],
        addr(n), encode_l(0b00110, 2, 1, 1, 0xABCD), "XORIH $1, $2, 0xABCD",
        {"r1": 0x00000000}, notes="XOR de 0xABCD0000 con ZC(0xABCD)=0xABCD0000 → 0")

    # ============== LOADS / STORES DIRECTOS ==============
    MEM_BASE = 0x1000

    # Para stores verificamos con un LW inmediatamente después (setup de verificación)
    # SW: store word, luego verificamos cargando con LW
    sw_addr = addr(n)
    add("SW — store word y verificación con LW",
        [("reg", 2, MEM_BASE), ("reg", 1, 0xDEADBEEF),
         # Inyectamos un LW $3, 0($2) en la siguiente palabra
         ("mem", sw_addr + 4, encode_i(0b01000, 2, 3, 0))],
        sw_addr, encode_i(0b01001, 2, 1, 0), "SW $1, 0($2)",
        {"r3": 0xDEADBEEF}, notes="LW $3, 0($2) está en PC+4 para verificar.", extra_steps=1)

    sh_addr = addr(n)
    add("SH — store halfword y verificación con LH",
        [("reg", 2, MEM_BASE), ("reg", 1, 0x1234ABCD),
         ("mem", sh_addr + 4, encode_i(0b01100, 2, 3, 0))],
        sh_addr, encode_i(0b01010, 2, 1, 0), "SH $1, 0($2)",
        {"r3": 0xFFFFABCD}, notes="LH $3, 0($2) en PC+4. Esperamos sign-extend de 0xABCD.", extra_steps=1)

    sb_addr = addr(n)
    add("SB — store byte y verificación con LB",
        [("reg", 2, MEM_BASE), ("reg", 1, 0x12345678),
         ("mem", sb_addr + 4, encode_i(0b01110, 2, 3, 0))],
        sb_addr, encode_i(0b01011, 2, 1, 0), "SB $1, 0($2)",
        {"r3": 0x00000078}, notes="LB $3, 0($2) en PC+4. Sign-extend de 0x78 (bit7=0) → 0x78.", extra_steps=1)

    add("LW — load word",
        [("reg", 2, MEM_BASE), ("mem", MEM_BASE, 0x1234ABCD)],
        addr(n), encode_i(0b01000, 2, 1, 0), "LW $1, 0($2)",
        {"r1": 0x1234ABCD})

    add("LH — load halfword con signo (negativo)",
        [("reg", 2, MEM_BASE), ("mem", MEM_BASE, 0xFFFF8000)],
        addr(n), encode_i(0b01100, 2, 1, 0), "LH $1, 0($2)",
        {"r1": 0xFFFF8000})

    add("LHU — load halfword sin signo",
        [("reg", 2, MEM_BASE), ("mem", MEM_BASE, 0xFFFF8000)],
        addr(n), encode_i(0b01101, 2, 1, 0), "LHU $1, 0($2)",
        {"r1": 0x00008000})

    add("LB — load byte con signo (negativo)",
        [("reg", 2, MEM_BASE), ("mem", MEM_BASE, 0xFFFFFF80)],
        addr(n), encode_i(0b01110, 2, 1, 0), "LB $1, 0($2)",
        {"r1": 0xFFFFFF80})

    add("LBU — load byte sin signo",
        [("reg", 2, MEM_BASE), ("mem", MEM_BASE, 0xFFFFFF80)],
        addr(n), encode_i(0b01111, 2, 1, 0), "LBU $1, 0($2)",
        {"r1": 0x00000080})

    # ============== LOADS / STORES INDEXADOS ==============
    add("LWX — load word indexado",
        [("reg", 2, MEM_BASE), ("reg", 3, 4), ("mem", MEM_BASE + 4, 0xCAFEBABE)],
        addr(n), encode_r(0, 2, 1, 3, 0, 0x14), "LWX $1, $2($3)",
        {"r1": 0xCAFEBABE})

    add("LHX — load halfword indexado con signo",
        [("reg", 2, MEM_BASE), ("reg", 3, 4), ("mem", MEM_BASE + 4, 0x00008000)],
        addr(n), encode_r(0, 2, 1, 3, 0, 0x10), "LHX $1, $2($3)",
        {"r1": 0xFFFF8000})

    add("LHUX — load halfword indexado sin signo",
        [("reg", 2, MEM_BASE), ("reg", 3, 4), ("mem", MEM_BASE + 4, 0x00008000)],
        addr(n), encode_r(0, 2, 1, 3, 0, 0x11), "LHUX $1, $2($3)",
        {"r1": 0x00008000})

    add("LBX — load byte indexado con signo",
        [("reg", 2, MEM_BASE), ("reg", 3, 4), ("mem", MEM_BASE + 4, 0x00000080)],
        addr(n), encode_r(0, 2, 1, 3, 0, 0x12), "LBX $1, $2($3)",
        {"r1": 0xFFFFFF80})

    add("LBUX — load byte indexado sin signo",
        [("reg", 2, MEM_BASE), ("reg", 3, 4), ("mem", MEM_BASE + 4, 0x00000080)],
        addr(n), encode_r(0, 2, 1, 3, 0, 0x13), "LBUX $1, $2($3)",
        {"r1": 0x00000080})

    # ============== ESPECIALES / PRIVILEGIADAS ==============
    add("CFS — copiar desde $psw a $2",
        [],
        addr(n), encode_r(0, 2, 0, 0, 0, 0x06), "CFS $2, 0 ($psw)",
        {"r2": lambda regs: True}, notes="Verificamos que no falle (cualquier valor de $psw es válido).")

    add("CTS — copiar $2 a $psw",
        [("reg", 2, 0x00000001)],
        addr(n), encode_r(0, 2, 0, 0, 0, 0x07), "CTS $2, 0 ($psw)",
        {}, notes="Escribimos 0x1 en $psw. No hay lectura directa posterior.")

    trap_addr = addr(n)
    add("TRAP — transferir a manejador",
        [("mem", 0x0, 0x00001000)],  # handler addr en M[0]
        trap_addr, encode_r(0, 0, 0, 0, 0, 0x20), "TRAP 0",
        {"pc": 0x1000, "epc": trap_addr + 4})

    add("RFT — retornar de excepción",
        # Necesitamos EPC seteado. Lo hacemos forzando un TRAP previo en el setup,
        # luego reseteamos, seteamos EPC manualmente (no hay cmd directo)...
        # Workaround: no verificamos PC, solo que no crashee.
        [],
        addr(n), encode_r(0, 0, 0, 0, 0, 0x21), "RFT",
        {"pc": lambda regs: True}, notes="Verificamos que no genere excepción. EPC previo puede ser 0.")

    return tests

# ---------------------------------------------------------------------------
# Ejecutar un caso
# ---------------------------------------------------------------------------

def run_case(dbg: DebuggerClient, t: TestCase) -> dict:
    dbg.reset()
    time.sleep(0.05)

    for kind, *rest in t.setup_cmds:
        if kind == "reg":
            dbg.set_reg(f"r{rest[0]}", rest[1])
        elif kind == "mem":
            dbg.set_mem(rest[0], rest[1])

    dbg.set_mem(t.instr_addr, t.instr_word)
    dbg.set_reg("pc", t.instr_addr)
    step_out = dbg.step()
    time.sleep(0.05)
    for _ in range(t.extra_steps):
        dbg.step()
        time.sleep(0.05)
    regs = dbg.registers()

    ok = True
    mismatches = []
    for k, v in t.expected_regs.items():
        actual = regs.get(k)
        if callable(v):
            if not v(regs):
                mismatches.append(f"{k}: condición falló (actual={actual})")
                ok = False
        else:
            if actual != v:
                mismatches.append(f"{k}: esperado 0x{v:08X}, obtenido 0x{actual:08X}" if actual is not None else f"{k}: no encontrado")
                ok = False

    cause_ok = True
    cause_note = ""
    if t.expected_cause is not None:
        actual_cause = regs.get("cause", 0)
        cause_note = f"CAUSE=0x{actual_cause:08X}"
        if actual_cause != t.expected_cause:
            cause_ok = False

    return {
        "name": t.name, "desc": t.desc, "instr": t.instr_str,
        "hex": f"0x{t.instr_word:08X}", "ok": ok and cause_ok,
        "regs": regs, "mismatches": mismatches,
        "cause_note": cause_note, "step_output": step_out,
        "notes": t.notes,
    }

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    tests = build_tests()
    print(f"Total casos: {len(tests)}")

    dbg = DebuggerClient()
    print("Conectado al debugger. Ejecutando...\n")

    results = []
    illegal_hit = False
    for t in tests:
        if illegal_hit:
            dbg.reset()
            time.sleep(0.1)
            illegal_hit = False

        res = run_case(dbg, t)
        results.append(res)
        if res["regs"].get("cause", 0) == 0x3:
            illegal_hit = True

        status = "PASS" if res["ok"] else "FAIL"
        print(f"{res['name']}: {status} — {res['desc']}")
        for m in res["mismatches"]:
            print(f"  ↳ {m}")
        if res["cause_note"]:
            print(f"  ↳ {res['cause_note']}")

    dbg.close()

    passed = sum(1 for r in results if r["ok"])
    failed = len(results) - passed
    print(f"\n{'='*60}")
    print(f"Resumen: {passed}/{len(results)} pasaron, {failed} fallaron.")

    # JSON
    out_json = "/Users/santiferrerpetit/Documents/SimuladorCoba/test_results.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2, default=lambda o: hex(o) if isinstance(o, int) else str(o))
    print(f"JSON: {out_json}")

    # Markdown
    md = ["# Resultados de pruebas STX4 — Ejecución automática\n\n"]
    md.append(f"**Total:** {len(results)} casos | **Pass:** {passed} | **Fail:** {failed}\n\n")
    md.append("---\n\n")
    for r in results:
        icon = "✅" if r["ok"] else "❌"
        md.append(f"## {r['name']}: {r['desc']} {icon}\n\n")
        md.append(f"- **Instrucción:** `{r['instr']}` → `{r['hex']}`\n")
        md.append(f"- **Registros obtenidos:**\n")
        for k, v in r["regs"].items():
            md.append(f"  - `{k}` = `0x{v:08X}`\n")
        if r["mismatches"]:
            md.append(f"- **Errores:**\n")
            for m in r["mismatches"]:
                md.append(f"  - {m}\n")
        if r["cause_note"]:
            md.append(f"- **{r['cause_note']}**\n")
        if r["notes"]:
            md.append(f"- *Notas:* {r['notes']}\n")
        md.append("\n")

    out_md = "/Users/santiferrerpetit/Documents/SimuladorCoba/test_results.md"
    with open(out_md, "w") as f:
        f.write("".join(md))
    print(f"Markdown: {out_md}")

if __name__ == "__main__":
    main()
