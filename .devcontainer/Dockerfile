FROM python:3.13.3-slim

RUN useradd -ms /bin/bash vscodeuser

WORKDIR /app

RUN pip install --upgrade pip && pip install paho-mqtt pyyaml

RUN chown -R vscodeuser:vscodeuser /app

USER vscodeuser
