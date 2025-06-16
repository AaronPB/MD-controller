import logging
import time
import signal
import sys

from config_manager import ConfigManager
from enums.config_paths import ConfigPaths
from mqtt_handler import MQTTHandler
from controllers import PIControllerPump

# Logger configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


def main() -> None:
    # Configuration manager
    cfg_mngr = ConfigManager()
    cfg_mngr.load_config(file_path="config.yml")
    # MQTT topics handler
    mqtt_handler = MQTTHandler()
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_FIR,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_FIR.value))
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_FIR,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_FIR.value))
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_TIC,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_TIC.value))
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_TIC,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_TIC.value))
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_SP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_SP.value))
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_SP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_SP.value))
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_MANUAL,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_MANUAL.value))
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_MANUAL,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_MANUAL.value))
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_MANUAL_OP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_MANUAL_OP.value))
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_MANUAL_OP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_MANUAL_OP.value))
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_OP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_OP.value))
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_OP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_OP.value))
    # Closure for container interrumptions
    def signal_handler(sig, frame):
        logging.info("Stopping controllers and MD operations")
        mqtt_handler.disconnect()
        logging.info("Disconnected from MQTT Broker")
        sys.exit(0)
    signal.signal(signal.SIGTERM, signal_handler)
    # Configure PI Controllers
    p1_controller = PIControllerPump(id="Pump 1 PI",params=cfg_mngr.get_value(ConfigPaths.P1_PI_CONTROL_SECTION.value))
    p2_controller = PIControllerPump(id="Pump 2 PI",params=cfg_mngr.get_value(ConfigPaths.P2_PI_CONTROL_SECTION.value))
    mqtt_handler.load_controllers(p1_controller,p2_controller)
    # Connect to MQTT Broker and start loop
    mqtt_handler.connect(host="mosquitto",port=1883)


if __name__ == "__main__":
    main()