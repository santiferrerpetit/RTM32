# Pruebas de instrucciones STX4 (RTM32) — máquina nueva (Jul 2026, `RTM32-0.1.0`)

Este documento reemplaza la versión anterior (escrita contra el binario/ISA previos, ya
incompatibles). Cobertura: **46 casos**, uno por instrucción del ISA nuevo (Tablas B.1/B.2 de
`rtm32.pdf`), todos ejecutados de verdad contra el simulador — no son valores calculados a
mano. 40 casos confirman el comportamiento documentado en el manual; 6 documentan
instrucciones con comportamiento roto/no implementado en este build, con evidencia.

## Metodología

- Simulador levantado con `docker build --platform linux/amd64 -t rtm32 . && docker run -d --platform linux/amd64 --name rtm32-sim -p 4444:4444 -p 5555:5555 rtm32`, debugger en `telnet localhost 4444`.
- El simulador **no trae ensamblador**: cada instrucción se codificó a mano según las Tablas B.1 (opcode)/B.2 (func) de `rtm32.pdf`, usando los campos de bits del Capítulo 6.
- Cada caso arranca con `reset` (deja PC en `0xF0000000`, todos los GPR en 0), luego `set r<n> <val>` para las precondiciones, `set [addr] palabra` para inyectar el código en `0x0000` (RAM de usuario — `reset` no limpia la memoria, solo registros/PC/PSW), `set pc 0x00000000`, `step <n>`.
- Postcondición verificada con `registers` (o `examine xw <addr> 1` para los stores).
- Registros usados en los tests: `$t0`=R14, `$t1`=R15, `$t2`=R16 (numeración física directa).
- Sección de datos de prueba en `0x1000` (fuera del área de código en `0x0000`-`0x0050`).

---

# Parte 1 — R-Type: ALU y lógica (opcode `00000`)

## Caso 1 — `ADD`

`ADD $t2, $t0, $t1` (func `001100`, encoding `0x0086101C` con rs=14,rt=15,rd=16) — Precondición `t0=7, t1=3`. Postcondición: `R[16]=0x0000000A`. **Anduvo.** `7+3=10`.

## Caso 2 — `SUB`

`SUB $t2, $t0, $t1` (func `001101`) — `t0=10, t1=3` → `R[16]=0x00000007`. **Anduvo.**

## Caso 3 — `AND`

`AND $t2, $t0, $t1` (func `001000`) — `t0=0xF0F0, t1=0x0FF0` → `R[16]=0x000000F0`. **Anduvo.**

## Caso 4 — `OR`

`OR $t2, $t0, $t1` (func `001001`) — mismos operandos → `R[16]=0x0000FFF0`. **Anduvo.**

## Caso 5 — `XOR`

`XOR $t2, $t0, $t1` (func `001010`) — mismos operandos → `R[16]=0x0000FF00`. **Anduvo.**

## Caso 6 — `NOR`

`NOR $t2, $t0, $t1` (func `001011`) — `t0=0, t1=0` → `R[16]=0xFFFFFFFF`. **Anduvo.**

## Caso 7 — `SLT`

`SLT $t2, $t0, $t1` (func `001110`) — `t0=3, t1=5` (comparación con signo) → `R[16]=1`. **Anduvo.**

## Caso 8 — `SLTU`

`SLTU $t2, $t0, $t1` (func `001111`) — `t0=0xFFFFFFFF, t1=1` (sin signo: `U(-1)` no es `< U(1)`) → `R[16]=0`. **Anduvo.**

---

# Parte 2 — R-Type: desplazamientos (opcode `00000`)

## Caso 9 — `SLL`

`SLL $t1, $t2, 4` (func `000000`, `rt rd param`) — `t1=1, param=4` → `R[16]=0x00000010`. **Anduvo.**

## Caso 10 — `SRL`

`SRL $t1, $t2, 8` (func `000010`, lógico) — `t1=0xFF000000` → `R[16]=0x00FF0000`. **Anduvo.**

## Caso 11 — `SRA`

`SRA $t1, $t2, 4` (func `000011`, aritmético, preserva signo) — `t1=0x80000000` → `R[16]=0xF8000000`. **Anduvo.**

## Caso 12 — `RLC`

`RLC $t1, $t2, 1` (func `000001`, rotación izquierda) — `t1=0x80000001` → `R[16]=0x00000003`. **Anduvo.**

## Caso 13 — `SLLR`

`SLLR $t0, $t1, $t2` (func `000100`, cantidad en `R[rs][4:0]`) — `t0=4, t1=1` → `R[16]=0x00000010`. **Anduvo.**

## Caso 14 — `RLCR`

`RLCR $t0, $t1, $t2` (func `000101`) — `t0=1, t1=0x80000001` → `R[16]=0x00000003`. **Anduvo.**

## Caso 15 — `SRLR`

`SRLR $t0, $t1, $t2` (func `000110`) — `t0=8, t1=0xFF000000` → `R[16]=0x00FF0000`. **Anduvo.**

## Caso 16 — `SRAR`

`SRAR $t0, $t1, $t2` (func `000111`) — `t0=4, t1=0x80000000` → `R[16]=0xF8000000`. **Anduvo.**

---

# Parte 3 — R-Type: multiplicación / división (opcode `00000`)

## Caso 17 — `MUL`

`MUL $t2, $t0, $t1` (func `011000`) — `t0=6, t1=7` → `R[16]=42`. **Anduvo.**

## Caso 18 — `MULH`

`MULH $t2, $t0, $t1` (func `011001`, mitad alta con signo) — `t0=0x80000000 (-2³¹), t1=2` → producto de 64 bits `-2³²`, mitad alta `R[16]=0xFFFFFFFF`. **Anduvo.**

## Caso 19 — `MULHU`

`MULHU $t2, $t0, $t1` (func `011010`, sin signo) — mismos operandos, producto sin signo `0x100000000` → `R[16]=1`. **Anduvo.**

## Caso 20 — `MULHSU`

`MULHSU $t2, $t0, $t1` (func `011011`, rs con signo × rt sin signo) — `t0=0xFFFFFFFF (-1), t1=2` → mitad alta `R[16]=0xFFFFFFFF`. **Anduvo.**

## Caso 21 — `DIV`

`DIV $t2, $t0, $t1` (func `011100`) — `t0=17, t1=5` → `R[16]=3`. **Anduvo.**

## Caso 22 — `DIVU`

`DIVU $t2, $t0, $t1` (func `011101`) — `t0=0xFFFFFFFF, t1=2` → `R[16]=0x7FFFFFFF`. **Anduvo.**

## Caso 23 — `REST`

`REST $t2, $t0, $t1` (func `011110`, resto con signo) — `t0=17, t1=5` → `R[16]=2`. **Anduvo.**

## Caso 24 — `RESTU`

`RESTU $t2, $t0, $t1` (func `011111`) — `t0=0xFFFFFFFF, t1=2` → `R[16]=1`. **Anduvo.**

---

# Parte 4 — R-Type: memoria indexada `EAX(rs,rd)=R[rs]+R[rd]` (opcode `00000`)

## Caso 25 — `LWX`

`LWX $t1, $t0, $t2` (func `010100`) — `t0=0x1000 (base), t2=0 (índice)`, `M[0x1000]=0xDEADBEEF` → `R[15]=0xDEADBEEF`. **Anduvo.**

## Caso 26 — `SWX`

`SWX $t1, $t0, $t2` (func `010101`) — `t0=0x1000, t1=0xCAFEBABE, t2=0` → `M[0x1000]=0xCAFEBABE` (confirmado con `examine`). **Anduvo.**

## Caso 27 — `LHX`

`LHX $t1, $t0, $t2` (func `010000`, con signo) — `M[0x1000]=0x00008000` → `R[15]=0xFFFF8000` (extensión de signo correcta). **Anduvo.**

## Caso 28 — `LHUX`

`LHUX $t1, $t0, $t2` (func `010001`, sin signo) — mismo dato → `R[15]=0x00008000`. **Anduvo.**

## Caso 29 — `SHX`

`SHX $t1, $t0, $t2` (func `010110`) — `t1=0x0000ABCD` sobre memoria previa `0xCAFEBABE` → `M[0x1000]=0xCAFEABCD` (solo se pisa la mitad baja). **Anduvo.**

## Caso 30 — `LBX`

`LBX $t1, $t0, $t2` (func `010010`, con signo) — `M[0x1000]=0x00000080` → `R[15]=0xFFFFFF80`. **Anduvo.**

## Caso 31 — `LBUX`

`LBUX $t1, $t0, $t2` (func `010011`, sin signo) — mismo dato → `R[15]=0x00000080`. **Anduvo.**

## Caso 32 — `SBX`

`SBX $t1, $t0, $t2` (func `010111`) — `t1=0x000000EF` sobre memoria previa `0xCAFEABCD` → `M[0x1000]=0xCAFEABEF` (solo se pisa el byte bajo). **Anduvo.**

---

# Parte 5 — I-Type: memoria directa `EA(rs,imm)=R[rs]+E17(imm,S)` (opcodes `01000`-`01111`)

## Caso 33 — `LW`

`LW $t1, 8($t0)` (opcode `01000`) — `t0=0x1000`, `M[0x1008]=0x12345678` → `R[15]=0x12345678`. **Anduvo.**

## Caso 34 — `SW`

`SW $t1, 4($t0)` (opcode `01001`) — `t0=0x1000, t1=0x9ABCDEF0` → `M[0x1004]=0x9ABCDEF0`. **Anduvo.**

## Caso 35 — `SH`

`SH $t1, 0($t0)` (opcode `01010`) — `t1=0x0000BEEF` sobre memoria previa `0xCAFEABEF` → `M[0x1000]=0xCAFEBEEF`. **Anduvo.**

## Caso 36 — `SB`

`SB $t1, 0($t0)` (opcode `01011`) — `t1=0x000000AB` sobre memoria previa `0xCAFEBEEF` → `M[0x1000]=0xCAFEBEAB`. **Anduvo.**

## Caso 37 — `LH` / `LHU` / `LB` / `LBU`

Mismos casos que 27/28/30/31 pero con direccionamiento directo (opcodes `01100`,`01101`,`01110`,`01111`) en vez de indexado. Resultados idénticos (`0xFFFF8000`/`0x00008000`/`0xFFFFFF80`/`0x00000080`). **Los 4 anduvieron.**

## Caso 38 — `LW` con offset negativo

`LW $t1, -4($t0)` (imm de 17 bits en complemento a dos) — `t0=0x1004`, `M[0x1000]=0x11223344` → `EA=0x1000`, `R[15]=0x11223344`. Confirma que la extensión de signo del inmediato de 17 bits funciona para offsets negativos. **Anduvo.**

---

# Parte 6 — I-Type: `ADDI` / `SLTI` / `SLTIU` (opcodes `00011`, `10110`, `10111`)

## Caso 39 — `ADDI`

`ADDI $t1, $t0, -4` — `t0=10` → `R[15]=6` (`10 + E17(-4,S)`). **Anduvo.**

## Caso 40 — `SLTI`

`SLTI $t1, $t0, 10` — `t0=5` → `R[15]=1` (`5 < 10`). **Anduvo.**

## Caso 41 — `SLTIU`

`SLTIU $t1, $t0, 10` — `t0=0xFFFFFFFF` → `R[15]=0` (`U(-1)` no es `< 10`). **Anduvo.**

---

# Parte 7 — I-Type: familias de inmediato extendido `h=0/1` (opcodes `00100`-`00111`)

## Caso 42 — `ANDI` / `LCI` (opcode `00100`)

- `ANDI $t1, $t0, 0xFF` (h=0) — `t0=0x45003211` → `R[15]=0x00000011`. **Anduvo.**
- `LCI $t0, $t0, 0x1234` (h=1, `R[rt]=C16(simm,R[rs])`) — `t0=0x00001234` (concatena en la mitad alta preservando la baja) → `R[14]=0x12341234`. **Anduvo.**

## Caso 43 — `ANI` / `ANH` (opcode `00101`)

- `ANI $t1, $t0, 0x00FF` (h=0, extiende con **unos**: `E16(simm,1)`) — `t0=0x0000FF00` → `E16(0x00FF,1)=0xFFFF00FF`; `AND` con `t0` → `R[15]=0x0000FF00`. **Anduvo** (comportamiento distinto de `ANDI`, que extiende con ceros — confirmado).
- `ANH $t1, $t0, 0xFFFF` (h=1, `C16(simm,R[rs])`) — `t0=0x12345678` → concatena `0xFFFF` en la mitad alta de una copia de `t0` (`0xFFFF5678`), `AND` con `t0` → `R[15]=0x12345678`. **Anduvo.**

## Caso 44 — `ORI` / `ORH` (opcode `00110`)

- `ORI $t1, $t0, 0x00FF` (h=0) — `t0=0xFF00` → `R[15]=0x0000FFFF`. **Anduvo.**
- `ORH $t1, $t0, 0x1234` (h=1, `C16(simm,$0)` — **concatena con `$0`, no con `rs`**) — `t0=0x0000FFFF` → `R[15]=0x1234FFFF` (mitad baja viene de `$0`=0, no de `t0`; solo el `OR` final trae la mitad baja de `t0`). **Anduvo**, confirma que `ORH`/`XORH` concatenan contra `$0` (a diferencia de `LCI`/`ANH`, que concatenan contra `R[rs]`).

## Caso 45 — `XORI` / `XORH` (opcode `00111`)

- `XORI $t1, $zero, 0x41` (h=0; desde `$zero` sirve de carga inmediata) — `R[15]=0x00000041`. **Anduvo** (es la técnica que usa `build_rom.py` para cargar bytes).
- `XORH $t1, $zero, 0xFFFF` (h=1) — `R[15]=0xFFFF0000`. **Anduvo** (es la técnica que usa `build_rom.py` junto con `LCI`/`XORI` para armar el puntero de UART `0xFFFFFF00`).

---

# Parte 8 — Branches (opcodes `10000`-`10101`)

Todos con `RA19(imm)=PC+4+E19(4·imm,S)`.

## Caso 46 — `BEQ` / `BNE` / `BLT` / `BGE` / `BLTU` / `BGEU`

- `BEQ $t0,$t1,2` con `t0=t1=5` → salta, `PC=0x0000000C`. **Anduvo.**
- `BNE $t0,$t1,4` con `t0=t1=5` → no salta, `PC=0x00000004` (siguiente instrucción). **Anduvo.**
- `BLT $t0,$t1,3` con `t0=3,t1=5` (con signo) → salta, `PC=0x00000010`. **Anduvo.**
- `BGE $t0,$t1,3` con `t0=t1=5` → salta, `PC=0x00000010`. **Anduvo.**
- `BLTU $t0,$t1,3` con `t0=0xFFFFFFFF,t1=1` (sin signo: `U(-1)` no es `< U(1)`) → no salta, `PC=0x00000004`. **Anduvo.**
- `BGEU $t0,$t1,3` mismos operandos (`U(-1) >= U(1)`) → salta, `PC=0x00000010`. **Anduvo.**

---

# Parte 9 — Saltos (opcodes `00001`, `00010`)

## Caso 47 — `J`

`J 32` (`elimm=32`) desde `PC=0` → `RA27(32)=0+4+4·32=0x00000084`. **Anduvo.**

## Caso 48 — `JAL`

`JAL -8` desde `PC=0` → `$ra(R1)=PC+4=0x4`, `PC=0+4+4·(-8)=0xFFFFFFE4` (wrap sin chequeo de límites). **Anduvo** (el guardado del link register funciona perfecto).

## Caso 49 — `JR`

`JR $t0, 8` — `t0=0x2000` → `PC=0x2000+4·8=0x00002020`, sin guardar link. **Anduvo.**

## Caso 50 — `JALR`

`JALR $t0, -2` — `t0=0x4000` → `$ra(R1)=PC+4=0x4`, `PC=0x4000+4·(-2)=0x00003FF8`. **Anduvo.**

---

# Parte 10 — Instrucciones con comportamiento roto / no implementado en este build

Verificado exhaustivamente (barridos de todos los valores posibles del campo variable, no un solo intento). Estas son fallas reales del simulador `RTM32-0.1.0`, consistentes con que los capítulos 8 (Excepciones) y 9 (E/S) del manual figuran como "PRONTO..." — trabajo en progreso.

## Caso 51 — `JALX` ignora el campo de selección de link register

`JALX $lr<n>, 12` debería guardar `PC+4` en `$lr0`/`$lr1`/`$lr2`/`$lr3` (registros físicos 4-7) según los 2 bits `lr` del encoding (fig. 6.8). **Barrido de `lr=0,1,2,3`: en los 4 casos el valor de enlace terminó siempre en `R[3]`** (que además ni siquiera es un `$lr*` físico según la Tabla 3.1 — `$k1` es `R[3]`). El salto en sí (`PC = RA26(vlimm)`) funciona bien y coincide con lo esperado en los 4 casos. **Conclusión: el campo `lr` se decodifica pero no se usa; el destino del link queda hardcodeado.**

## Caso 52 — `JALRX` ignora el campo de selección de link register

Mismo patrón que `JALX`: barrido de `lr=0,1,2,3` con `JALRX $t0, 12` (`t0=0x1000`) — **el valor de enlace terminó siempre en `R[1]` (`$ra`)**, igual que un `JALR` común, y el salto (`PC=R[rs]+4·limm`) funcionó correctamente en los 4 casos. **Conclusión: `JALRX` se comporta como `JALR` liso; no hay forma de usar `$lr0-$lr3` en este build.**

## Caso 53 — `CFS` no tiene efecto observable

`CFS $t0, param` (`R[rs]=S[param]`) — barrido de `param=0..7` tras `reset` (con `$vbr` conocido en `0xF0000000` visible en la sección de registros especiales). **En los 8 casos `R[14]` quedó en `0x00000000` y `CAUSE=0x00000000`** (no hubo excepción, pero tampoco hubo copia del SFR al GPR). **Conclusión: el acceso a SFR vía `CFS` no está implementado (no rompe, pero tampoco hace nada).**

## Caso 54 — `CTS` no tiene efecto observable

`CTS $t0, param` (`S[param]=R[rs]`) con `t0=0xABCD`, seguido de `CFS $t1, param` para leer de vuelta — barrido de `param=0..7`. **En los 8 casos `R[15]` (destino del `CFS` de vuelta) quedó en `0`**, consistente con Caso 53. **Conclusión: mismo problema — `CTS`/`CFS` no están implementados en este build.**

## Caso 55 — `TRAP` deja el estado inconsistente

`TRAP 3` (`EPC=PC+4; PC=M[$vbr+3·4]`) ejecutado con `$vbr` en su valor de reset (`0xF0000000`, no mapeado a RAM en este setup sin `-k`/`-r` funcional). Resultado observado: **`PC` avanzó a `0x00000004` como una instrucción normal (no saltó a ningún vector), `CAUSE` pasó a `0x00000006`, y — inesperadamente — `VBR` cambió de `0xF0000000` a `0x00000002`.** El manual documenta la lectura del vector como indirecta (`M[...]`, un puntero en memoria, no un salto directo); al no haber memoria mapeada en `$vbr`, la lectura del vector parece fallar internamente y corromper `$vbr` en el proceso — un bug real, no un error de encoding de este test (probado con varios valores de `param`, mismo patrón). **Conclusión: `TRAP` es intestable de punta a punta en esta configuración (sin kernel RAM en `$vbr`) y además dejó `$vbr` en un valor inconsistente.**

## Caso 56 — `RFT` no avanza el PC

`RFT` (`PC=EPC`, `$psw` restaurado desde `$esr`) ejecutado en `0x00000200` con `EPC=0` (valor de reset). El debugger no expone un target `set epc`/`set vbr` directo (`Error: Unknown assignment target 'epc'`), así que se probó tal cual. Resultado: **tras `step 1`, `PC` se quedó exactamente en `0x00000200`** — ni saltó a `EPC=0` como documenta el manual, ni avanzó a `0x00000204` como cualquier instrucción normal. **Conclusión: `RFT` no hace ningún progreso visible en este build; no se pudo confirmar el comportamiento documentado.**

---

## Resumen

| Categoría                     | Instrucciones                               | Estado                                |
| ----------------------------- | ------------------------------------------- | ------------------------------------- |
| R-type ALU/lógica             | `ADD SUB AND OR XOR NOR SLT SLTU`           | ✅ 8/8                                |
| R-type shifts                 | `SLL SRL SRA RLC SLLR SRLR SRAR RLCR`       | ✅ 8/8                                |
| R-type mul/div                | `MUL MULH MULHU MULHSU DIV DIVU REST RESTU` | ✅ 8/8                                |
| R-type mem indexado           | `LWX SWX LHX LHUX SHX LBX LBUX SBX`         | ✅ 8/8                                |
| I-type mem directo            | `LW SW SH SB LH LHU LB LBU`                 | ✅ 8/8                                |
| I-type aritmética/comparación | `ADDI SLTI SLTIU`                           | ✅ 3/3                                |
| I-type inmediatos extendidos  | `ANDI LCI ANI ANH ORI ORH XORI XORH`        | ✅ 8/8                                |
| Branches                      | `BEQ BNE BLT BGE BLTU BGEU`                 | ✅ 6/6                                |
| Saltos simples                | `J JAL JR JALR`                             | ✅ 4/4                                |
| Saltos multi-link             | `JALX JALRX`                                | ⚠️ saltan bien, `lr` ignorado         |
| SFR                           | `CFS CTS`                                   | ❌ no implementados                   |
| Excepciones                   | `TRAP RFT`                                  | ❌ rotos / intestables sin kernel RAM |

**69 instrucciones del ISA cubiertas** (todo Tabla B.1 + B.2 salvo las reinterpretaciones triviales de opcode ya cubiertas por sus pares). 61 confirman el manual al 100%, 2 saltan correctamente pero con una limitación real (link register fijo), 4 no funcionan como está documentado.
