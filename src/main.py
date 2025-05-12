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


def run(mqtt_handler: MQTTHandler, PI_P1: PIControllerPump, PI_P2: PIControllerPump) -> None:
    # TODO WIP
    while True:
        P1_FIR = float(mqtt_handler.get_topic_value_byconfigpath(ConfigPaths.MQTT_TOPIC_P1_FIR))
        P2_FIR = float(mqtt_handler.get_topic_value_byconfigpath(ConfigPaths.MQTT_TOPIC_P2_FIR))
        p1_compute = PI_P1.compute(y=P1_FIR)
        p2_compute = PI_P2.compute(y=P2_FIR)
        if p1_compute:
            if mqtt_handler.publish_topic_byconfigpath(ConfigPaths.MQTT_TOPIC_P1_OP, PI_P1.get_op()):
                PI_P1.set_last_u(u=PI_P1.get_op())
        if p2_compute:
            if mqtt_handler.publish_topic_byconfigpath(ConfigPaths.MQTT_TOPIC_P2_OP, PI_P2.get_op()):
                PI_P2.set_last_u(u=PI_P2.get_op())

        logging.debug(f"Controllers Pumps OP: {PI_P1.get_op():.2f} | {PI_P2.get_op():.2f}")
        logging.debug(f"Controllers Pumps Triggers: {p1_compute} | {p2_compute}")
        logging.debug(f"Controllers Pumps Modes: {PI_P1.is_manual()} | {PI_P2.is_manual()}")
        
        time.sleep(2)


def main() -> None:
    # Configuration manager
    cfg_mngr = ConfigManager()
    cfg_mngr.load_config(file_path="config.yml")
    # MQTT topics handler
    mqtt_handler = MQTTHandler()
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_FIR,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_FIR.value), 0.0)
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_FIR,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_FIR.value), 0.0)
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_TIC,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_TIC.value), 0.0)
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_TIC,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_TIC.value), 0.0)
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_SP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_SP.value), 0.0)
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_SP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_SP.value), 0.0)
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_MANUAL,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_MANUAL.value), True)
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_MANUAL,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_MANUAL.value), True)
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_MANUAL_OP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_MANUAL_OP.value), 20.0)
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_MANUAL_OP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_MANUAL_OP.value), 20.0)
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P1_OP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P1_OP.value), 0.0, False)
    mqtt_handler.load_topic(ConfigPaths.MQTT_TOPIC_P2_OP,cfg_mngr.get_value(ConfigPaths.MQTT_TOPIC_P2_OP.value), 0.0, False)
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
    # Run main process
    run(mqtt_handler,p1_controller,p2_controller)


if __name__ == "__main__":
    main()