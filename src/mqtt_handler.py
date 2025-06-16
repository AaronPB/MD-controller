import logging
import paho.mqtt.client as mqtt

from typing import Any
from enums.config_paths import ConfigPaths
from controllers import PIControllerPump


class MQTTHandler:
    def __init__(self):
        self.client = mqtt.Client()
        self.pump1_pi: PIControllerPump
        self.pump2_pi: PIControllerPump
        self.pump1_op_publish: str
        self.pump2_op_publish: str
        self.subscribe_topics: dict[str, Any] = {}
        self.publish_topics: dict[str, Any] = {}
    
    # MQTT client handlers
    def connect(self, host: str, port: int) -> None:
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        try:
            self.client.connect(host, port)
        except Exception as e:
            logging.critical(f"Could not connect to the MQTT Broker: {e}")
            return
        self.client.loop_forever()
    
    def disconnect(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
        logging.info("Disconnected from MQTT Broker")
    
    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: dict[str, Any], rc: int) -> None:
        if rc == 0:
            logging.info("Correctly connected to MQTT broker.")
            topic_list = [client.subscribe(topic) for topic in self.subscribe_topics]
            logging.info(f"Successfully subscribed into {len(topic_list)} mqtt topics")
        else:
            logging.error(f"Connection error, code {rc}")

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        try:
            payload = msg.payload.decode('utf-8')

            logging.debug(f"Raw MQTT topic received: {msg.topic} with payload: {payload}")

            handler = self.subscribe_topics.get(msg.topic)

            if handler:
                handler(payload)
                logging.info(f"{msg.topic} updated with value: {payload}")

        except Exception as e:
            logging.error(f"Error trying to process mqtt message from {msg.topic}: {e}")
    
    # MQTT topics
    def load_topic(self, config_path: ConfigPaths, topic_path: str) -> None:
        # TODO Manually set default values??
        # Topic subscriptions
        if config_path == ConfigPaths.MQTT_TOPIC_P1_FIR:
            self.subscribe_topics[topic_path] = lambda payload: self._controller_compute(self.pump1_op_publish, self.pump1_pi, float(payload))
        if config_path == ConfigPaths.MQTT_TOPIC_P2_FIR:
            self.subscribe_topics[topic_path] = lambda payload: self._controller_compute(self.pump2_op_publish, self.pump2_pi, float(payload))
        if config_path == ConfigPaths.MQTT_TOPIC_P1_MANUAL:
            self.subscribe_topics[topic_path] = lambda payload: self.pump1_pi.set_manual(bool(int(payload)))
        if config_path == ConfigPaths.MQTT_TOPIC_P2_MANUAL:
            self.subscribe_topics[topic_path] = lambda payload: self.pump2_pi.set_manual(bool(int(payload)))
        if config_path == ConfigPaths.MQTT_TOPIC_P1_MANUAL_OP:
            self.subscribe_topics[topic_path] = lambda payload: self.pump1_pi.set_manual_op(float(payload))
        if config_path == ConfigPaths.MQTT_TOPIC_P2_MANUAL_OP:
            self.subscribe_topics[topic_path] = lambda payload: self.pump2_pi.set_manual_op(float(payload))
        if config_path == ConfigPaths.MQTT_TOPIC_P1_SP:
            self.subscribe_topics[topic_path] = lambda payload: self.pump1_pi.set_sp(float(payload))
        if config_path == ConfigPaths.MQTT_TOPIC_P2_SP:
            self.subscribe_topics[topic_path] = lambda payload: self.pump2_pi.set_sp(float(payload))
        # Topic publishers
        if config_path == ConfigPaths.MQTT_TOPIC_P1_OP:
            self.publish_topics[topic_path] = 0.0
            self.pump1_op_publish = topic_path
        if config_path == ConfigPaths.MQTT_TOPIC_P2_OP:
            self.publish_topics[topic_path] = 0.0
            self.pump2_op_publish = topic_path
    
    # MQTT load controllers
    def load_controllers(self, pump1_pi: PIControllerPump, pump2_pi: PIControllerPump) -> None:
        self.pump1_pi = pump1_pi
        self.pump2_pi = pump2_pi

    # MQTT publish topic
    def publish_topic(self, topic_path: str, value: Any) -> bool:
        if self.publish_topics.get(topic_path) is None:
            logging.warning(f"Could not find topic with following path {topic_path}")
            return False
        # message = json.dumps({"value": value})
        result = self.client.publish(topic_path, value)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            self.publish_topics[topic_path] = value
            logging.info(f"Published value {value} to {topic_path}")
        else:
            logging.warning(f"Error publishing mqtt message, code: {result.rc}")
            return False
        return True
    
    # Internal topic processes
    def _controller_compute(self, publish_topic_path: str, controller: PIControllerPump, y: float) -> None:
        published = False
        update = controller.compute(y)
        if update:
            published = self.publish_topic(publish_topic_path, controller.get_op())
        if published:
            controller.set_last_u(controller.get_op())
