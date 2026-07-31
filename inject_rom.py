#!/usr/bin/env python3
"""
Inyecta rom.bin en memoria del simulador STX4 via debugger TCP y arranca la CPU.

Dado que 'load rom.bin exact' espera un formato snapshot (no raw binary) y que
el flag '-r/--rom' no tiene efecto en este build (ver nota en build_rom.py), este
script envia las palabras no-cero de la ROM usando 'set [addr] word', setea
PC=0x0000 y ejecuta continue.

IMPORTANTE: en este build, cerrar la conexion telnet del debugger termina TODO
el proceso rtm32 (no solo la sesion de depuracion) -- se verifico que al cerrar
el socket tras 'continue', el simulador se apaga inmediatamente ("Debugger
session channel context destroyed cleanly" seguido de "Destroying serial
device" en el log). Por eso este script NUNCA cierra el socket: despues de
'continue' se queda bloqueado indefinidamente mantiendo la conexion viva. Debe
ejecutarse en background (ver docker-entrypoint.sh).
"""
import socket, time, struct, sys, os

HOST = "127.0.0.1"
PORT = 4444

ROM_PATH = "/rom.bin"


def send_cmd(sock, cmd, delay=0.15):
    sock.sendall((cmd + "\r\n").encode())
    time.sleep(delay)
    data = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            if len(chunk) < 4096:
                break
    except socket.timeout:
        pass
    return data.decode("ascii", errors="replace")


def inject():
    if not os.path.exists(ROM_PATH):
        print(f"ERROR: no existe {ROM_PATH}")
        sys.exit(1)

    with open(ROM_PATH, "rb") as f:
        rom = f.read()

    print(f"[INJECT] Conectando al debugger {HOST}:{PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect((HOST, PORT))
    time.sleep(0.5)

    # Handshake del debugger (descarta las 2 primeras lineas negociadas)
    send_cmd(sock, "dummy1", delay=0.3)
    send_cmd(sock, "dummy2", delay=0.3)

    print("[INJECT] Reset CPU...")
    send_cmd(sock, "reset", delay=0.3)

    words_injected = 0
    total_words = len(rom) // 4
    for i in range(total_words):
        word = struct.unpack_from('<I', rom, i * 4)[0]
        if word != 0:
            addr = i * 4
            cmd = f"set [0x{addr:08X}] 0x{word:08X}"
            send_cmd(sock, cmd, delay=0.05)
            words_injected += 1

    print(f"[INJECT] Cargadas {words_injected} palabras.")

    send_cmd(sock, "set pc 0x00000000", delay=0.2)
    send_cmd(sock, "continue", delay=0.2)
    print("[INJECT] ROM lista. CPU ejecutando.")

    # No cerrar el socket: cerrarlo mata el proceso rtm32 completo.
    sock.settimeout(None)
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                print("[INJECT] El simulador cerro la conexion. Saliendo.")
                break
        except OSError:
            break


def main():
    inject()


if __name__ == "__main__":
    main()
