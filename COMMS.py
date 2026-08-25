import serial
import serial.tools.list_ports
import time
import sys

#A class outlining all PLC command functions to be called by handler functions in the MAIN_SERVER file
class PLC():

    def __init__(self, name):
        self.name = name
        self.serialObj = -1;
    
    def initializeSerialComms(self, com_selected):
        try:
            ser = serial.Serial(port=com_selected, baudrate=9600, timeout=1)
            self.serialObj = ser
            return "Serial connection successfully established!"
        except serial.SerialException:
            return "SerialException: Device not found"
    
    def initializeMotor(self):
        print("Initializing to Position 1")
        #pseudo-code
        #check current position, verify that it is not corrupt
        #response1 = send_command("RD iCURRENT_POSITION")
        #position1 = trim_response(response_1)
        #if position1 >= 0 and position1 <= 12:
        #   print("Valid position, initializing motor")
        #   response2 = send_command("ST iHMI_INITIALIZE_PB 1")
        #   if response2 == "ST iHMI_INITIALIZE_PB 1":
        #       print("Initialize command sent")
        #   else:
        #       print("Invalid initialization response from PLC")
        #else:
        #   print("Invalid position at start-up in PLC code, pos = " + str(position1))
     
    def command_override(self, user_input):
        prefix = user_input[0:2]
        if prefix == "ST" or prefix == "RD":
            print("Command has valid ST/RD (write/read) prefix, attempting send")
            raw_response = self.send_command(user_input)
            trimmed_response = self.trim_response(raw_response)
            return trimmed_response
        else:
            print("Invalid prefix -- command must start with 'ST' or 'RD' (write/read)")
            return "Error: no response due to invalid command"
         
     
    def send_command(self, command):
        if command[-2:] == "\r":
            pass
        else:
           command_cr = command + '\r'
            
        command_ascii = command_cr.encode('ascii')
        serial_connection.write(command_ascii)
        response = serial_connection.read_until(b'\r')
        return response
         
    def trim_response(self, response):
        return response.decode('ascii').strip()

    #function for identifying + listing all comm ports (appears to work for windows)
    #intended for use in a dropdown menu in main web-based GUI

    def list_COM_ports(self):
        port_objects = serial.tools.list_ports.comports()
        com_array = []
        for port_obj in port_objects:
            com_entry = []
            com_entry.append(port_obj.device)
            com_entry.append(port_obj.description)
            com_array.append(com_entry)
        
        return com_array


