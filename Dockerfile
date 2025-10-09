# ---- Base image ----
FROM python:3.7-slim

# ---- System setup ----
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (needed for geopandas, shapely, lxml)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgeos-dev \
    libproj-dev \
    gdal-bin \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---- Create non-root user ----
ENV USER=appuser
ENV HOME=/home/$USER
RUN useradd -m -u 1000 $USER

WORKDIR $HOME

# ---- Python dependencies ----
COPY requirements.txt .

# Install Python and pip packages
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy Streamlit app ----
COPY . $HOME/
RUN chown -R $USER:$USER $HOME

# ---- Switch to non-root user ----
USER $USER

# ---- Streamlit environment variables ----
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV PYTHONUNBUFFERED=1
# Solve Streamlit cache and Matplotlib permission issues
ENV HOME=/tmp
ENV DIJITSO_CACHE_DIR=/tmp/dijitso
ENV XDG_CACHE_HOME=/tmp
ENV MPLCONFIGDIR=/tmp/mplconfig

# ---- Expose port ----
EXPOSE 8501

# ---- Healthcheck ----
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# ---- Launch command ----
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]
