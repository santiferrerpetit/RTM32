# Pruebas de instrucciones STX4 (RTM32)

Cobertura: **38 de 54 instrucciones** del set (≈70%), agrupadas por tipo. Quedan pendientes para una segunda tanda: los loads/stores directos e indexados (`LW/SW/SH/SB/LH/LHU/LB/LBU`, `LWX/LHX/LHUX/LBX/LBUX`) y las privilegiadas/especiales (`CFS`, `CTS`, `TRAP`, `RFT`), tal como sugirió el profesor para dejarlas al final.

## Metodología (aplica a todos los casos)

- Simulador levantado con `docker build -t rtm32 . && docker run -d --name rtm32-sim -p 4444:4444 -p 5555:5555 rtm32`, debugger en `telnet localhost 4444`.
- El simulador **no trae ensamblador**: cada instrucción se codificó a mano (opcode/func/rs/rt/rd/aux/imm según Apéndice A del manual) con un pequeño script Python, y se inyectó directo en memoria con `set [addr] palabra`.
- Cada caso arranca con `reset` (ver Caso 41 — es imprescindible: una instrucción ilegal previa deja la CPU "trabada").
- Postcondición verificada con `registers` (o el propio texto de `step`, que informa el PC destino).
- **Nota de protocolo no documentada en el README:** al conectar por telnet, el debugger negocia opciones y después descarta silenciosamente **las primeras dos líneas** que se envían (una especie de doble "handshake"), antes de aceptar el primer comando real. Si no se manda algo de relleno primero, se pierden los primeros 1-2 comandos reales sin ningún error visible.

---

# Caso 1

## Descripción: que estoy testeando
`ADD` — suma de dos registros.

## Instrucctions: instrucciones que use durante el test
`ADD $1, $2, $3`  (encoding: `0x0086101C`)

## Precondiciones:
- `set r2 0x5`
- `set r3 0x3`

## Code
```
set [0x0] 0x86101c
set pc 0x0
step 1
registers
```

## Postcondiciones:
- `registers` → `R[1] = 0x00000008`

## Conclusiones:
Anduvo. `5 + 3 = 8`, coincide exactamente con la especificación.

---

# Caso 2

## Descripción: que estoy testeando
`SUB` — resta de dos registros.

## Instrucctions
`SUB $1, $2, $3`  (`0x0086101D`)

## Precondiciones:
- `set r2 0x5`
- `set r3 0x3`

## Code
```
set [0x40] 0x86101d
set pc 0x40
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x00000002`

## Conclusiones:
Anduvo. `5 - 3 = 2`.

---

# Caso 3

## Descripción: que estoy testeando
`AND` bit a bit.

## Instrucctions
`AND $1, $2, $3`  (`0x00861008`)

## Precondiciones:
- `set r2 0xF0F0`
- `set r3 0x0FF0`

## Code
```
set [0x80] 0x861008
set pc 0x80
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x000000F0`

## Conclusiones:
Anduvo. `0xF0F0 & 0x0FF0 = 0x00F0`.

---

# Caso 4

## Descripción: que estoy testeando
`OR` bit a bit.

## Instrucctions
`OR $1, $2, $3`  (`0x00861009`)

## Precondiciones:
- `set r2 0xF0F0`
- `set r3 0x0FF0`

## Code
```
set [0xc0] 0x861009
set pc 0xc0
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x0000FFF0`

## Conclusiones:
Anduvo. `0xF0F0 | 0x0FF0 = 0xFFF0`.

---

# Caso 5

## Descripción: que estoy testeando
`XOR` bit a bit.

## Instrucctions
`XOR $1, $2, $3`  (`0x0086100A`)

## Precondiciones:
- `set r2 0xF0F0`
- `set r3 0x0FF0`

## Code
```
set [0x100] 0x86100a
set pc 0x100
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x0000FF00`

## Conclusiones:
Anduvo. `0xF0F0 ^ 0x0FF0 = 0xFF00`.

---

# Caso 6

## Descripción: que estoy testeando
`NOR` bit a bit, con ambos operandos en 0 para chequear que da todos unos.

## Instrucctions
`NOR $1, $2, $3`  (`0x0086100B`)

## Precondiciones:
- `set r2 0x0`
- `set r3 0x0`

## Code
```
set [0x140] 0x86100b
set pc 0x140
step 1
registers
```

## Postcondiciones:
- `R[1] = 0xFFFFFFFF`

## Conclusiones:
Anduvo. `NOR(0,0) = ~0 = 0xFFFFFFFF`.

---

# Caso 7

## Descripción: que estoy testeando
`SLT` — comparación menor-que **con signo**. Elegimos `0xFFFFFFFF` (-1) vs `1` a propósito: con signo es verdadero (-1 < 1), sin signo es falso (ver Caso 8, mismo par de operandos).

## Instrucctions
`SLT $1, $2, $3`  (`0x0086100C`)

## Precondiciones:
- `set r2 0xFFFFFFFF`
- `set r3 0x1`

## Code
```
set [0x180] 0x86100c
set pc 0x180
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x00000001`

## Conclusiones:
Anduvo. Con signo, `-1 < 1` es verdadero → `R1=1`.

---

# Caso 8

## Descripción: que estoy testeando
`SLTU` — mismo par de operandos que el Caso 7, para contrastar con/sin signo.

## Instrucctions
`SLTU $1, $2, $3`  (`0x0086100D`)

## Precondiciones:
- `set r2 0xFFFFFFFF`
- `set r3 0x1`

## Code
```
set [0x1c0] 0x86100d
set pc 0x1c0
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x00000000`

## Conclusiones:
Anduvo. Sin signo, `0xFFFFFFFF` es enorme, no es menor que `1` → `R1=0`. Junto con el Caso 7 confirma que SLT/SLTU interpretan el signo correctamente y de forma distinta entre sí.

---

# Caso 9

## Descripción: que estoy testeando
`MUL` — palabra baja del producto, caso simple sin overflow.

## Instrucctions
`MUL $1, $2, $3`  (`0x00861015`)

## Precondiciones:
- `set r2 0x6`
- `set r3 0x7`

## Code
```
set [0x200] 0x861015
set pc 0x200
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x0000002A` (42)

## Conclusiones:
Anduvo. `6*7=42`.

---

# Caso 10

## Descripción: que estoy testeando
`MULH` — palabra alta del producto **con signo**. Usamos `-1 * 2 = -2` para verificar el sign-extend de la mitad alta (compañero del Caso 11, MULHU, con los mismos bits de entrada).

## Instrucctions
`MULH $1, $2, $3`  (`0x00861016`)

## Precondiciones:
- `set r2 0xFFFFFFFF`
- `set r3 0x2`

## Code
```
set [0x240] 0x861016
set pc 0x240
step 1
registers
```

## Postcondiciones:
- `R[1] = 0xFFFFFFFF`

## Conclusiones:
Anduvo. `-1*2 = -2 = 0xFFFFFFFFFFFFFFFE` (64 bits con signo); la mitad alta es `0xFFFFFFFF`.

---

# Caso 11

## Descripción: que estoy testeando
`MULHU` — mismos bits que el Caso 10 pero interpretados sin signo, para contrastar.

## Instrucctions
`MULHU $1, $2, $3`  (`0x00861017`)

## Precondiciones:
- `set r2 0xFFFFFFFF`
- `set r3 0x2`

## Code
```
set [0x280] 0x861017
set pc 0x280
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x00000001`

## Conclusiones:
Anduvo. Sin signo, `0xFFFFFFFF * 2 = 0x1FFFFFFFE`; la mitad alta es `0x1`. Distinto del Caso 10 (`0xFFFFFFFF`), confirmando que MULH/MULHU sí distinguen signo.

---

# Caso 12

## Descripción: que estoy testeando
`DIV` — división entera con signo. Usamos `-9 / 4` (trunca hacia cero). Mismos bits se reutilizan en los Casos 13-15 (DIVU/REST/RESTU) para comparar las cuatro variantes con un solo par de operandos.

## Instrucctions
`DIV $1, $2, $3`  (`0x00861018`)

## Precondiciones:
- `set r2 0xFFFFFFF7` (-9)
- `set r3 0x4`

## Code
```
set [0x2c0] 0x861018
set pc 0x2c0
step 1
registers
```

## Postcondiciones:
- `R[1] = 0xFFFFFFFE` (-2)

## Conclusiones:
Anduvo. `-9/4 = -2.25` truncado hacia cero da `-2`, coincide.

---

# Caso 13

## Descripción: que estoy testeando
`DIVU` — mismos bits que el Caso 12, interpretados sin signo.

## Instrucctions
`DIVU $1, $2, $3`  (`0x00861019`)

## Precondiciones:
- `set r2 0xFFFFFFF7`
- `set r3 0x4`

## Code
```
set [0x300] 0x861019
set pc 0x300
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x3FFFFFFD` (1073741821)

## Conclusiones:
Anduvo. `4294967287 / 4 = 1073741821` (entero), muy distinto del resultado con signo del Caso 12 — confirma la distinción DIV/DIVU.

---

# Caso 14

## Descripción: que estoy testeando
`REST` — resto con signo de la misma división del Caso 12.

## Instrucctions
`REST $1, $2, $3`  (`0x0086101A`)

## Precondiciones:
- `set r2 0xFFFFFFF7`
- `set r3 0x4`

## Code
```
set [0x340] 0x86101a
set pc 0x340
step 1
registers
```

## Postcondiciones:
- `R[1] = 0xFFFFFFFF` (-1)

## Conclusiones:
Anduvo. `-9 = 4*(-2) + (-1)` → resto `-1`, consistente con la división truncada del Caso 12.

---

# Caso 15

## Descripción: que estoy testeando
`RESTU` — resto sin signo de los mismos bits.

## Instrucctions
`RESTU $1, $2, $3`  (`0x0086101B`)

## Precondiciones:
- `set r2 0xFFFFFFF7`
- `set r3 0x4`

## Code
```
set [0x380] 0x86101b
set pc 0x380
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x00000003`

## Conclusiones:
Anduvo. `4294967287 mod 4 = 3`, consistente con el cociente sin signo del Caso 13 (`4*1073741821 + 3 = 4294967287`).

---

# Caso 16

## Descripción: que estoy testeando
`SLL` — shift lógico a izquierda con cantidad inmediata (campo `aux`).

## Instrucctions
`SLL $1, $2, 4`  (`0x00041200`)

## Precondiciones:
- `set r2 0x1`

## Code
```
set [0x3c0] 0x41200
set pc 0x3c0
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x00000010`

## Conclusiones:
Anduvo. `1 << 4 = 16`.

---

# Caso 17

## Descripción: que estoy testeando
`SRL` — shift lógico a derecha; no debe extender signo aunque el bit más alto sea 1.

## Instrucctions
`SRL $1, $2, 4`  (`0x00041201`)

## Precondiciones:
- `set r2 0x80000000`

## Code
```
set [0x400] 0x41201
set pc 0x400
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x08000000`

## Conclusiones:
Anduvo. Corrimiento lógico puro, sin relleno de unos por la izquierda.

---

# Caso 18

## Descripción: que estoy testeando
`SRA` — shift aritmético a derecha; con MSB=1 debe extender signo (compañero directo del Caso 17, mismo operando).

## Instrucctions
`SRA $1, $2, 4`  (`0x00041202`)

## Precondiciones:
- `set r2 0x80000000`

## Code
```
set [0x440] 0x41202
set pc 0x440
step 1
registers
```

## Postcondiciones:
- `R[1] = 0xF8000000`

## Conclusiones:
Anduvo. A diferencia del Caso 17, acá sí se propaga el signo (`0xF8...` en vez de `0x08...`), confirmando la diferencia lógico/aritmético.

---

# Caso 19

## Descripción: que estoy testeando
`SLLR` — shift a izquierda con la cantidad tomada de un registro, en vez de inmediato.

## Instrucctions
`SLLR $1, $2, $3`  (`0x00C41003`) — cantidad en `$3`, valor a desplazar en `$2`.

## Precondiciones:
- `set r2 0x1`
- `set r3 0x4`

## Code
```
set [0x480] 0xc41003
set pc 0x480
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x00000010`

## Conclusiones:
Anduvo. Igual resultado que el Caso 16 (SLL) pero con la cantidad en registro.

---

# Caso 20

## Descripción: que estoy testeando
`SRLR` — shift lógico a derecha con cantidad en registro.

## Instrucctions
`SRLR $1, $2, $3`  (`0x00C41004`)

## Precondiciones:
- `set r2 0x80000000`
- `set r3 0x4`

## Code
```
set [0x4c0] 0xc41004
set pc 0x4c0
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x08000000`

## Conclusiones:
Anduvo. Coincide con el Caso 17.

---

# Caso 21

## Descripción: que estoy testeando
`SRAR` — shift aritmético a derecha con cantidad en registro.

## Instrucctions
`SRAR $1, $2, $3`  (`0x00C41005`)

## Precondiciones:
- `set r2 0x80000000`
- `set r3 0x4`

## Code
```
set [0x500] 0xc41005
set pc 0x500
step 1
registers
```

## Postcondiciones:
- `R[1] = 0xF8000000`

## Conclusiones:
Anduvo. Coincide con el Caso 18 (extiende signo).

---

# Caso 22

## Descripción: que estoy testeando
`JR` — salto incondicional a la dirección contenida en un registro.

## Instrucctions
`JR $2`  (`0x0080000E`)

## Precondiciones:
- `set r2 0x100`

## Code
```
set [0x540] 0x80000e
set pc 0x540
step 1
registers
```

## Postcondiciones:
- `step` informa `Target PC: 0x00000100`; `registers` confirma `PC = 0x00000100`.

## Conclusiones:
Anduvo. Salta exactamente a `R[2]`.

---

# Caso 23

## Descripción: que estoy testeando
`JALR` — salto con guardado de dirección de retorno. **Ver también el Caso 39**, donde se detectó que el destino real del enlace no es el que dice el manual.

## Instrucctions
`JALR $2, $0`  (`0x0080000F`) — codificado tal como lo describe el manual (`rs, rt`), con `rt=$0`.

## Precondiciones:
- `set r2 0x104`

## Code
```
set [0x580] 0x80000f
set pc 0x580
step 1
registers
```

## Postcondiciones:
- `PC = 0x00000104` (correcto, salta a `R[2]`).
- `R[31] = 0x00000000` (**no** se actualizó, contra lo que dice el manual).
- `R[0] = 0x00000584` (el valor de enlace terminó en `$zero`, ver Caso 39).

## Conclusiones:
Parcialmente. El salto (`PC=R[rs]`) funciona, pero el guardado de la dirección de retorno **no fue a `$ra`/`$31`** como indica el manual. Investigado a fondo en el Caso 39.

---

# Caso 24

## Descripción: que estoy testeando
`BEQ` — branch si iguales, caso tomado.

## Instrucctions
`BEQ $2, $3, 2`  (`0x80860002`) — con `imm=2`, si se toma el PC destino es `base+4+4*2 = base+0xC`.

## Precondiciones:
- `set r2 0x5`
- `set r3 0x5`

## Code
```
set [0x5c0] 0x80860002
set pc 0x5c0
step 1
registers
```

## Postcondiciones:
- `PC = 0x000005CC` (`0x5C0 + 0xC`)

## Conclusiones:
Anduvo. Como `5==5`, el salto se toma y el PC coincide exactamente con la fórmula del manual (`PC = PC + 4 + 4*imm`).

---

# Caso 25

## Descripción: que estoy testeando
`BNE` — branch si distintos, caso tomado.

## Instrucctions
`BNE $2, $3, 2`  (`0x88860002`)

## Precondiciones:
- `set r2 0x5`
- `set r3 0x6`

## Code
```
set [0x600] 0x88860002
set pc 0x600
step 1
registers
```

## Postcondiciones:
- `PC = 0x0000060C`

## Conclusiones:
Anduvo. `5 != 6` → salto tomado, PC correcto.

---

# Caso 26

## Descripción: que estoy testeando
`BLT` — branch si menor (con signo), caso tomado.

## Instrucctions
`BLT $2, $3, 2`  (`0x90860002`)

## Precondiciones:
- `set r2 0x3`
- `set r3 0x5`

## Code
```
set [0x640] 0x90860002
set pc 0x640
step 1
registers
```

## Postcondiciones:
- `PC = 0x0000064C`

## Conclusiones:
Anduvo. `3 < 5` → tomado.

---

# Caso 27

## Descripción: que estoy testeando
`BGT` — branch si mayor, caso tomado.

## Instrucctions
`BGT $2, $3, 2`  (`0x98860002`)

## Precondiciones:
- `set r2 0x5`
- `set r3 0x3`

## Code
```
set [0x680] 0x98860002
set pc 0x680
step 1
registers
```

## Postcondiciones:
- `PC = 0x0000068C`

## Conclusiones:
Anduvo. `5 > 3` → tomado.

---

# Caso 28

## Descripción: que estoy testeando
`BLE` — branch si menor o igual, caso tomado con igualdad (borde).

## Instrucctions
`BLE $2, $3, 2`  (`0xA0860002`)

## Precondiciones:
- `set r2 0x5`
- `set r3 0x5`

## Code
```
set [0x6c0] 0xa0860002
set pc 0x6c0
step 1
registers
```

## Postcondiciones:
- `PC = 0x000006CC`

## Conclusiones:
Anduvo. `5 <= 5` → tomado (caso borde de igualdad correcto).

---

# Caso 29

## Descripción: que estoy testeando
`BGE` — branch si mayor o igual, caso tomado con igualdad (borde).

## Instrucctions
`BGE $2, $3, 2`  (`0xA8860002`)

## Precondiciones:
- `set r2 0x5`
- `set r3 0x5`

## Code
```
set [0x700] 0xa8860002
set pc 0x700
step 1
registers
```

## Postcondiciones:
- `PC = 0x0000070C`

## Conclusiones:
Anduvo. `5 >= 5` → tomado.

---

# Caso 30

## Descripción: que estoy testeando
`ADDI` — suma con constante inmediata.

## Instrucctions
`ADDI $1, $2, 5`  (`0x08820005`)

## Precondiciones:
- `set r2 0x0`

## Code
```
set [0x740] 0x8820005
set pc 0x740
step 1
registers
```

## Postcondiciones:
- Esperado: `R[1] = 0x00000005`.
- Real: `R[1] = 0x00000000` (**sin cambios**).
- `CAUSE = 0x00000003` → excepción de instrucción ilegal.
- Log interno del simulador (`/tmp/rtm32.log`): `Illegal Instruction 0x8820005 at PC 0x00000740`, con `Opcode: 0b00001` (que es exactamente el opcode de ADDI según la Tabla A.1).

## Conclusiones:
**No anduvo — bug real de la máquina.** El opcode `00001` (ADDI) está correctamente documentado en el manual, y el decoder incluso lo identifica como tal (`Opcode: 0b00001`), pero la CPU lo marca como instrucción ilegal en vez de ejecutarlo. Confirmado también contra otro `rs` distinto de `$0` (mismo resultado). Reproducible.

---

# Caso 31

## Descripción: que estoy testeando
`SLTI` — comparación menor-que con signo contra constante inmediata.

## Instrucctions
`SLTI $1, $2, 5`  (`0xB0820005`)

## Precondiciones:
- `set r2 0x3`

## Code
```
set [0x780] 0xb0820005
set pc 0x780
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x00000001`

## Conclusiones:
Anduvo. `3 < 5` con signo → `1`. (Nota: a diferencia de ADDI, este opcode de la misma familia I-type sí funciona.)

---

# Caso 32

## Descripción: que estoy testeando
`SLTIU` — comparación menor-que sin signo contra constante inmediata.

## Instrucctions
`SLTIU $1, $2, 1`  (`0xB8820001`)

## Precondiciones:
- `set r2 0xFFFFFFFF`

## Code
```
set [0x7c0] 0xb8820001
set pc 0x7c0
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x00000000`

## Conclusiones:
Anduvo. Sin signo, `0xFFFFFFFF` no es menor que `1` → `0`.

---

# Caso 33

## Descripción: que estoy testeando
`J` — salto incondicional a dirección absoluta.

## Instrucctions
`J 0xC0`  (campo de dirección en palabras; `0xC0*4 = 0x300`) → `0x100000C0`

## Precondiciones:
- Ninguna.

## Code
```
set [0x800] 0x100000c0
set pc 0x800
step 1
registers
```

## Postcondiciones:
- `PC = 0x00000300`

## Conclusiones:
Anduvo. Coincide con `E(address)` de la fórmula del manual (con los 3 bits altos del PC en 0, ya que estamos en direcciones bajas).

---

# Caso 34

## Descripción: que estoy testeando
`JAL` — salto absoluto con guardado de dirección de retorno.

## Instrucctions
`JAL 0xC4`  (`0xC4*4 = 0x310`) → `0x180000C4`

## Precondiciones:
- Ninguna.

## Code
```
set [0x840] 0x180000c4
set pc 0x840
step 1
registers
```

## Postcondiciones:
- `PC = 0x00000310`
- `R[31] = 0x00000844` (`0x840 + 4`)

## Conclusiones:
Anduvo, y a diferencia de `JALR` (Caso 23/39) **acá sí** el enlace fue directo a `$31`, tal como documenta el manual para el formato J.

---

# Caso 35

## Descripción: que estoy testeando
`ANDI` (h=0, mitad baja) — AND lógico con constante inmediata.

## Instrucctions
`ANDI $1, $2, 0x0F`  (`0x2082000F`, h=0)

## Precondiciones:
- `set r2 0xFF`

## Code
```
set [0x880] 0x2082000f
set pc 0x880
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x0000000F`

## Conclusiones:
Anduvo para h=0. El manual (nota al pie, sección 1.2) advierte de "un bug importante a solucionar en la instrucción ANDI" — con este operando puntual no lo detectamos, pero **no llegamos a probar la variante h=1** (mitad alta) con un operando que realmente la ejercite (ver limitaciones más abajo). Queda pendiente de una prueba más específica.

---

# Caso 36

## Descripción: que estoy testeando
`ORI` (h=0) — OR lógico con constante inmediata.

## Instrucctions
`ORI $1, $2, 0x0F`  (`0x2882000F`)

## Precondiciones:
- `set r2 0xF0`

## Code
```
set [0x8c0] 0x2882000f
set pc 0x8c0
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x000000FF`

## Conclusiones:
Anduvo. `0xF0 | 0x0F = 0xFF`.

---

# Caso 37

## Descripción: que estoy testeando
`XORI` (h=0) — XOR lógico con constante inmediata.

## Instrucctions
`XORI $1, $2, 0x00FF`  (`0x308200FF`)

## Precondiciones:
- `set r2 0xFF00`

## Code
```
set [0x900] 0x308200ff
set pc 0x900
step 1
registers
```

## Postcondiciones:
- `R[1] = 0x0000FFFF`

## Conclusiones:
Anduvo. `0xFF00 ^ 0x00FF = 0xFFFF`.

---

# Caso 38

## Descripción: que estoy testeando
`LUI` — carga inmediata en la mitad alta del registro.

## Instrucctions
`LUI $1, 0xABCD`  (`0x3803ABCD`)

## Precondiciones:
- Ninguna.

## Code
```
set [0x940] 0x3803abcd
set pc 0x940
step 1
registers
```

## Postcondiciones:
- Esperado: `R[1] = 0xABCD0000`.
- Real: `R[1] = 0x00000000` (sin cambios).
- `CAUSE = 0x00000003` → excepción de instrucción ilegal (mismo patrón que ADDI, Caso 30).

## Conclusiones:
**No anduvo — bug real de la máquina.** El opcode `00111` (LUI) también es rechazado como instrucción ilegal, igual que ADDI. Entre los 38 casos, estos dos son los únicos con esta falla.

---

# Caso 39

## Descripción: que estoy testeando
Investigación puntual sobre `JALR` a partir de lo raro que se vio en el Caso 23: ¿a qué registro va realmente la dirección de retorno?

## Instrucctions
Tres variantes de `JALR $2, ...`, cambiando sólo el campo que el manual llama "rt" (o el campo real `rd` del encoding R-type):
- `JALR` con `rt=$0` (igual al Caso 23): `0x0080000F`
- `JALR` con `rt=$31` (probando si `rt` es el destino): `0x00BE000F`
- `JALR` con `rd=$31` explícito (probando si el destino real es el campo `rd`, no `rt`): `0x0081F00F`

## Precondiciones:
- `set r2 0x104` (dirección destino del salto, igual en las tres variantes)

## Code
```
reset
set r2 0x104
set [0x0] 0x80000f
set pc 0x0
step 1
registers

reset
set r2 0x104
set [0x0] 0xbe000f
set pc 0x0
step 1
registers

reset
set r2 0x104
set [0x0] 0x81f00f
set pc 0x0
step 1
registers
```

## Postcondiciones:
- Variante `rt=$0`: `PC=0x104` ✔, `R[0]=0x00000004`, `R[31]=0x00000000`.
- Variante `rt=$31`: `PC=0x104` ✔, `R[0]=0x00000004` (¡de nuevo!), `R[31]=0x00000000`.
- Variante `rd=$31` explícito: `PC=0x104` ✔, `R[31]=0x00000004`, `R[0]=0x00000000`.

## Conclusiones:
Anduvo el salto en las tres variantes, pero el guardado de la dirección de retorno **no depende del campo `rt`** (cambiar `rt` de `$0` a `$31` no cambia nada) — depende del campo `rd` del encoding tipo R. El manual describe la operación como `R[31] = PC+4` y lista los operandos como `rs rt`, pero el hardware real usa el campo `rd` (bits 16-12) como destino del enlace, igual que en las ALU ops. Para lograr el comportamiento convencional de `$ra` hay que codificar `JALR` con `rd=31` (no `rt=31`). Esto también expone que el campo `rt` de `JALR` parece no usarse para nada.

---

# Caso 40

## Descripción: que estoy testeando
El manual (sección 1.1) dice textualmente que `$0`/`$zero` "está cableado en el hardware, así que no se puede modificar, aunque puede usarse como destino en cualquier instrucción". Probamos justamente eso: usar `$0` como destino de una ALU op común.

## Instrucctions
`ADD $0, $2, $3`  (`0x0086001C`)

## Precondiciones:
- `set r2 0x5`
- `set r3 0x3`

## Code
```
set [0x0] 0x86001c
set pc 0x0
step 1
registers
```

## Postcondiciones:
- Esperado (según manual): `R[0] = 0x00000000` (la escritura debería descartarse).
- Real: `R[0] = 0x00000008` (¡se modificó!).

## Conclusiones:
**No anduvo — bug real, y de alcance general (no sólo de `JALR`).** `$0` no está protegido contra escritura en esta implementación; una ALU op común lo pisa sin problema. Esto es consistente con lo visto en el Caso 39 (donde `JALR` con `rd=0` también pisaba `$0`), pero acá lo confirmamos con una instrucción totalmente básica (`ADD`), así que no es un caso aislado de `JALR`.

---

# Caso 41

## Descripción: que estoy testeando
Comportamiento de la máquina **después** de ejecutar una instrucción ilegal (como `ADDI`, Caso 30). ¿Se salta esa instrucción y sigue, o pasa algo más grave?

## Instrucctions
Secuencia: `ADDI $1,$2,5` (ilegal, Caso 30) seguida de una `SLTI` perfectamente válida, **sin `reset` en el medio**.

## Precondiciones:
- `set r2 0x3`

## Code
```
set [0x740] 0x8820005
set pc 0x740
step 1
registers
set [0x780] 0xb0820005
set pc 0x780
step 1
registers
```

## Postcondiciones:
- Después del primer `step` (la ilegal): `PC` avanza normalmente a `0x744`, `CAUSE=0x3`.
- Después de reubicar el PC en `0x780` y hacer `step` sobre la `SLTI` válida: el log interno (`/tmp/rtm32.log`) **no muestra ningún `Instruction:`/`Opcode:` nuevo** — la CPU no volvió a fetchear nada. El registro destino queda con el valor de la corrida anterior (no se actualiza), como si el `step` no hubiese hecho nada.
- Con un `reset` intercalado antes de la segunda instrucción, la `SLTI` se ejecuta perfectamente (ver Caso 31).

## Conclusiones:
**Bug real y importante para la metodología de todo el curso.** Una vez que la CPU ejecuta una instrucción ilegal, queda "trabada": cualquier `step` posterior es un no-op silencioso (no tira error, no avanza el PC, no cambia registros) hasta que se hace `reset`. Si no se sabe esto, **cualquier instrucción que se prueba después de una ilegal en la misma sesión da un falso negativo** (parece que no anda, cuando en realidad ni se llegó a ejecutar). Recomendación para los compañeros: hacer `reset` después de cualquier caso donde `CAUSE` quede en `0x3`, o directamente dejar las instrucciones sospechosas de estar rotas para el final de la sesión.

---

# Caso 42

## Descripción: que estoy testeando
No es una instrucción de la CPU sino del **comando `examine` del debugger** (`examine <tipo> <dir> <cant>`, según el README). Al no coincidir nunca los valores que esperábamos ver en memoria, sospechamos del comando en sí y no de la CPU.

## Instrucctions
N/A (comando de debugger, no instrucción de máquina).

## Precondiciones:
- Ninguna especial.

## Code
```
examine xw 0x9 3
```

## Postcondiciones:
- Salida del debugger: `0x00000003: 0x00000000    0x00000000    0x00000000`
- Log interno (`/tmp/rtm32.log`), que muestra los accesos reales al bus: `ADDR: 0x00000003`, `0x00000007`, `0x0000000B` — es decir, arrancó en `0x3`, **no en `0x9`** como pedimos.
- Repitiendo con `examine xw 0x40 2`: arrancó en `0x2` (el valor de "cantidad"), no en `0x40`.

## Conclusiones:
**No anduvo — bug del comando `examine`, no de la CPU.** El argumento de dirección se ignora por completo; el comando usa el valor de "cantidad" tanto como dirección de inicio como como cantidad de palabras a mostrar. Por eso durante buena parte de las pruebas preferimos verificar resultados con `registers` (para ver registros) y con el log interno del simulador (para bus/memoria) en vez de confiar en `examine`.

---

# Resumen

| Resultado | Cantidad | Detalle |
|---|---|---|
| Instrucciones que anduvieron según el manual | 35 | Casos 1-22, 24-29, 31-33, 35-38 |
| Instrucciones con comportamiento distinto al manual (no rotas, pero mal documentadas) | 1 | `JALR` (Casos 23, 39) — el destino real es `rd`, no `rt`/`$31` fijo |
| Instrucciones no implementadas / ilegales | 2 | `ADDI` (Caso 30), `LUI` (Caso 38) |
| Bugs de alcance general encontrados | 2 | `$0` escribible (Caso 40); CPU se traba tras instrucción ilegal (Caso 41) |
| Bugs de la herramienta de debug (no de la CPU) | 1 | `examine` ignora la dirección (Caso 42) |

Pendiente para la próxima tanda: loads/stores (directos e indexados) y `CFS`/`CTS`/`TRAP`/`RFT`.
