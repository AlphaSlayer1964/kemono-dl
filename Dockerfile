FROM python:3.13-slim

WORKDIR /app

COPY kemono_dl/ ./kemono_dl/
COPY pyproject.toml ./

RUN pip install --no-cache-dir .

RUN mkdir -p /media /appdata
VOLUME ["/media", "/appdata"]

ENTRYPOINT ["kemono-dl"]
