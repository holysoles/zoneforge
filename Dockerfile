FROM python:3.13-slim

ARG VERSION

WORKDIR /app

# Copy the necessary files and directories into the container
COPY static/ ./static/
COPY lib/examples/ ./lib/examples/
COPY templates/ ./templates/
COPY zoneforge/ ./zoneforge/
COPY requirements/  ./requirements/
COPY app.py ./

# create non-root user
RUN useradd -m -u 1000 appuser
RUN chown -R appuser:appuser /app
USER appuser

# Upgrade pip and install Python dependencies
RUN pip3 install --upgrade pip && pip install --no-cache-dir -r requirements/prod.txt

ENV CONTAINER="true"
ENV VERSION=$VERSION
ENV PORT=5000
ENV GUNICORN_WORKERS=4
ENV GUNICORN_CMD_ARGS="--bind 0.0.0.0:${PORT} --workers ${GUNICORN_WORKERS}"
ENV PATH="${PATH}:/home/appuser/.local/bin"
EXPOSE ${PORT}/tcp
CMD ["gunicorn", "app:production"]