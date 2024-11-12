import paho.mqtt.publish as publish
import json
from time import sleep, time
from datetime import datetime
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder


# Initialize Modbus client
client = ModbusClient(method='rtu', port='/dev/ttyUSB0', stopbits=1, parity='N', bytesize=8, baudrate=9600, timeout=0.5)
connection = client.connect()

# Energy Meter IDs
EM_IDS = {
    1: "118", 2: "119", 3: "120", 4: "121", 5: "122", 6: "123", 7: "124", 8: "125", 
    9: "126", 10: "127", 11: "128", 12: "129", 13: "130", 15: "132", 16: "133", 
    17: "134", 18: "135", 19: "136"
}

# Function to read and decode Modbus registers
def read_and_decode_registers(address, count, unit):
    try:
        response = client.read_holding_registers(address, count, unit=unit)
        return response.registers if response.isError() is False else None
    except Exception as e:
        print(f"Error reading from unit {unit}: {e}")
        return None

# Function to decode registers into float values
def decode_registers(registers, byteorder=Endian.Big, wordorder=Endian.Little):
    decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=byteorder, wordorder=wordorder)
    return decoder.decode_32bit_float()

# Main loop for processing the data
if connection:
    print("Connected to Modbus client")
    scan_count = 0
    while True:
        now = str(datetime.now())

        for unit_id, EM in EM_IDS.items():
            scan_count += 1
            print(f"Reading Energy Meter {EM} ----------------------------------------------------")

            # Read various registers (adjust address and count based on actual configuration)
            # Current readings
            current_registers = read_and_decode_registers(2999, 6, unit_id)
            if current_registers:
                current_ph1 = decode_registers(current_registers[:2])
                current_ph2 = decode_registers(current_registers[2:4])
                current_ph3 = decode_registers(current_registers[4:6])
                
                # Voltage readings
                voltage_registers = read_and_decode_registers(21299, 4, unit_id)
                if voltage_registers:
                    voltage_ph1_ph2 = decode_registers(voltage_registers[:2])
                    voltage_ph2_ph3 = decode_registers(voltage_registers[2:4])
                    
                    # Energy readings
                    energy_registers = read_and_decode_registers(2697, 6, unit_id)
                    if energy_registers:
                        total_import_energy = decode_registers(energy_registers[:2])
                        total_export_energy = decode_registers(energy_registers[2:4])
                        total_energy = decode_registers(energy_registers[4:6])

                        # Power Factor
                        power_factor_registers = read_and_decode_registers(3189, 2, unit_id)
                        if power_factor_registers:
                            power_factor = decode_registers(power_factor_registers)

                            # Print results
                            print(f"Time                     :------> {now}")
                            print(f"Current Ph1 (A)          :------> {current_ph1:.2f}")
                            print(f"Current Ph2 (A)          :------> {current_ph2:.2f}")
                            print(f"Current Ph3 (A)          :------> {current_ph3:.2f}")
                            print(f"Voltage Ph1-Ph2 (V)      :------> {voltage_ph1_ph2:.2f}")
                            print(f"Voltage Ph2-Ph3 (V)      :------> {voltage_ph2_ph3:.2f}")
                            print(f"Total Import Energy (KWH):------> {total_import_energy:.2f}")
                            print(f"Total Export Energy (KWH):------> {total_export_energy:.2f}")
                            print(f"Total Energy (KWH)       :------> {total_energy:.2f}")
                            print(f"Power Factor             :------> {power_factor:.2f}")
                            
                            # Prepare data for MQTT or further processing
                            data = {
                                "ID": EM,
                                "NCH1": current_ph1,
                                "NCH2": voltage_ph1_ph2,
                                "NCH3": voltage_ph2_ph3,
                                "NCH4": total_import_energy,
                                "NCH5": total_export_energy,
                                "NCH6": total_energy,
                                "NCH7": power_factor,
                            }
                            
                            # Convert to JSON
                            json_data = json.dumps(data)
                            print(f"Sending data: {json_data}")

                            # Sleep to prevent overwhelming the system
                            sleep(0.001)
            else:
                print(f"Error reading registers for unit {unit_id}")

        # Optional: Publish data to MQTT or handle it as needed
        # publish.single("your_topic", payload=json_data, qos=0, retain=False)
        sleep(0.1)  # Control the frequency of the loop

else:
    print("Failed to connect to Modbus client")
