# Install system ODBC libs required by pyodbc (Debian/Ubuntu)
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc \
    unixodbc-dev \
    libodbc1 \
    odbcinst \
    build-essential \
    python3-dev \
 && rm -rf /var/lib/apt/lists/*
