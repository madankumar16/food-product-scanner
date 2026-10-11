FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=8080
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt gunicorn==26.2.0
COPY --chown=appuser:appuser *.py ./
COPY --chown=appuser:appuser templates ./templates
COPY --chown=appuser:appuser static ./static
USER appuser
EXPOSE 8080
CMD gunicorn --workers 2 --threads 8 --bind 0.0.0.0:${PORT} --timeout 60 app:app
