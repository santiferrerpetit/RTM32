#!/bin/bash

# No usar set -e para evitar que el contenedor muera por fallos menores
# set -e

echo "[BOOT] Iniciando simulador STX4..."
/rtm32 -d telnet -m 64K &>/tmp/rtm32.log &
SIM_PID=$!

# Esperar a que el simulador realmente esté corriendo
sleep 2

# Verificar que el proceso existe
if ! kill -0 $SIM_PID 2>/dev/null; then
  echo "[BOOT] ERROR: el simulador no levantó. Últimas líneas del log:"
  tail -5 /tmp/rtm32.log 2>/dev/null || echo "(log vacío o no existe)"
  # Aún así mantener el contenedor vivo para debugging
  echo "[BOOT] Manteniendo contenedor vivo para inspección..."
  tail -f /dev/null
  exit 1
fi

# Esperar a que UART PTY aparezca
PTY=""
for i in $(seq 1 20); do
  PTY=$(grep 'UART available on' /tmp/rtm32.log 2>/dev/null | grep -o '/dev/pts/[0-9]*' | tail -1)
  if [ -n "$PTY" ] && [ -c "$PTY" ]; then
    break
  fi
  sleep 1
done

if [ -z "$PTY" ] || [ ! -c "$PTY" ]; then
  echo "[BOOT] ERROR: no se encontró PTY de UART"
  echo "[BOOT] Log del simulador:"
  cat /tmp/rtm32.log 2>/dev/null || true
  kill $SIM_PID 2>/dev/null || true
  tail -f /dev/null
  exit 1
fi

echo "[BOOT] UART PTY: $PTY"
stty -F "$PTY" raw -echo -echoe -echok -echoctl -echoke

# Levantar socat
socat -u "$PTY" TCP-LISTEN:5555,reuseaddr,fork &
SOCAT_PID=$!
echo "[BOOT] socat bridge UART→5555 activo (PID $SOCAT_PID)"

# Esperar a que debugger esté listo
sleep 2

# Inyectar ROM (queda corriendo en background: mantiene la conexión al debugger
# abierta para siempre porque cerrarla mata el proceso rtm32 completo, ver
# inject_rom.py)
echo "[BOOT] Inyectando ROM en memoria..."
python3 /inject_rom.py &
INJECT_PID=$!
sleep 1
if ! kill -0 $INJECT_PID 2>/dev/null; then
  echo "[BOOT] WARNING: falló la inyección automática."
  echo "               Conectá manualmente al debugger (telnet localhost 4444) y usá inject_rom.py"
fi

# Mantener vivo
echo "[BOOT] Sistema listo."
echo "       Debugger: telnet <host> 4444"
echo "       UART:     telnet <host> 5555"
echo ""
echo "       La ROM debería estar cargada. Conectá a la UART para ver 'ROM OK'."
echo ""

wait $SIM_PID
