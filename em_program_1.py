import paho.mqtt.client as mqtt
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from datetime import datetime
import threading
import time
import json
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Modbus and MQTT Configurations
MODBUS_HOST = "10.204.88.8"
MODBUS_PORT = 502
MQTT_BROKER = "10.204.155.11"
MQTT_PORT = 1883
MQTT_USERNAME = "avl_mqtt_client"
MQTT_PASSWORD = "emqx@avl123!@#"
METERS = ["1193", "1194"]  # Energy meter IDs
UNIT_IDS = [3, 4]  # Unit IDs for each meter

# Initialize Modbus client
modbus_client = ModbusTcpClient(host=MODBUS_HOST, port=MODBUS_PORT)

# Initialize MQTT client
mqtt_client = mqtt.Client("energy_meter_client")
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# Utility function to decode registers
def decode_registers(registers, indices, factor=1):
    decoded_data = {}
    for key, index in indices.items():
        try:
            decoder = BinaryPayloadDecoder.fromRegisters(
                [registers[index]], byteorder=Endian.Big, wordorder=Endian.Little
            )
            decoded_data[key] = decoder.decode_16bit_uint() / factor
        except Exception as e:
            logging.error(f"Error decoding {key}: {e}")
    return decoded_data

# Function to read and process Modbus data
def read_meter_data(meter_id, unit_id):
    try:
        response = modbus_client.read_holding_registers(1099, 120, unit=unit_id)
        if not response.isError():
            data_indices = {
                "current_phase1": 0,
                "current_phase2": 1,
                "current_phase3": 2,
                "voltage_ph1_ph2": 19,
                "voltage_ph2_ph3": 20,
                "voltage_ph3_ph1": 21,
                "frequency": 79,
                "active_power": 42,
                "power_factor": 62,
            }
            decoded_data = decode_registers(response.registers, data_indices, factor=100)
            decoded_data["timestamp"] = str(datetime.now())
            logging.info(f"Meter {meter_id}: {json.dumps(decoded_data)}")
            mqtt_client.publish(meter_id, json.dumps(decoded_data))
        else:
            logging.warning(f"Failed to read data for meter {meter_id}, unit {unit_id}")
    except Exception as e:
        logging.error(f"Error reading meter {meter_id}: {e}")

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT broker")
        for meter in METERS:
            client.subscribe(meter)
    else:
        logging.error(f"MQTT connection failed with code {rc}")

def on_publish(client, userdata, mid):
    logging.info(f"Data published, mid: {mid}")

# Thread to poll Modbus data
def modbus_polling_thread():
    while True:
        for meter, unit_id in zip(METERS, UNIT_IDS):
            read_meter_data(meter, unit_id)
            time.sleep(0.5)

# Main function
if __name__ == "__main__":
    try:
        modbus_client.connect()
        mqtt_client.on_connect = on_connect
        mqtt_client.on_publish = on_publish
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

        # Start threads
        modbus_thread = threading.Thread(target=modbus_polling_thread, daemon=True)
        mqtt_thread = threading.Thread(target=mqtt_client.loop_forever, daemon=True)
        modbus_thread.start()
        mqtt_thread.start()

        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        modbus_client.close()
        mqtt_client.disconnect()
