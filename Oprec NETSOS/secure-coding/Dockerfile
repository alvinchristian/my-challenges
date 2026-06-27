FROM ubuntu:24.04@sha256:d1e2e92c075e5ca139d51a140fff46f84315c0fdce203eab2807c7e495eff4f9

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        socat \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN rm -rf /var/lib/apt/lists/*
RUN     useradd ctf
WORKDIR /home/ctf

COPY ./src/chall.c /home/ctf/
COPY ./src/libc.so.6 /home/ctf/
COPY ./src/ld-linux-x86-64.so.2 /home/ctf/
COPY ./src/flag.txt /home/ctf/

RUN chown -R root:root  /home/ctf
RUN chmod -R 755        /home/ctf
RUN gcc -Wl,-z,relro,-z,lazy chall.c -o chall -Wno-implicit-function-declaration

EXPOSE 1337
ENTRYPOINT ["socat", "TCP-LISTEN:9999,reuseaddr,fork,nodelay,su=ctf", "EXEC:'timeout 60 ./chall'"]
