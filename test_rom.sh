#!/bin/bash
set -e

echo "=== Test ROM boot STX4 ==="
echo ""

# 1. Limpiar contenedor previo
docker rm -f rtm32-sim 2>/dev/null || true

# 2. Build
echo "[1/4] Build imagen Docker..."
docker build --platform linux/amd64 -t rtm32 . >/dev/null 2>&1

# 3. Run
echo "[2/4] Levantando contenedor..."
docker run -d --platform linux/amd64 --name rtm32-sim -p 4444:4444 -p 5555:5555 rtm32 >/dev/null

# 4. Esperar a que bootee
echo "[3/4] Esperando boot (5s)..."
sleep 5

# 5. Leer UART
echo "[4/4] Leyendo UART..."
python3 -c "
import socket, time
s = socket.socket()
s.settimeout(3)
try:
    s.connect(('localhost', 5555))
    time.sleep(1)
    data = s.recv(4096)
    text = data.decode('ascii', errors='replace')
    if 'ROM OK' in text:
        print('✅ EXITO: ROM OK recibido por UART')
        print('   Output:', repr(text))
    else:
        print('❌ FALLA: no se recibio ROM OK')
        print('   Output:', repr(text))
except Exception as e:
    print('❌ ERROR:', e)
finally:
    s.close()
"

# 6. Cleanup
docker rm -f rtm32-sim 2>/dev/null || true

echo ""
echo "=== Fin ==="
