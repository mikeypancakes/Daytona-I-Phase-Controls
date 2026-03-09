import serial
import serial.tools.list_ports
import time

class LedStrip:

    def __init__(self):
        self.com_port = None
        self.baud_rate = None
        self.num_leds = None
        self.polling_rate = None
        self.serialConnection = None

        self.state_dict = {
            'init' : 'i',
            'ready' : 'r',
            'worklist' : 'w',
            'error' : 'e',
            'off' : 'o',
            'update' : 'u'
        }

    def connect(self, com_port, baud_rate):
        try:
            self.serialConnection = serial.Serial(port=com_port, baudrate=int(baud_rate), timeout=1)
            time.sleep(2)  # wait for microcontroller reset
            self.set_LED_state("init")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to {com_port}: {e}")
            self.serialConnection = None

    def find_ports(self):

        found_ports = []

        CH340_VID_PID = "VID:PID=1A86:7523"

        ports = serial.tools.list_ports.comports()
        for port in ports:
            # Check if the hardware ID string contains the CH340's VID and PID
            if CH340_VID_PID in port.hwid.upper():
                print(f"Found CH340 device at: {port.device}")
                found_ports.append(port.device)

        if len(found_ports) > 0:
            return found_ports
        else:
            print(f"No CH340 device found with {CH340_VID_PID}.")
            return None
        
    def set_LED_state(self, input_state, value = None):
        if command := self.state_dict.get(input_state):
            if self.serialConnection:
                if value:
                    payload = f"<{command}:{value}>"
                else:
                    payload = f"<{command}>"
                try:
                    self.serialConnection.write(payload.encode())
                except Exception as e:
                    print(f"Cannot deliver payload: {payload} ({e})")
        else:
            print(f"Invalid command: {input_state}")
    