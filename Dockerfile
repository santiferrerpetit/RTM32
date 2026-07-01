FROM ubuntu:22.04
RUN apt-get update -qq && apt-get install -y socat telnet picocom && rm -rf /var/lib/apt/lists/*
COPY rtm32.s /rtm32
RUN chmod +x /rtm32
EXPOSE 4444 5555
CMD bash -c "\
  /rtm32 -d telnet -m 64K &> /tmp/rtm32.log & \
  sleep 1 && \
  PTY=\$(grep 'UART available on' /tmp/rtm32.log | grep -o '/dev/pts/[0-9]*') && \
  echo \"UART en \$PTY\" && \
  stty -F \$PTY raw -echo -echoe -echok -echoctl -echoke && \
  socat -u \$PTY TCP-LISTEN:5555,reuseaddr,fork &\
  wait"
