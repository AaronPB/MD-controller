import logging
import paho.mqtt.client as mqtt

from typing import Any
from enums.config_paths import ConfigPaths


class MQTTHandler:
    def __init__(self):
        self.client = mqtt.Client()
        self.subscribe_topics: dict[str, Any] = {}
        self.publish_topics: dict[str, Any] = {}
        self.subscribe_topic_paths: dict[ConfigPaths, str] = {}
        self.publish_topic_paths: dict[ConfigPaths, str] = {}
    
    # MQTT client handlers
    def connect(self, host: str, port: int) -> None:
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        try:
            self.client.connect(host, port)
        except Exception as e:
            logging.critical(f"Could not connect to the MQTT Broker: {e}")
            return
        self.client.loop_start()
    
    def disconnect(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
        logging.info("Disconnected from MQTT Broker")
    
    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: dict[str, Any], rc: int) -> None:
        if rc == 0:
            logging.info("Correctly connected to MQTT broker.")
            # Configure topic connections
            # TODO Is this better?? -> client.subscribe_callback()
            topic_list = [client.subscribe(topic) for topic in self.subscribe_topics]
            logging.info(f"Successfully subscribed into {len(topic_list)} mqtt topics")
        else:
            logging.error(f"Connection error, code {rc}")

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        try:
            payload = msg.payload.decode('utf-8')
            # data: dict = json.loads(payload)
            # logging.debug(payload)
            logging.debug(f"Raw MQTT topic received: {msg.topic} with payload: {payload}")
            # value = float(data.get("value", None))
            # value = float(data)
            # topic_key = self.subscribe_topics.get(msg.topic)
            # logging.debug(f"Received data from topic key: {topic_key}, with value: {value}")

            if self.subscribe_topics.get(msg.topic) is not None:
                self.subscribe_topics[msg.topic] = payload
                logging.info(f"{msg.topic} updated with value: {payload}")
        except Exception as e:
            logging.error(f"Error trying to process mqtt message from {msg.topic}: {e}")
    
    # MQTT topics
    def load_topic(self, config_path: ConfigPaths, topic_path: str, default_value: Any, subscribe: bool = True) -> None:
        if subscribe:
            self.subscribe_topics[topic_path] = default_value
            self.subscribe_topic_paths[config_path] = topic_path
            return
        self.publish_topics[topic_path] = default_value
        self.publish_topic_paths[config_path] = topic_path

    # MQTT publish topic
    def publish_topic_bytopicpath(self, topic_path: str, value: Any) -> bool:
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

    def publish_topic_byconfigpath(self, config_path: ConfigPaths, value: Any) -> bool:
        topic_path = self.publish_topic_paths.get(config_path)
        if topic_path is None:
            logging.warning(f"Could not find topic path, using config path {config_path}")
            return False
        return self.publish_topic_bytopicpath(topic_path, value)
    
    # MQTT subscribe topic
    # def get_topic_path(self, config_path: ConfigPaths) -> str:
    #     return self.s

    def get_topic_value_bytopicpath(self, topic_path: str) -> Any:
        return self.subscribe_topics.get(topic_path)

    def get_topic_value_byconfigpath(self, config_path: ConfigPaths) -> Any:
        return self.get_topic_value_bytopicpath(self.subscribe_topic_paths.get(config_path))