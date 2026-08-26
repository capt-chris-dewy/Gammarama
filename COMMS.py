import serial
import serial.tools.list_ports
import time
import sys

#A class outlining all PLC command functions to be called by handler functions in the MAIN_SERVER file
class PLC():

    def __init__(self, name):
        self.name = name
        self.serialObj = -1;
    
    """INITIALIZATION STEPS / FUNCTIONS"""
    
    def initializeSerialComms(self, com_selected):
        #initialize PLC Serial Object for communications
        try:
            ser = serial.Serial(port=com_selected, baudrate=9600, timeout=1)
            self.serialObj = ser
            #verify proper response from PLC to generic command (establish two-way comms is working)
            response1 = self.send_command("RD iCURRENT_POSITION")
            position1 = self.isolateRead(response1)
            position1_asint = int(position1)
        
            if position1_asint >= 0 and position1_asint <= 12:
                return 1 #system is operational, allow full operation
            else:
                return 2
                
        except serial.SerialException:
            return 0 
    
    def initializeMotor(self):
        print("Attempting initialization")
        cmd = "ST iHMI_INITIALIZE_PB 1"
        response1 = self.send_command(cmd)
        trimmed1 = self.trim_response(response1)
        return trimmed1
    
    """BASIC MOVEMENT FUNCTIONS"""
    
    def indexPos(self):
        cmd = "ST iHMI_INDEX_PB 1"
        response1 = self.send_command(cmd)
        trimmed1 = self.trim_response(response1)
        return trimmed1
        
    def goToPosition(self, new_pos):
        cmd1 = "ST iHMI_NEW_POSITON " + str(new_pos)
        response1 = self.send_command(cmd1)
        trimmed1 = self.trim_response(response1)
        
        cmd2 = "ST iHMI_NEW_POSITION_PB 1"
        response2 = self.send_command(cmd2)
        trimmed2 = self.trim_response(response2)
        
        return trimmed1
    
    """SENSOR READING FUNCTIONS"""
    
    def readPosition(self):
        cmd = "RD iCURRENT_POSITION"
        response1 = self.send_command(cmd)
        current_pos = self.isolateRead(response1)
        current_pos_as_int = int(current_pos)
        return current_pos_as_int
    
    """MISCELLANEOUS -- CUSTOM COMMAND / COMMAND OVERRIDE"""
    
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
    
    """READ AND WRITE COMMAND UTILITY FUNCTIONS"""
     
    def send_command(self, command):
        if command[-2:] == "\r":
            pass
        else:
           command_cr = command + '\r'
        
        if self.serialObj == -1:
            print("Error: serial connection was never initialized prior to \"send_command\", please review Python errors in console")
        command_ascii = command_cr.encode('ascii')
        self.serialObj.write(command_ascii)
        response = self.serialObj.read_until(b'\r')
        return response
         
    def trim_response(self, response):
        response_nix_cr = response.decode('ascii').strip() #decode to ascii, get rid of '\r' carriage return / "cr"
        return response_nix_cr
    
    def isolateRead(self, response):
        trimmed_response = self.trim_response(response)
        starting_index = trimmed_response.rfind(' ') + 1 #find the last index containing a space to isolate returned value from read command, add 1
        return trimmed_response[starting_index:] 
        

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


