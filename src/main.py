import logging
import time
import signal
import sys
import json
import paho.mqtt.client as mqtt

from typing import Any

from config_manager import ConfigManager
from enums.config_paths import ConfigPaths
from controllers import PIController_Pump

# Logger configuration
logging.basicConfig(
    level=logging.DEBUG,
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
        cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_FIR.value): 0.0,
        cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_TIC.value): 0.0,
        cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_FIR.value): 0.0,
        cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_TIC.value): 0.0,
        cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_SP.value): 3.0,
        cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_SP.value): 3.0
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
            # data: dict = json.loads(payload)
            # logging.debug(payload)
            logging.debug(f"Raw MQTT topic received: {msg.topic} with payload: {payload}")
            # value = float(data.get("value", None))
            # value = float(data)
            topic_key = mqtt_topics.get(msg.topic)
            # logging.debug(f"Received data from topic key: {topic_key}, with value: {value}")

            if topic_key is not None:
                mqtt_topics[msg.topic] = float(payload)
                logging.info(f"{topic_key} updated with value: {float(payload)}")
        except Exception as e:
            logging.error(f"Error trying to process mqtt message from {msg.topic}: {e}")


def run(client: mqtt.Client, PI_P1: PIController_Pump, PI_P2: PIController_Pump) -> None:
    # TODO WIP
    while True:
        P1_SP = mqtt_topics[cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_SP.value)]
        P2_SP = mqtt_topics[cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_SP.value)]
        P1_FIR = mqtt_topics[cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_FIR.value)]
        P2_FIR = mqtt_topics[cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_FIR.value)]
        # logging.debug(f"Pumps SP: {P1_SP:.2f} | {P2_SP:.2f}")
        # logging.debug(f"FIR m3/h: {P1_FIR:.2f} | {P2_FIR:.2f}")
        if PI_P1.get_sp() != P1_SP:
            PI_P1.set_sp(P1_SP)
        if PI_P2.get_sp() != P2_SP:
            PI_P2.set_sp(P2_SP)
        p1_compute = PI_P1.compute(y=P1_FIR)
        p2_compute = PI_P2.compute(y=P2_FIR)
        if p1_compute:
            # message = json.dumps({"value": PI_P1.get_op()})
            result = client.publish(cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_OP.value), PI_P1.get_op())
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logging.info(f"Publish Pump 1 OP: {PI_P1.get_op():.2f}%")
                PI_P1.set_last_u(u=PI_P1.get_op())
            else:
                logging.warning(f"Error publishing mqtt message, code: {result.rc}")
        if p2_compute:
            # message = json.dumps({"value": PI_P2.get_op()})
            result = client.publish(cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_OP.value), PI_P2.get_op())
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logging.info(f"Publish Pump 2 OP: {PI_P2.get_op():.2f}%")
                PI_P2.set_last_u(u=PI_P2.get_op())
            else:
                logging.warning(f"Error publishing mqtt message, code: {result.rc}")

        logging.debug(f"Controllers Pumps OP: {PI_P1.get_op():.2f} | {PI_P2.get_op():.2f}")
        logging.debug(f"Controllers Pumps Triggers: {p1_compute} | {p2_compute}")

        # Just to simulate pump models
        # mqtt_topics[cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_FIR.value)] = 0.9243*mqtt_topics[cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_FIR.value)] + 0.0113*PI_P1.get_u_deque()[0]
        # mqtt_topics[cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_FIR.value)] = 0.9580*mqtt_topics[cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_FIR.value)] + 0.0057*PI_P2.get_u_deque()[0]
        
        time.sleep(2)


def main() -> None:
    # Load configuration file
    cfg_mngr.load_config(file_path="config.yml")
    # Prepare topics list
    load_mqtt_topics()
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
    # Configure PI Controllers
    p1_controller = PIController_Pump(id="Pump 1 PI",params=cfg_mngr.get_value(ConfigPaths.P1_PI_CONTROL_SECTION.value))
    p2_controller = PIController_Pump(id="Pump 2 PI",params=cfg_mngr.get_value(ConfigPaths.P2_PI_CONTROL_SECTION.value))
    p1_controller.set_manual(False)
    p2_controller.set_manual(False)
    # Connect to MQTT Broker and start loop
    try:
        client.connect(host="mosquitto")
    except Exception as e:
        logging.critical(f"Could not connect to the MQTT Broker: {e}")
        return

    client.loop_start()
    # Run main process
    run(client,p1_controller,p2_controller)


if __name__ == "__main__":
    main()