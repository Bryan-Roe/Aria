FROM mcr.microsoft.com/devcontainers/python:2-3.14-trixie@sha256:43311767f101e1c2a7bd0ecacf2c866f5c42124fc2efe45bb384eb2995ecce4d

# Some upstream base images include a Yarn apt source that can fail signature
# verification when its key is unavailable. We do not require Yarn for this
# container build, so remove Yarn-specific apt sources before updating indexes.
RUN find /etc/apt/sources.list.d -maxdepth 1 -type f \( -iname '*yarn*' -o -iname '*dl_yarnpkg_com*' \) -delete || true

# Install system ODBC libs required by pyodbc and Azure SQL connectivity.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gnupg \
    odbcinst \
    python3-dev \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*
