"""MQTT publisher for decoded packets.

Requires: pip install paho-mqtt
Topics  : <prefix>/<Model-Name>/<device_id>
Payload : JSON (the full packet raw dict)
"""

from __future__ import annotations

import json
import logging
import time
import threading
from dataclasses import dataclass

from .packet import DecodedPacket

logger = logging.getLogger(__name__)


@dataclass
class MqttConfig:
    host: str
    port: int = 1883
    username: str | None = None
    password: str | None = None
    topic_prefix: str = "rtl_433"
    keepalive: int = 60
    qos: int = 0
    retain: bool = False


class MqttPublisher:
    def __init__(self, config: MqttConfig) -> None:
        try:
            import paho.mqtt.client as mqtt  # type: ignore
        except ImportError:
            raise ImportError("paho-mqtt is required for MQTT support:\n  pip install paho-mqtt")

        self._cfg = config
        self._backoff = 1.0
        self._connected = False

        self._client = mqtt.Client()
        if config.username:
            self._client.username_pw_set(config.username, config.password)
        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    def connect(self) -> None:
        self._client.connect(self._cfg.host, self._cfg.port, self._cfg.keepalive)
        self._client.loop_start()

    def publish(self, pkt: DecodedPacket) -> None:
        if not self._connected:
            logger.debug("MQTT not connected  dropping packet")
            return
        model_slug = pkt.model.replace(" ", "_")
        device_id  = pkt.raw.get("id", "unknown")
        topic      = f"{self._cfg.topic_prefix}/{model_slug}/{device_id}"
        payload    = json.dumps(pkt.raw, default=str)
        self._client.publish(topic, payload, qos=self._cfg.qos, retain=self._cfg.retain)

    def close(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    # ------------------------------------------------------------------
    # paho callbacks
    # ------------------------------------------------------------------

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self._connected = True
            self._backoff   = 1.0
            logger.info("MQTT connected to %s:%d", self._cfg.host, self._cfg.port)
        else:
            logger.error("MQTT connect failed rc=%d", rc)

    def _on_disconnect(self, client, userdata, rc) -> None:
        self._connected = False
        if rc != 0:
            logger.warning("MQTT unexpected disconnect (rc=%d)  reconnecting in %.0fs", rc, self._backoff)
            delay = self._backoff
            self._backoff = min(self._backoff * 2, 60.0)

            def _reconnect():
                time.sleep(delay)
                try:
                    client.reconnect()
                except Exception as exc:
                    logger.error("MQTT reconnect failed: %s", exc)

            threading.Thread(target=_reconnect, daemon=True).start()
