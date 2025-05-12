from enum import Enum


class ConfigPaths(Enum):
    FILE_VERSION = "version"

    # TODO General settings? (sample time)

    MQTT_TOPIC_P1_FIR = "mqtt_topics.pump_1_flow_rate"
    MQTT_TOPIC_P1_TIC = "mqtt_topics.pump_1_temperature"
    MQTT_TOPIC_P2_FIR = "mqtt_topics.pump_2_flow_rate"
    MQTT_TOPIC_P2_TIC = "mqtt_topics.pump_2_temperature"
    MQTT_TOPIC_P1_SP = "mqtt_topics.pump_1_sp"
    MQTT_TOPIC_P2_SP = "mqtt_topics.pump_2_sp"
    MQTT_TOPIC_P1_OP = "mqtt_topics.pump_1_op"
    MQTT_TOPIC_P2_OP = "mqtt_topics.pump_2_op"
    MQTT_TOPIC_V3_OP = "mqtt_topics.valve_31_op"

    P1_PI_CONTROL_SECTION = "control_params.pump_1_pi_controller"
    P2_PI_CONTROL_SECTION = "control_params.pump_2_pi_controller"
