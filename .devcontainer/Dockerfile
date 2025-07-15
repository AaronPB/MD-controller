FROM python:3.13.3-slim

COPY --from=ghcr.io/astral-sh/uv:0.7.20 /uv /uvx /bin/

RUN useradd -ms /bin/bash vscodeuser

WORKDIR /app

COPY . .

RUN uv sync --locked

RUN chown -R vscodeuser:vscodeuser /app

USER vscodeuser
