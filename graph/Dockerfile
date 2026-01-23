FROM python:3.11-slim

WORKDIR /workspace

# System deps for matplotlib fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

CMD ["make", "paper"]
