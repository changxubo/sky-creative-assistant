FROM cnharbor.amway.com.cn/lightai/uv:python3.12-bookworm

# Install uv.
COPY --from=cnharbor.amway.com.cn/lightai/uv:latest /uv /bin/uv

WORKDIR /app

# Pre-cache the application dependencies.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy the application into the container.
COPY . /app
COPY ./config-nim.yaml /app/config.yaml

# Install the application dependencies.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 8000

# Run the application.
CMD ["uv", "run", "python", "server.py", "--host", "0.0.0.0", "--port", "8000"]
