# syntax=docker/dockerfile:1.7
# =============================================================================
# MAKU - production image
#   * multi-stage: build tools never reach the runtime image
#   * fonts-noto-core is installed in a build stage and only the 4 TTF files
#     the PDF exporter needs (Latin + Arabic) are copied into the runtime
#     image - not the whole ~100 MB package
#   * runs as an unprivileged user, tini as PID 1, built-in healthcheck
# =============================================================================

ARG PYTHON_IMAGE=python:3.12-slim-bookworm

# ---- 1. Python dependencies -------------------------------------------------
FROM ${PYTHON_IMAGE} AS deps
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# ---- 2. Fonts for Arabic PDF rendering ---------------------------------------
FROM debian:bookworm-slim AS fonts
RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-noto-core \
 && mkdir -p /fonts \
 && cp /usr/share/fonts/truetype/noto/NotoSans-Regular.ttf \
       /usr/share/fonts/truetype/noto/NotoSans-Bold.ttf \
       /usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf \
       /usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf /fonts/

# ---- 3. Runtime ---------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime
RUN apt-get update \
 && apt-get install -y --no-install-recommends tini curl \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 10001 --shell /usr/sbin/nologin maku

COPY --from=fonts /fonts/ /usr/share/fonts/truetype/noto/
COPY --from=deps /opt/venv /opt/venv

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    MAKU_DB_PATH=/app/data/maku_site_data.db

WORKDIR /app
COPY --chown=maku:maku . /app
RUN mkdir -p /app/data && chown maku:maku /app/data && chmod +x /app/docker-entrypoint.sh

USER maku
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8501/_stcore/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/app/docker-entrypoint.sh"]
CMD ["streamlit", "run", "app.py", "--server.enableCORS=true"]
