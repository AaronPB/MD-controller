import logging
import time
import signal
import sys
import json
import paho.mqtt.client as mqtt

from typing import Any

from config_manager import ConfigManager
from enums.config_paths import ConfigPaths
# from controllers import PIController_Pump

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Define configuration manager
cfg_mngr = ConfigManager()

# Topic values handler
# TODO Maybe prepare a data handler class, idk
mqtt_topics: dict[str, float] = {}

def load_mqtt_topics():
    global mqtt_topics
    mqtt_topics = {
        cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_FIR.value): -1.0,
        cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_TIC.value): -1.0,
        cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_FIR.value): -1.0,
        cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_TIC.value): -1.0
    }

def on_connect(client: mqtt.Client, userdata: Any, flags: dict[str, Any], rc: int) -> None:
    if rc == 0:
        logging.info("Correctly connected to MQTT broker.")
        # Configure topic connections
        # TODO Is this better?? -> client.subscribe_callback()
        topic_list = [client.subscribe(topic) for topic in mqtt_topics]
        logging.info(f"Successfully subscribed into {len(topic_list)} mqtt topics")
    else:
        logging.error(f"Connection error, code {rc}")

def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        try:
            payload = msg.payload.decode('utf-8')
            data: dict = json.loads(payload)
            value = float(data.get("value", None))
            topic_key = mqtt_topics.get(msg.topic)

            if topic_key:
                mqtt_topics[topic_key] = value
                logging.info(f"{topic_key} updated with value: {value}")
        except Exception as e:
            logging.error(f"Error trying to process mqtt message from {msg.topic}: {e}")


def run(client: mqtt.Client) -> None:
    # TODO WIP - Code test, change accordingly
    while True:
        bomb_percent = 50.17
        message = json.dumps({"value": bomb_percent})
        result = client.publish("fuxa/command/bomb_percent", message)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logging.info(f"Publish Pump OP: {bomb_percent:.2f}%")
        else:
            logging.warning(f"Error publishing mqtt message, code: {result.rc}")
        time.sleep(2)


def main() -> None:
    # Load configuration file
    cfg_mngr.load_config(file_path="config.yml")
    load_mqtt_topics()
    # Prepare topics list
    # Configure MQTT topics
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    # Closure for container interrumptions
    def signal_handler(sig, frame):
        logging.info("Stopping controllers and MD operations")
        client.loop_stop()
        client.disconnect()
        logging.info("Disconnected from MQTT Broker")
        sys.exit(0)
    signal.signal(signal.SIGTERM, signal_handler)
    # TODO Configure PI Controllers

    # Connect to MQTT Broker and start loop
    try:
        client.connect(host="mosquitto")
    except Exception as e:
        logging.critical(f"Could not connect to the MQTT Broker: {e}")
        return

    client.loop_start()
    # Run main process
    run(client)


if __name__ == "__main__":
    main()