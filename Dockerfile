FROM python:3.11-slim

WORKDIR /workspace

# Dépendances système nécessaires à geopandas (GDAL, GEOS, PROJ)
RUN apt-get update && apt-get install -y \
    gdal-bin libgdal-dev libgeos-dev libproj-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
