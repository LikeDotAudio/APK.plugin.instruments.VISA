#!/usr/bin/env python3
# Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
# MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
"""📡 Virtual Test Set — Dual-Domain (RF Cellular + Audio) Emulator.

Simulates a combination test set (cellular base station / transceiver + precision audio analyzer).
Supports:
  1. SCPI TCP Socket Server (IEEE 488.2 + SCPI commands over raw TCP)
  2. MQTT Databus Integration (publishes readings, handles Write -> Read cycles)
  3. Interactive & Background Telemetry generation with physical jitter
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import random
import re
import socket
import sys
import threading
import time
from typing import Dict, Optional, Tuple

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

logger = logging.getLogger("VirtualTestSet")


class VirtualTestSetEngine:
    """Emulates internal RF and Audio signal generators and measurement analyzers."""

    def __init__(self, serial: str = "VTS-0001"):
        self.serial = serial
        self.maker = "APK.audio"
        self.model = "Virtual_TestSet"
        self.firmware = "1.0.0"

        # RF / Cellular State
        self.call_state = "IDLE"  # "IDLE", "CONNECTING", "CONNECTED"
        self.rf_power_target_dbm = -15.0
        self.rf_frequency_hz = 1950000000.0  # 1.95 GHz (Band 1 PCS/UMTS)
        self.target_ber = 0.02
        self.target_evm = 2.1

        # Audio State
        self.audio_freq_hz = 1000.0
        self.audio_level_vrms = 1.0
        self.target_thd_pct = 0.015
        self.target_sinad_db = 76.5

        # Synchronization lock
        self._lock = threading.Lock()

    def execute_scpi(self, raw_cmd: str) -> Optional[str]:
        """Process one SCPI line and return reply string if it is a query, else None."""
        cmd = raw_cmd.strip()
        if not cmd:
            return None

        with self._lock:
            # IEEE 488.2 Common Commands
            if cmd == "*IDN?":
                return f"{self.maker},{self.model},{self.serial},{self.firmware}"
            if cmd == "*OPC":
                return None
            if cmd == "*OPC?":
                return "1"
            if cmd == "*CLS":
                return None
            if cmd == "*RST":
                self.call_state = "IDLE"
                self.rf_power_target_dbm = -15.0
                self.audio_freq_hz = 1000.0
                self.audio_level_vrms = 1.0
                return None
            if cmd == "*WAI":
                return None

            # Cellular / RF Commands
            if cmd in ("CALL:PCON", "CALL:PCONNECTION", "CALL:CONNECT", "CALL:CONN"):
                self.call_state = "CONNECTED"
                return None
            if cmd in ("CALL:END", "CALL:DISCONNECT"):
                self.call_state = "IDLE"
                return None
            if cmd in ("CALL:STAT?", "CALL:STATUS?"):
                return self.call_state

            # RF Power Set/Get
            m_rf_pow = re.match(r"^SOUR(?:CE)?:RF:POW(?:ER)?\s+([+-]?\d+(?:\.\d+)?)$", cmd, re.I)
            if m_rf_pow:
                self.rf_power_target_dbm = float(m_rf_pow.group(1))
                return None
            if re.match(r"^MEAS(?:URE)?:RF:POW(?:ER)?\?$", cmd, re.I):
                noise = random.gauss(0, 0.05)
                val = self.rf_power_target_dbm + noise if self.call_state == "CONNECTED" else -110.0
                return f"{val:.2f}"

            # Bit Error Rate & EVM Queries
            if re.match(r"^MEAS(?:URE)?:BER\?$", cmd, re.I):
                if self.call_state == "CONNECTED":
                    ber = max(0.0, self.target_ber + random.gauss(0, 0.003))
                else:
                    ber = 99.9
                return f"{ber:.4f}"
            if re.match(r"^MEAS(?:URE)?:EVM\?$", cmd, re.I):
                if self.call_state == "CONNECTED":
                    evm = max(0.5, self.target_evm + random.gauss(0, 0.1))
                else:
                    evm = 45.0
                return f"{evm:.2f}"

            # Audio Generator Set/Get
            m_af = re.match(r"^SOUR(?:CE)?:AUD(?:IO)?:FREQ(?:UENCY)?\s+(\d+(?:\.\d+)?)$", cmd, re.I)
            if m_af:
                self.audio_freq_hz = float(m_af.group(1))
                return None
            if re.match(r"^SOUR(?:CE)?:AUD(?:IO)?:FREQ(?:UENCY)?\?$", cmd, re.I):
                return f"{self.audio_freq_hz:.2f}"

            m_al = re.match(r"^SOUR(?:CE)?:AUD(?:IO)?:LEV(?:EL)?\s+(\d+(?:\.\d+)?)$", cmd, re.I)
            if m_al:
                self.audio_level_vrms = float(m_al.group(1))
                return None

            # Audio Measurements
            if re.match(r"^MEAS(?:URE)?:AUD(?:IO)?:LEV(?:EL)?\?$", cmd, re.I):
                v_meas = self.audio_level_vrms * (1.0 + random.gauss(0, 0.002))
                return f"{v_meas:.4f}"
            if re.match(r"^MEAS(?:URE)?:AUD(?:IO)?:THD\?$", cmd, re.I):
                thd = max(0.001, self.target_thd_pct + random.gauss(0, 0.001))
                return f"{thd:.4f}"
            if re.match(r"^MEAS(?:URE)?:(?:AUD(?:IO)|AFAN(?:ALYZER)?):SINA(?:D)?\?$", cmd, re.I):
                sinad = self.target_sinad_db + random.gauss(0, 0.2)
                return f"{sinad:.2f}"

            # Unrecognized command
            return "ERR_COMMAND_NOT_SUPPORTED"

    def current_readings(self) -> Dict[str, str]:
        """Snapshot of all live meter readings."""
        with self._lock:
            rf_pow = f"{(self.rf_power_target_dbm + random.gauss(0, 0.05)):.2f}" if self.call_state == "CONNECTED" else "-110.00"
            ber = f"{max(0.0, self.target_ber + random.gauss(0, 0.003)):.4f}" if self.call_state == "CONNECTED" else "99.9000"
            evm = f"{max(0.5, self.target_evm + random.gauss(0, 0.1)):.2f}" if self.call_state == "CONNECTED" else "45.00"
            v_meas = f"{(self.audio_level_vrms * (1.0 + random.gauss(0, 0.002))):.4f}"
            thd = f"{max(0.001, self.target_thd_pct + random.gauss(0, 0.001)):.4f}"
            sinad = f"{(self.target_sinad_db + random.gauss(0, 0.2)):.2f}"
            return {
                "Get_Call_Status": self.call_state,
                "Get_Rf_Power": rf_pow,
                "Get_Ber": ber,
                "Get_Evm": evm,
                "Get_Audio_Freq": f"{self.audio_freq_hz:.2f}",
                "Get_Audio_Level": v_meas,
                "Get_Thd": thd,
                "Get_Sinad": sinad,
            }


class ScpiSocketServer(threading.Thread):
    """Raw TCP socket SCPI listener (standard port 5025 or allocated port 16303)."""

    def __init__(self, engine: VirtualTestSetEngine, host: str = "0.0.0.0", port: int = 16303):
        super().__init__(daemon=True, name="ScpiSocketServer")
        self.engine = engine
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.running = False

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            logger.info("SCPI socket server listening on %s:%d", self.host, self.port)
            while self.running:
                client_sock, client_addr = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True,
                ).start()
        except Exception as exc:
            if self.running:
                logger.error("SCPI Server socket failed: %s", exc)
        finally:
            self.close()

    def _handle_client(self, client_sock: socket.socket, addr: Tuple[str, int]):
        logger.info("SCPI client connected from %s:%d", addr[0], addr[1])
        buff = ""
        try:
            while self.running:
                data = client_sock.recv(4096)
                if not data:
                    break
                buff += data.decode("latin-1", errors="replace")
                while "\n" in buff:
                    line, buff = buff.split("\n", 1)
                    line = line.strip("\r")
                    reply = self.engine.execute_scpi(line)
                    if reply is not None:
                        client_sock.sendall((reply + "\n").encode("latin-1"))
        except Exception as exc:
            logger.debug("Client socket closed: %s", exc)
        finally:
            client_sock.close()

    def close(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass


class MqttBusBridge(threading.Thread):
    """Bridges the virtual test set to the APK.audio MQTT databus."""

    def __init__(
        self,
        engine: VirtualTestSetEngine,
        broker_host: str = "127.0.0.1",
        broker_port: int = 1883,
        dev_name: str = "Dev0",
        publish_interval: float = 1.0,
    ):
        super().__init__(daemon=True, name="MqttBusBridge")
        self.engine = engine
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.dev_name = dev_name
        self.publish_interval = publish_interval
        self.base_topic = f"APK.audio/System/Protocols/visa/Device/TestSet/Virtual_TestSet/{self.dev_name}"
        self.running = False
        self.client: Optional[mqtt.Client] = None

    def run(self):
        if not mqtt:
            logger.warning("paho-mqtt not available; bus integration disabled.")
            return

        client_id = f"VirtualTestSet_{self.dev_name}_{random.randint(1000, 9999)}"
        if hasattr(mqtt, "CallbackAPIVersion"):
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)
        else:
            self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            self.running = True

            # Publish Device Identity
            self.client.publish(f"{self.base_topic}/model", "Virtual_TestSet", retain=True)
            self.client.publish(f"{self.base_topic}/vendor", "APK.audio", retain=True)
            self.client.publish(f"{self.base_topic}/serial", self.engine.serial, retain=True)
            self.client.publish(f"{self.base_topic}/status", "online", retain=True)

            logger.info("Connected to MQTT broker at %s:%d (topic: %s)", self.broker_host, self.broker_port, self.base_topic)

            while self.running:
                readings = self.engine.current_readings()
                for cmd, val in readings.items():
                    self.client.publish(f"{self.base_topic}/Reading/{cmd}", str(val))
                time.sleep(self.publish_interval)

        except Exception as exc:
            logger.error("MQTT connection error: %s", exc)
        finally:
            self.close()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            write_topic = f"{self.base_topic}/Write"
            client.subscribe(write_topic)
            logger.info("Subscribed to command write topic: %s", write_topic)

    def _on_message(self, client, userdata, msg):
        try:
            raw_payload = msg.payload.decode("utf-8", errors="replace")
            # Might be JSON payload: {"command": "MEAS:BER?"} or bare string
            cmd_str = raw_payload.strip()
            if cmd_str.startswith("{"):
                try:
                    obj = json.loads(cmd_str)
                    cmd_str = obj.get("command") or obj.get("scpi") or cmd_str
                except Exception:
                    pass
            reply = self.engine.execute_scpi(cmd_str)
            if reply is not None:
                client.publish(f"{self.base_topic}/Read", reply)
        except Exception as exc:
            logger.error("Error processing bus message: %s", exc)

    def close(self):
        self.running = False
        if self.client:
            try:
                self.client.publish(f"{self.base_topic}/status", "offline", retain=True)
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass


def run_self_test():
    """Unit self-test verifying SCPI engine responses."""
    print("Testing VirtualTestSetEngine...")
    engine = VirtualTestSetEngine(serial="VTS-TEST")

    # Identity
    idn = engine.execute_scpi("*IDN?")
    assert "APK.audio,Virtual_TestSet,VTS-TEST" in idn, f"Bad IDN: {idn}"

    # Reset
    assert engine.execute_scpi("*RST") is None

    # Call Connect
    assert engine.execute_scpi("CALL:STAT?") == "IDLE"
    assert engine.execute_scpi("CALL:PCON") is None
    assert engine.execute_scpi("CALL:STAT?") == "CONNECTED"

    # RF Power & BER
    rf_pow = float(engine.execute_scpi("MEAS:RF:POW?"))
    assert -16.0 <= rf_pow <= -14.0, f"RF Power out of range: {rf_pow}"
    ber = float(engine.execute_scpi("MEAS:BER?"))
    assert 0.0 <= ber <= 0.1, f"BER out of range: {ber}"

    # Audio Generator & Measurements
    assert engine.execute_scpi("SOUR:AUD:FREQ 2500") is None
    assert float(engine.execute_scpi("SOUR:AUD:FREQ?")) == 2500.0
    thd = float(engine.execute_scpi("MEAS:AUD:THD?"))
    assert 0.005 <= thd <= 0.03, f"THD out of range: {thd}"
    sinad = float(engine.execute_scpi("MEAS:AFAN:SINA?"))
    assert 70.0 <= sinad <= 85.0, f"SINAD out of range: {sinad}"

    # Disconnect
    assert engine.execute_scpi("CALL:END") is None
    assert engine.execute_scpi("CALL:STAT?") == "IDLE"

    print("✅ All VirtualTestSetEngine self-tests passed successfully!")


def main():
    parser = argparse.ArgumentParser(description="Virtual Test Set Emulator (RF + Audio)")
    parser.add_argument("--scpi-port", type=int, default=16303, help="SCPI TCP socket server port (default: 16303)")
    parser.add_argument("--scpi-host", type=str, default="0.0.0.0", help="SCPI TCP bind host (default: 0.0.0.0)")
    parser.add_argument("--mqtt-host", type=str, default="127.0.0.1", help="MQTT broker host (default: 127.0.0.1)")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="MQTT broker port (default: 1883)")
    parser.add_argument("--dev-name", type=str, default="Dev0", help="Device name on bus (default: Dev0)")
    parser.add_argument("--serial", type=str, default="VTS-0001", help="Serial number string")
    parser.add_argument("--no-mqtt", action="store_true", help="Disable MQTT bridge")
    parser.add_argument("--no-scpi", action="store_true", help="Disable SCPI socket server")
    parser.add_argument("--test", action="store_true", help="Run self-test and exit")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    if args.test:
        run_self_test()
        sys.exit(0)

    engine = VirtualTestSetEngine(serial=args.serial)
    threads = []

    if not args.no_scpi:
        scpi_server = ScpiSocketServer(engine, host=args.scpi_host, port=args.scpi_port)
        scpi_server.start()
        threads.append(scpi_server)

    if not args.no_mqtt:
        mqtt_bridge = MqttBusBridge(
            engine,
            broker_host=args.mqtt_host,
            broker_port=args.mqtt_port,
            dev_name=args.dev_name,
        )
        mqtt_bridge.start()
        threads.append(mqtt_bridge)

    logger.info("Virtual Test Set running. Press Ctrl+C to terminate.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Virtual Test Set...")
        for t in threads:
            t.close()


if __name__ == "__main__":
    main()
