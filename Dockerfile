FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

RUN mkdir -p /app/data/input /app/data/output

VOLUME ["/app/data"]

ENTRYPOINT ["green-planner"]
CMD ["--help"]
