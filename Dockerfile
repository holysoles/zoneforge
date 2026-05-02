FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

ARG VERSION

RUN groupadd --system --gid 999 nonroot \
	&& useradd --system --gid 999 --uid 999 --create-home nonroot

# Recommended uv options
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy
# Ensure installed tools can be executed out of the box
ENV UV_TOOL_BIN_DIR=/usr/local/bin
# use uv to install deps
RUN --mount=type=cache,target=/root/.cache/uv \
	--mount=type=bind,source=uv.lock,target=uv.lock \
	--mount=type=bind,source=pyproject.toml,target=pyproject.toml \
	uv sync --locked --no-install-project --no-dev --group prod
# reset entrypoint from uv
ENTRYPOINT []

# Copy the necessary files and directories into the container
WORKDIR /app
COPY static/ ./static/
COPY lib/examples/ ./lib/examples/
COPY templates/ ./templates/
COPY zoneforge/ ./zoneforge/
COPY app.py pyproject.toml uv.lock ./

# install Python dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --locked --no-dev --group prod

RUN chown -R nonroot:nonroot /app
USER nonroot
ENV CONTAINER="true"
ENV VERSION=$VERSION
ENV PORT=5000
ENV GUNICORN_WORKERS=4
ENV GUNICORN_CMD_ARGS="--bind 0.0.0.0:${PORT} --workers ${GUNICORN_WORKERS}"
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE ${PORT}/tcp
CMD ["gunicorn", "app:production"]
