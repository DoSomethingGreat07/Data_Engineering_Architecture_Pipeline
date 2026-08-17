FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    default-jre-headless \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements /tmp/requirements
RUN python -m pip install --upgrade pip && \
    pip install -r /tmp/requirements/development.txt

COPY . /workspace

CMD ["bash"]
