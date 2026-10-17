FROM pwn.red/jail

COPY --from=ubuntu:24.04 / /srv

COPY ./src/challenge /srv/app/challenge

RUN chmod 755 /srv/app/challenge && \
    ln -s /app/challenge /srv/app/run

RUN echo "COMPFEST18{we_have_rop_mprotect_at_home_ahhh_chall}" > /srv/flag.txt && \
    chmod 444 /srv/flag.txt

ENV JAIL_TIME=60
ENV JAIL_MEM=64M
ENV JAIL_PIDS=16
ENV JAIL_CPU=100