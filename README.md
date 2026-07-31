# RTM32 — Simulador de CPU STX4

Harness Docker para correr el simulador precompilado de **STX4** (`RTM32-0.1.0`), una CPU RISC de 32 bits custom, dentro del sistema **RTM32**. El simulador expone un debugger remoto por telnet y una consola UART, ambas sobre TCP.

Este repo no tiene código fuente propio: el binario a ejecutar (`rtm32`) ya viene compilado.

> ⚠️ **Máquina y manual actualizados (Jul 2026).** El binario y el `rtm32.pdf` cambiaron a una revisión nueva e incompatible con la anterior: convención de registros distinta, opcodes distintos, capítulo del debugger del manual desactualizado respecto del binario real. Todo lo que sigue ya está verificado contra el binario nuevo. Ver `pruebas-stx4.md` para las 69 instrucciones probadas una por una contra el simulador real (incluye 6 que están rotas/no implementadas en este build: `CFS`/`CTS`/`TRAP`/`RFT`/`JALX`/`JALRX` — aunque `RFT` en particular resultó andar bien de forma aislada, el bug real es más de fondo: cualquier excepción deja la CPU trabada para siempre, ver "Bugs y comportamiento no documentado" al final de este archivo).

## Contenido del repo

| Archivo                | Qué es                                                                                                                    |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `rtm32`                | Simulador (ELF x86-64 dinámico, `RTM32-0.1.0`). Es lo que corre el contenedor.                                            |
| `rtm32.s`              | Misma build, enlazada estáticamente. No la usa Docker; sirve para debuggear en el host directamente.                      |
| `rtm32.pdf`            | Manual de arquitectura/ISA de STX4 (español). Referencia de registros, memoria y opcodes.                                 |
| `Dockerfile`           | Imagen que corre el simulador + `docker-entrypoint.sh` + un puente `socat` para la UART.                                  |
| `docker-entrypoint.sh` | Arranca `rtm32`, levanta el puente UART→5555, e inyecta/arranca la ROM de boot.                                           |
| `rom.bin`              | ROM de boot mínima (64K), hand-assembleada a mano con el ISA verificado. Imprime `ROM OK\r\n` y entra en loop infinito. Ver sección "Boot ROM".                          |
| `test_rom.sh`          | Smoke test end-to-end: build + run + chequea `ROM OK` por UART + cleanup.                                                 |
| `pruebas-stx4.md`      | Batería de pruebas de instrucciones — 69 casos re-verificados contra el binario nuevo (incluye instrucciones rotas).      |

## Requisitos

- Docker Desktop corriendo

## Uso

```bash
docker rm -f rtm32-sim 2>/dev/null  # por si quedó un contenedor previo con ese nombre
docker build -t rtm32 .
docker run -d --name rtm32-sim -p 4444:4444 -p 5555:5555 rtm32
```

Esto levanta `rtm32 -d telnet -m 64K` (debugger por telnet, 64K de memoria de usuario) y un puente `socat` que expone la UART del simulador en el puerto 5555, y arranca la ROM de boot automáticamente (ver "Boot ROM" abajo).

**Terminal 1 — Consola UART (salida del programa):**

```bash
telnet localhost 5555
```

**Terminal 2 — Debugger:**

```bash
telnet localhost 4444
```

> **Ojo con el handshake:** al conectar por telnet al debugger, las primeras dos líneas enviadas se descartan silenciosamente (negociación de opciones). Si el primer comando real se pierde sin error visible, mandá una línea de relleno antes.

**Parar el simulador:**

```bash
docker rm -f rtm32-sim
```

## Boot ROM

El archivo `rom.bin` es una ROM mínima que arranca la CPU STX4 automáticamente: carga la dirección de la UART, imprime `ROM OK\r\n`, y entra en un loop infinito.

### Arquitectura del boot

Al hacer `docker run`, el entrypoint del contenedor realiza esta secuencia automáticamente:

```
┌─────────────────────┐
│  1. Levanta rtm32   │ → Crea PTY de UART y debugger telnet (4444)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  2. socat bridge    │ → Expone PTY en TCP 5555
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  3. Inyecta ROM     │ → Conecta a debugger 127.0.0.1:4444
│     vía debugger    │    y escribe 21 palabras en memoria con
│     (set [addr])    │    `set [addr] word`
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  4. set PC=0x0000   │
│  5. continue        │ → CPU ejecuta la ROM
└──────────┬──────────┘
           │
     ┌─────▼─────┐
     │  ROM OK   │ → Visible en telnet localhost 5555
     └───────────┘
```

> **Nota importante:** `load rom.bin exact` **no funciona** en este build (espera un formato snapshot interno con magic+versión+tag de arquitectura, no un binario raw — confirmado por los mensajes de error del propio binario). El flag `-r/--rom` que el manual documenta como reemplazo (bootear desde el vector de reset real, `0xF0000000`) **tampoco tiene efecto**: probado directamente, el log de arranque siempre dice `CPU PC initialized to 0x00000000` (la ruta sin ROM), nunca el mensaje de "reset vector" que el binario sí soporta internamente. Por eso la ROM se inyecta palabra por palabra a través del debugger TCP, arrancando en `0x0000` (RAM de usuario) en vez del vector arquitectural.
>
> **Gotcha crítico:** cerrar la conexión telnet del debugger mata **todo el proceso** `rtm32`, no solo la sesión de depuración (verificado: el log muestra `Debugger session channel context destroyed cleanly` seguido inmediatamente de `Destroying serial device`). Por eso el proceso que inyecta la ROM nunca cierra su socket — se queda bloqueado para siempre después de `continue`, y `docker-entrypoint.sh` lo corre en background (`&`).

### Uso — Boot automático

**1. Build y run:**

```bash
docker rm -f rtm32-sim 2>/dev/null
docker build --platform linux/amd64 -t rtm32 .
docker run -d --platform linux/amd64 --name rtm32-sim -p 4444:4444 -p 5555:5555 rtm32
```

> **Mac M1/M2:** siempre agregar `--platform linux/amd64` porque el simulador es un binario x86-64.

**2. Esperar ~7-10 segundos** (boot completo: simulador → PTY → socat → inyección ROM → `continue`).

**3. Conectar a la UART:**

```bash
telnet localhost 5555
```

Deberías ver inmediatamente:

```
ROM OK
```

**4. Apagar:**

```bash
docker rm -f rtm32-sim
```

### Qué hace la ROM paso a paso

Usa `$t0`(físico `$14`) como puntero a la UART y `$t1`(físico `$15`) como dato temporal — numeración física directa de la Tabla 3.1 del manual nuevo, sin traducción.

| Dirección | Instrucción (machine code)    | Efecto                                              |
| --------- | ----------------------------- | --------------------------------------------------- |
| `0x0000`  | `LCI $t0, $t0, 0xFFFF` (h=1)  | `$t0 = C16(0xFFFF, $t0) = 0xFFFF0000`               |
| `0x0004`  | `XORI $t0, $t0, 0xFF00` (h=0) | `$t0 = 0xFFFF0000 ^ 0x0000FF00 = 0xFFFFFF00`        |
| `0x0008`  | `XORI $t1, $zero, 'R'` (h=0)  | `$t1 = 0x52`                                        |
| `0x000C`  | `SH $t0, $t1, 0`              | UART ← 'R'                                          |
| `0x0010`  | `XORI $t1, $zero, 'O'` (h=0)  | `$t1 = 0x4F`                                        |
| `0x0014`  | `SH $t0, $t1, 0`              | UART ← 'O'                                          |
| ...       | ...                           | ...                                                 |
| `0x0040`  | `XORI $t1, $zero, '\n'` (h=0) | `$t1 = 0x0A`                                        |
| `0x0044`  | `SH $t0, $t1, 0`              | UART ← '\n'                                         |
| `0x0048`  | `J 0x0048`                    | Loop infinito (`elimm=-1`, `PC = PC+4+4·(-1) = PC`) |

Instrucciones usadas, todas **verificadas por ejecución real** en el simulador (inyectadas a mano, `step`/`continue`, chequeado con `registers` y leyendo la UART por el puerto 5555): `LCI`, `XORI` (ambas variantes `h=0`/`h=1`), `SH`, `J`.

### Método manual (debug)

Si querés entender qué hace la ROM o debuggear, podés inyectarla a mano vía `telnet localhost 4444` (los valores son el volcado de instrucciones de la ROM ya generada):

```
reset
set [0x00000000] 0x239DFFFF
set [0x00000004] 0x3B9CFF00
set [0x00000008] 0x381E0052
set [0x0000000C] 0x539E0000
set [0x00000010] 0x381E004F
set [0x00000014] 0x539E0000
set [0x00000018] 0x381E004D
set [0x0000001C] 0x539E0000
set [0x00000020] 0x381E0020
set [0x00000024] 0x539E0000
set [0x00000028] 0x381E004F
set [0x0000002C] 0x539E0000
set [0x00000030] 0x381E004B
set [0x00000034] 0x539E0000
set [0x00000038] 0x381E000D
set [0x0000003C] 0x539E0000
set [0x00000040] 0x381E000A
set [0x00000044] 0x539E0000
set [0x00000048] 0x09FFFFFF
set pc 0x00000000
continue
```

⚠️ Con la sesión de telnet manual, en cuanto cierres esa conexión (o el cliente telnet) **todo el simulador se apaga** (ver gotcha arriba) — no es un bug de este método, es cómo se comporta el binario.

### Regenerar la ROM

`rom.bin` se regenera con el generador de ROM interno del proyecto (no incluido en este repo). El binario resultante (`rom.bin`) **sí está trackeado** en git.

### Troubleshooting

| Síntoma                                        | Causa probable                               | Solución                                                                                                                                                |
| ---------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `telnet localhost 5555` → "Connection refused" | El contenedor murió antes de levantar socat. | Revisá `docker logs rtm32-sim`. Si dice `ERROR: no se encontró PTY`, esperá unos segundos más antes de conectarte (el simulador tarda en crear el PTY). |
| UART vacía (no aparece `ROM OK`)               | La inyección no se completó.                 | Conectate al debugger (`telnet localhost 4444`), hacé `registers` para ver si `PC=0x00000000`. Si no, hacé `set pc 0x00000000` y `continue`.            |
| Build tarda mucho                              | Docker descargando imágenes base.            | Es normal la primera vez (~15-30s). Las siguientes usan cache.                                                                                          |

## Hello World (vía debugger)

Escribir directo en la UART (`0xFFFFFF00`) byte por byte:

```
set [0xFFFFFF00] 0x48
set [0xFFFFFF00] 0x65
set [0xFFFFFF00] 0x6C
set [0xFFFFFF00] 0x6C
set [0xFFFFFF00] 0x6F
set [0xFFFFFF00] 0x20
set [0xFFFFFF00] 0x77
set [0xFFFFFF00] 0x6F
set [0xFFFFFF00] 0x72
set [0xFFFFFF00] 0x6C
set [0xFFFFFF00] 0x64
set [0xFFFFFF00] 0x0D
set [0xFFFFFF00] 0x0A
```

Resultado visible en Terminal 1 (`Hello world`).

## UART MMIO

Escribir una halfword en `0xFFFFFF00` emite el byte bajo a la consola UART (Terminal 1) —
verificado empíricamente contra el binario nuevo. No está documentado en el manual (el
capítulo de Entrada/Salida figura como "PRONTO...", no escrito todavía); el mapa de memoria sí
dice que el bloque de dispositivos MMIO arranca en `0xFFFFF000`, y `0xFFFFFF00` cae dentro de
ese bloque.

## Comandos del debugger

Estos son los comandos **reales** del binario (extraídos de su `help`/usage), que **no**
coinciden con el capítulo 10 del manual nuevo (ese capítulo describe comandos `G`/`D R`/`D
M`/`W`/`S`/`L` que no existen en este build — no lo uses como referencia).

| Comando          | Sintaxis                                     | Descripción                                   |
| ---------------- | -------------------------------------------- | --------------------------------------------- |
| `set`            | `set r1 0xFF00` / `set [0x40] 0xEA0000`      | Setear registro o escribir palabra en memoria |
| `registers`      | `registers`                                  | Ver los 32 GPR + PC + CAUSE/EPC/BADVADR/VBR   |
| `examine`        | `examine xw 0x1000 4`, `examine bb 0x2000 8` | Ver memoria                                   |
| `step`           | `step [n]`                                   | Ejecutar n instrucciones                      |
| `continue`       | `continue`                                   | Ejecutar libre                                |
| `until`          | `until <addr>`                               | Correr hasta una dirección                    |
| `break`/`delete` | `break <addr>` / `delete b <id>`             | Breakpoints                                   |
| `watch`/`delete` | `watch <addr> [+size\|range] [r\|w\|rw]`     | Watchpoints de memoria                        |
| `list`           | `list`                                       | Listar breakpoints/watchpoints                |
| `dump`           | `dump hex\|bin <start> <end\|size> [file]`   | Volcar memoria a pantalla o archivo           |
| `load`           | `load archivo.bin [fast\|exact]`             | Cargar snapshot (**no** acepta binarios raw)  |
| `reset`          | `reset`                                      | Reset CPU (PC → `0xF0000000`, modo KERNEL)    |
| `help`           | `help [comando]`                             | Ayuda                                         |
| `quit`           | `quit`                                       | Terminar simulación (¡mata todo el proceso!)  |

> **Handshake:** al conectar, el debugger descarta silenciosamente las primeras dos líneas
> enviadas (negociación). Mandá dos líneas de relleno antes del primer comando real.

## Codificar instrucciones a mano

El simulador no trae ensamblador: cada instrucción se codifica a mano (opcode/func/rs/rt/rd/param/imm) y se inyecta en memoria con `set [addr] palabra` (`load archivo.bin exact` no acepta binarios raw, ver arriba).

- **R-type** (`opcode=00000`): `opcode|rs|rt|rd|param(5b)|x(1)|func(6b)` — ALU, shifts, saltos indexados, `CFS`/`CTS`, `TRAP`/`RFT`.
- **I-type básico**: `opcode|rs|rt|imm(17b)` — loads/stores directos, branches, `ADDI`, `SLTI`/`SLTIU`.
- **I-type inmediato extendido**: `opcode|rs|rt|h(1)|simm(16b)` — `ANDI`/`LCI`, `ANI`/`ANH`, `ORI`/`ORH`, `XORI`/`XORH` (`h` elige variante inmediata vs. variante "concat" para construir constantes de 32 bits).
- **J-type**: `opcode|so(2b)|elimm(25b)` para `J`/`JAL` (salto **relativo al PC**, no absoluto), o `opcode|1|lr(2b)|vlimm(24b)` para `JALX`.

Registros: `$0`-`$31` de propósito general (numeración **física**, ver tabla abajo — la máquina nueva no requiere traducción MIPS) + `$pc` + 7 registros especiales (`$psw`, `$ecr`, `$epc`, `$esr`, `$bva`, `$vbr`, `$pir`) accedidos vía `CFS`/`CTS`.

> **Convención Tabla 3.1 del manual (Jul 2026), YA son los números físicos:** `$zero`($0), `$ra`($1), `$k0,$k1`($2-3), `$lr0-$lr3`($4-7), `$a0-$a5`($8-13, alias `$v0,$v1`=`$a0,$a1`), `$t0-$t5`($14-19), `$s0-$s7`($20-27), `$fp`($28, alias `$s8`), `$gp`($29, alias `$s9`), `$sp`($30), `$at`($31).

## Bugs y comportamiento no documentado

Encontrados corriendo casos límite contra el simulador real (Casos 57-59 de `pruebas-stx4.md`, ahí está el detalle completo con encodings y valores):

- **`MUL` setea flags `C` (overflow sin signo) y `V` (overflow con signo)** — la Tabla B.2 del manual no menciona flags para ninguna instrucción aritmética R-type, pero el binario las calcula de verdad: barrido de 4 combinaciones de operandos muestra que `C` y `V` responden al signo real de los operandos, no son ruido. Ejemplo: `0xFFFFFFFF * 2` da `Flags: [N-C--]` (overflow sin signo, `V` no se setea porque el resultado con signo es válido) mientras que `0x7FFFFFFF * 2` (mismo resultado en `R[rd]`) da `Flags: [N--V-]` (acá sí desborda con signo). Orden del campo `Flags: [_____]` de `registers`: `N Z C V _`.

- **El bug real no es "`TRAP` y `RFT` están rotos" — es que cualquier excepción deja la CPU trabada para siempre.** El manual no documenta códigos de `CAUSE` ni el comportamiento de excepciones (Cap. 8 = "PRONTO..."). Lo que se ve desde afuera:
  - `TRAP`, y también división por cero / resto por cero / overflow de división (`INT_MIN / -1`), ponen `CAUSE` en un código fijo (`0x6` para `TRAP`, `0x3` para las excepciones aritméticas — sin distinguir división por cero de overflow), avanzan `PC` a `PC+4` como si nada (no hay salto a ningún vector), y corrompen `$vbr` a `0x00000002`. `TRAP` además nunca llega a escribir `$epc` pese a que la fórmula documentada dice que debería.
  - Probado por separado, `RFT` (`PC=EPC`, `$psw` restaurado desde `$esr`) **funciona perfecto** si todavía no ocurrió ninguna excepción en la sesión: salta a `$epc` y cambia de modo `KERNEL` a `USER` como corresponde. La conclusión anterior de "`RFT` no hace nada" era un artefacto de haberlo probado después de que la CPU ya estuviera trabada por otra causa.
  - La prueba definitiva: tras un `DIV` por cero, se intentó ejecutar cinco instrucciones `ADD` inofensivas puestas a propósito en el camino. Ninguna corrió — `PC` y hasta el campo `Last Memory Operation` (que sigue mostrando la dirección de la excepción original) quedaron congelados bit a bit en 6 `step` consecutivos. Pedirle `continue` al simulador en ese estado lo confirma con su propio mensaje: `[Execution Fault: Core Exception 3 thrown at PC 0x00000004] / Core execution stopped.` — la CPU se niega a ejecutar cualquier instrucción más, y ni siquiera `RFT` (que debería ser la salida) la revive. La única forma de recuperarla es `reset`.
