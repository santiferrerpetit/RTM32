# RTM32 — Simulador de CPU STX4

Harness Docker para correr el simulador precompilado de **STX4**, una CPU RISC de 32 bits custom, dentro del sistema **RTM32**. El simulador expone un debugger remoto por telnet y una consola UART, ambas sobre TCP.

Este repo no tiene código fuente propio: el "binario" a ejecutar (`rtm32.s`) ya viene compilado. Lo único editable acá es el `Dockerfile` y este README.

## Contenido del repo

| Archivo           | Qué es                                                                                                                        |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `rtm32.s`         | Simulador (ELF x86-64 estático). A pesar de la extensión `.s`, **es un binario**, no assembly. Es lo que corre el contenedor. |
| `rtm32`           | Misma build del simulador, pero dinámica y sin strip. No la usa Docker; sirve para debuggear en el host directamente.         |
| `rtm32.pdf`       | Manual de arquitectura/ISA de STX4 (español). Referencia de registros, formatos de instrucción y opcodes (Apéndice A).        |
| `Dockerfile`      | Imagen que corre el simulador + un puente `socat` para la UART.                                                               |
| `pruebas-stx4.md` | Batería de pruebas manuales de instrucciones (casos con precondición/código/postcondición/conclusión).                        |

## Requisitos

- Docker Desktop corriendo

## Uso

```bash
docker build -t rtm32 .
docker run -d --name rtm32-sim -p 4444:4444 -p 5555:5555 rtm32
```

Esto levanta `rtm32.s -d telnet -m 64K` (debugger por telnet, 64K de memoria) y un puente `socat` que expone la UART del simulador en el puerto 5555.

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

Único dispositivo mapeado en memoria en esta configuración: escribir un byte en `0xFFFFFF00` lo emite a la consola UART (Terminal 1).

## Comandos del debugger

| Comando                  | Descripción                 |
| ------------------------ | --------------------------- |
| `set r1 0x1234`          | Setear registro             |
| `set [0x1000] 0xABCD`    | Escribir palabra en memoria |
| `registers`              | Ver todos los registros     |
| `examine xw 0x0000 4`    | Ver memoria                 |
| `step 1`                 | Ejecutar N instrucciones    |
| `continue`               | Ejecutar libre              |
| `load archivo.bin exact` | Cargar binario en memoria   |
| `reset`                  | Reset CPU                   |
| `quit`                   | Terminar simulación         |

## Codificar instrucciones a mano

El simulador no trae ensamblador: cada instrucción se codifica a mano (opcode/func/rs/rt/rd/aux/imm) según el Apéndice A de `rtm32.pdf`, y se inyecta en memoria con `set [addr] palabra` o vía `load archivo.bin exact`.

Resumen rápido de formatos (detalle completo en el PDF):

- **R-type** (`opcode=00000`): `opcode|rs|rt|rd|aux|X|func` — ALU, shifts, saltos por registro, CFS/CTS, TRAP/RFT.
- **I-type**: `opcode|rs|rt|imm(17b)` — loads/stores directos, branches, ADDI, SLTI/SLTIU.
- **L-type**: `opcode|rs|rt|h|imm(16b)` — ANDI/H, ORI/H, XORI/H, LUI (`h` elige mitad alta/baja del inmediato).
- **J-type**: `opcode|jump_address(27b)` — J/JAL incondicionales.

Registros: `$0`-`$31` de propósito general + `$pc` + 5 registros especiales (`$psw`, `$ecr`, `$epc`, `$bva`, `$vbr`) accedidos vía `CFS`/`CTS`. Convención tipo MIPS (`$zero`, `$at`, `$a0-$a3`, `$v0-$v1`, `$t0-$t9`, `$s0-$s7`, `$fp`, `$gp`, `$sp`, `$ra`).

Ver `pruebas-stx4.md` para casos de prueba reales, con encoding, código inyectado y resultado esperado por instrucción.
