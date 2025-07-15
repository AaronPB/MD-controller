FROM python:3.13.3-slim

COPY --from=ghcr.io/astral-sh/uv:0.7.20 /uv /uvx /bin/

WORKDIR /app

COPY . .

RUN uv sync --locked

CMD ["uv", "run", "src/main.py"]
