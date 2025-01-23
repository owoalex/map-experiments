FROM debian:bookworm
SHELL ["/bin/bash", "-c"]
RUN apt-get update
RUN apt-get install -y tar unzip wget osm2pgsql net-tools curl
STOPSIGNAL SIGQUIT
