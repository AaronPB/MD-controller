A docker image to control the Membrane Distillation (MD) plant located at the IFAPA research centre, as part of the [Agroconnect](https://agroconnect.es/) project.

> [!WARNING]
> This project is currently under development and code may be unstable.

## Description

The goal is to develop an open-source, virtualized system that includes all the necessary components to produce a sustainable water supply using solar energy, Reverse Osmosis, and Membrane Distillation technologies.

To achieve this, a Docker-based environment has been created for both simulation and real deployment of a web-based SCADA system for the RO+MD unit at IFAPA, using [FUXA](https://github.com/frangoteam/FUXA).

This repository proposes a modular approach to integrating controllers into the network using the MQTT protocol, which is highly efficient and compatible with FUXA.

## The docker-compose file

Below is a simple example of how the Docker Compose setup works using this project.

```yaml
networks:
  fuxa-net:
    driver: bridge

services:
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: mosquitto
    networks:
      - fuxa-net
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - ./mosquitto/data:/mosquitto/data
      - ./mosquitto/log:/mosquitto/log
    restart: unless-stopped

  fuxa:
    image: frangoteam/fuxa
    container_name: fuxa
    networks:
      - fuxa-net
    ports:
      - "1881:1881"
    volumes:
      - ./fuxa/_appdata:/usr/src/app/FUXA/server/_appdata
      - ./fuxa/_db:/usr/src/app/FUXA/server/_db
      - ./fuxa/_logs:/usr/src/app/FUXA/server/_logs
      - ./fuxa/_images:/usr/src/app/FUXA/server/_images
    environment:
      - TZ=Europe/Madrid
    restart: unless-stopped

  md-control:
    container_name: md-control
    build:
      context: ../path/to/repo/MD-controller
    networks:
      - fuxa-net
    volumes:
      - ./config-md-controllers.yml:/app/config.yml
    restart: unless-stopped
```

## Acknowledgements

This work is part of the R&D&I project PID2023-150739OB-I00, funded by MCIN/AEI/10.13039/501100011033/ and “FEDER – A way of making Europe.”

The work has also been partially funded by the European Union’s LIFE Programme under grant agreement number LIFE23-ENV-ES-SALTEAU/101148475.
