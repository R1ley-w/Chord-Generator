FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    fluidsynth \
    lame \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/soundfonts && \
    curl -sL "https://raw.githubusercontent.com/arbruijn/TimGM6mb/master/TimGM6mb.sf2" \
    -o /app/data/soundfonts/TimGM6mb.sf2

EXPOSE 8000

CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
