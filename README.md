# Industrial_RealTime_Data_Acquisition_IIOT
Modbus to MQTT Data Acquisition and Publishing


## Modbus to MQTT Data Acquisition Script

This Python script reads data from Modbus energy meters and publishes it to an MQTT broker. 

**Features:**

* Connects to Modbus energy meters via a serial port.
* Reads various registers including current, voltage, and energy readings.
* Decodes registers and converts them to appropriate units.
* Prepares data for further processing or publishing to an MQTT broker.
* Includes error handling for Modbus communication.

**Installation:**

1. Clone the repository.
2. Install required libraries:
   ```bash
   pip install paho-mqtt pymodbus
   ```

**Usage:**

1. Modify the script with your specific Modbus configuration (port, baud rate, slave IDs, register addresses).
2. Replace "your_topic" in the commented-out MQTT publish line with your desired topic.
3. Run the script:
   ```bash
   python main.py
   ```

**Data Output:**

The script prints the read data to the console in a formatted way.

**Dependencies:**

* Python 3 (tested with 3.x)
* paho-mqtt library
* pymodbus library

**License:**

GNU

**Contributing:**

 encouraging contributions to improve this script. Please create a pull request with your changes and a clear description.

**Further Development:**
* Develop a user interface for configuration and monitoring.
* Integrate with cloud-based platforms for data storage and analytics.

