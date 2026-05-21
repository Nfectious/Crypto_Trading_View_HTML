FROM python:3.11-slim

WORKDIR /opt/valkyrie

# gcc + libpq-dev required to build psycopg2 from source if needed;
# psycopg2-binary in requirements.txt avoids this but the headers are kept as a safety net.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY scanner/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY scanner/ .

RUN mkdir -p /opt/valkyrie/logs

# Unbuffered output so logs appear in docker logs immediately
CMD ["python", "-u", "headless_scanner.py"]
