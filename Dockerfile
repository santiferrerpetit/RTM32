FROM ubuntu:22.04
RUN apt-get update -qq && apt-get install -y -qq socat python3 && rm -rf /var/lib/apt/lists/*
COPY rtm32 /rtm32
RUN chmod +x /rtm32
COPY rom.bin /rom.bin
COPY inject_rom.py /inject_rom.py
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
EXPOSE 4444 5555
CMD ["/docker-entrypoint.sh"]
