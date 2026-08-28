FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        build-essential \
        libpq-dev \
        postgresql-16 \
        postgresql-client-16 \
        python3 \
        python3-pip \
        python3-venv \
        python3.12-venv \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 (matches project prerequisites)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ubuntu

USER ubuntu
WORKDIR /home/ubuntu
