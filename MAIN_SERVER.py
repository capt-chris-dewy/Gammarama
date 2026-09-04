#base / "vanilla" python library imports
import asyncio
import json
import random
import os
import re

#pip-installed library dependencies via virtual environment (venv)
import websockets

#custom classes for handling app functionality
import SPAWN_EXE
import COMMS

# Track active client connections
CONNECTED_CLIENTS = set()

EXE_SPAWNER = SPAWN_EXE.EXESpawner("Master")
PLC_HANDLER = COMMS.PLC("UML Sample Changer")

#global variables
SYSTEM_OPERATIONAL = 0 #now witness the power of this fully armed and operational battle station
PREVIOUS_POSITION = 0 #for command to go to previous
CURRENT_POSITION = 0
POLL_INTERVAL = 0.2 #seconds

#asyncio lock to prevent the UI querying the PLC at the same time as regular sensor polling
PLC_LOCK = asyncio.Lock()

# --- Python Handler Functions ---
def execute_greet_handler(target_id: str) -> dict:
    """Standard Python logic executed upon UI request."""
    return {
        "type": "ui_update",
        "target_id": target_id,
        "text": "Hello, World! (From Python)",
    }    
    
async def broadcast_sensor_data():
    global POLL_INTERVAL
    global CURRENT_POSITION
    while True:
        await asyncio.sleep(POLL_INTERVAL)
        if SYSTEM_OPERATIONAL == 1 and CONNECTED_CLIENTS:
            async with PLC_LOCK:
                position = PLC_HANDLER.readPosition()
                pos_sense_bit_array = PLC_HANDLER.readPosSensors()
                motor_fault_state = PLC_HANDLER.readMotorFault()
                
                CURRENT_POSITION = position
                
            sensor_info = {
                "type": "sensor_poll",
                "pos": position,
                "posSense": pos_sense_bit_array,
                "motorFault": motor_fault_state,
            }
            
            websockets.broadcast(CONNECTED_CLIENTS, json.dumps(sensor_info))
            

async def timer_program(hold_time, start, finish, save_to, target_ID):
    global CURRENT_POSITION
    
    #navigating to start position
    if CURRENT_POSITION != start:
        async with PLC_LOCK:
            PLC_HANDLER.goToPosition(start)
        
        while CURRENT_POSITION != start:
            #print(CURRENT_POSITION)
            await asyncio.sleep(1)
        
    #insert command to start collecting data here, and all other associated functionality
    EXE_SPAWNER.launch_genie2000()
    await asyncio.sleep(6) # wait 6 seconds for Genie to start up
    EXE_SPAWNER.manual_stop_acquisition()
    await asyncio.sleep(3) # wait 3 seconds for Genie to end acqusition (to clear data and stop acq if happening
    EXE_SPAWNER.manual_start_acquisition()
    await asyncio.sleep(3) # wait 3 seconds for Genie to begin acquiring data prior to starting the actual timer
    await asyncio.sleep(hold_time) #hold at position for specified time (set by user)
    EXE_SPAWNER.manual_stop_acquisition()
    error_out = EXE_SPAWNER.save_spectrum(save_to + "sample" + str(CURRENT_POSITION) + ".txt")
    #print(error_out)
    if "Error" in error_out:
        response = {"type":"ui_update", "target_id": target_ID, "text": error_out}
    else:
        await asyncio.sleep(5) #if no error, wait 5 seconds for file to save
        response = {"type":"ui_update", "target_id": target_ID, "text": "Status: Save Success: " + save_to + "sample" + str(CURRENT_POSITION) + ".txt"}
        await asyncio.sleep(3) # wait 3 seconds after stop before moving to next sample
        #defining first target
        if CURRENT_POSITION != 12:
            target = start + 1
        else:
            target = 1
        
        while True:
            if target == finish + 1:
                print("next target is " + str(target) + " meaning loop has finished")
                break
            async with PLC_LOCK:
                PLC_HANDLER.goToPosition(target)
            while CURRENT_POSITION != target:
                await asyncio.sleep(1) #check once per second if next position has been reached
            
            EXE_SPAWNER.manual_start_acquisition()
            await asyncio.sleep(3)
            await asyncio.sleep(hold_time)
            EXE_SPAWNER.manual_stop_acquisition()
            await asyncio.sleep(3)
            error_out = EXE_SPAWNER.save_spectrum(save_to + "sample" + str(CURRENT_POSITION) + ".txt")
            await asyncio.sleep(5) 
            
            if CURRENT_POSITION != 12:
                target = target + 1
            else:
                target = 1

async def counts_program(peaks, start, finish, save_to, target_ID):
    global CURRENT_POSITION
    
    #navigating to start position
    if CURRENT_POSITION != start:
        async with PLC_LOCK:
            PLC_HANDLER.goToPosition(start)
        
        while CURRENT_POSITION != start:
            #print(CURRENT_POSITION)
            await asyncio.sleep(1)
        
    #find what to do for this sample
    samplePeak = -1
    for i in range(len(peaks)):
        peak = peaks[i]
        relevant_samples = peak.get("Applies to Samples")
        if str(CURRENT_POSITION) in relevant_samples:
            print("sample " + str(CURRENT_POSITION) + " controlled by " + peak.get("Name"))
            samplePeak = i
            break
    
    SAMPLE_CENTROID = 0;
    SAMPLE_WIDTH = 0;
    SAMPLE_TIL_COUNTS = 0;
    
    if samplePeak != -1:
        SAMPLE_CENTROID = peaks[samplePeak].get("Peak Centroid (keV)")
        SAMPLE_WIDTH = peaks[samplePeak].get("Peak Width (keV)")
        SAMPLE_TIL_COUNTS = peaks[samplePeak].get("Move to Next Sample after")        
    else:
        print("peak not found for sample " + str(CURRENT_POSITION))
        return
    
    #insert command to start collecting data here, and all other associated functionality
    EXE_SPAWNER.launch_genie2000()
    await asyncio.sleep(6) # wait 6 seconds for Genie to start up
    EXE_SPAWNER.manual_stop_acquisition()
    await asyncio.sleep(3) # wait 3 seconds for Genie to end acqusition (to clear data and stop acq if happening
    #new data collection method, the automatic version, see SPAWN_EXE.py
    await EXE_SPAWNER.acquire_until_counts(SAMPLE_TIL_COUNTS, SAMPLE_CENTROID, SAMPLE_WIDTH)
    error_out = EXE_SPAWNER.save_spectrum(save_to + "sample" + str(CURRENT_POSITION) + ".txt")
    #print(error_out)
    if "Error" in error_out:
        response = {"type":"ui_update", "target_id": target_ID, "text": error_out}
    else:
        await asyncio.sleep(5) #if no error, wait 5 seconds for file to save
        response = {"type":"ui_update", "target_id": target_ID, "text": "Status: Save Success: " + save_to + "sample" + str(CURRENT_POSITION) + ".txt"}
        await asyncio.sleep(3) # wait 3 seconds after stop before moving to next sample
        #defining first target
        if CURRENT_POSITION != 12:
            target = start + 1
        else:
            target = 1
        
        while True:
            samplePeak = -1
            if target == finish + 1:
                print("next target is " + str(target) + " meaning loop has finished")
                break
            async with PLC_LOCK:
                PLC_HANDLER.goToPosition(target)
            while CURRENT_POSITION != target:
                await asyncio.sleep(1) #check once per second if next position has been reached
            
            for i in range(len(peaks)):
                peak = peaks[i]
                relevant_samples = peak.get("Applies to Samples")
                if str(CURRENT_POSITION) in relevant_samples:
                    print("sample " + str(CURRENT_POSITION) + " controlled by " + peak.get("Name"))
                    samplePeak = i
                    break
                    
            if samplePeak != -1:
                SAMPLE_CENTROID = peaks[samplePeak].get("Peak Centroid (keV)")
                SAMPLE_WIDTH = peaks[samplePeak].get("Peak Width (keV)")
                SAMPLE_TIL_COUNTS = peaks[samplePeak].get("Move to Next Sample after")        
            else:
                print("peak not found for sample " + str(CURRENT_POSITION))
                return
            
            await EXE_SPAWNER.acquire_until_counts(SAMPLE_TIL_COUNTS, SAMPLE_CENTROID, SAMPLE_WIDTH)
            error_out = EXE_SPAWNER.save_spectrum(save_to + "sample" + str(CURRENT_POSITION) + ".txt")
            await asyncio.sleep(5) 
            
            if CURRENT_POSITION != 12:
                target = target + 1
            else:
                target = 1
        
  
async def websocket_handler(websocket):
    global PREVIOUS_POSITION
    global SYSTEM_OPERATIONAL
    CONNECTED_CLIENTS.add(websocket)
    print(f"[+] Client connected. Total: {len(CONNECTED_CLIENTS)}")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            target_id = data.get("target")
            
            match action:
                case "portScan":
                    async with PLC_LOCK:
                        port_list = PLC_HANDLER.list_COM_ports()
                    response = {"type":"get_values_for_handler", "target_id": target_id, "text": port_list}
                
                case "initSerial":
                    com_port = data.get("COMSelected")
                    
                    async with PLC_LOCK:
                        result = PLC_HANDLER.initializeSerialComms(com_port)
                    message = -1;
                
                    #equivalent of a switch statement:
                    status_color = -1;
                    match result:
                        
                        case 0:
                            message = "SerialException: Device not found"
                            status_color = {"r": 255, "g": 0, "b": 0}
                        case 1:
                            message = "SYSTEM ONLINE"
                            SYSTEM_OPERATIONAL = 1
                            status_color = {"r": 0, "g": 140, "b": 0}
                        case 2:
                            message = "Error: PLC returned invalid positon < 0 or > 12"
                            status_color = {"r": 255, "g": 0, "b": 0}
                    
                    response = {"type":"ui_update", "target_id": target_id, "text": message, "status_rgb": status_color}
                    
                case "initMotor":
                    async with PLC_LOCK:
                        result = PLC_HANDLER.initializeMotor()
                    response = {"type":"ui_update", "target_id": target_id, "text": result}
                
                case "nextPos":
                    async with PLC_LOCK:
                        old_position = PLC_HANDLER.readPosition()
                    PREVIOUS_POSITION = old_position
                
                    async with PLC_LOCK:
                        result = PLC_HANDLER.indexPos()
                    response = {"type":"ui_update", "target_id": target_id, "text": result}
                    
                case "goToPos":
                    async with PLC_LOCK:
                        old_position = PLC_HANDLER.readPosition()
                    PREVIOUS_POSITION = old_position
                
                    new_position = data.get("new_position")
                    async with PLC_LOCK:
                        result = PLC_HANDLER.goToPosition(new_position)
                    response = {"type":"ui_update", "target_id": target_id, "text": result}
                    
                case "prevPos":
                    prev_position = PREVIOUS_POSITION
                
                    async with PLC_LOCK:
                        old_position = PLC_HANDLER.readPosition()
                    PREVIOUS_POSITION = old_position
                
                    async with PLC_LOCK:
                        result = PLC_HANDLER.goToPosition(prev_position)
                    response = {"type":"ui_update", "target_id": target_id, "text": result}
                
                case "launch_genie":
                    EXE_SPAWNER.launch_genie2000()
                    response = {"nada":""}
                
                case "manual_start_mca":
                    EXE_SPAWNER.manual_start_acquisition()
                    response = {"nada":""}
                    
                case "manual_stop_mca":
                    EXE_SPAWNER.manual_stop_acquisition()
                    response = {"nada":""}
                
                case "manual_save":
                    save_path = data.get("the_path")
                    #print(save_path)
                    if os.path.isfile(save_path):
                        response = {"type":"ui_update", "target_id": target_id, "text": "Status: ERROR - Overwrite disabled, delete file or rename"}
                        await websocket.send(json.dumps(response))
                    else:
                        
                        dir_path_check = save_path.rsplit("\\", 1)[0] #remove the file name and extension, get dir path
                        if not os.path.exists(dir_path_check):
                            os.makedirs(dir_path_check)
                        error_out = EXE_SPAWNER.save_spectrum(save_path)
                        #print(error_out)
                        if "Error" in error_out:
                            response = {"type":"ui_update", "target_id": target_id, "text": error_out}
                        else:
                            response = {"type":"ui_update", "target_id": target_id, "text": "Status: Save Success!!"}
                    
                case "start_timer_program":
                    hrs = data.get("hold_time_hrs")
                    mins = data.get("hold_time_mins")
                    s = data.get("hold_time_secs")
                    
                    if hrs == "":
                        print("hours not specified, defaulting to 0")
                        hrs = 0
                        
                    if mins == "":
                        print("minutes not specified, defaulting to 0")
                        mins = 0
                        
                    if s == "":
                        print("seconds not specified, defaulting to 0")
                        s = 0
                    
                    #print(hold_time_hrs + ", " + hold_time_mins + ", " + hold_time_s)
                    
                    save_to_dir = data.get("save_loc")
                    starting_pos = data.get("start_pos")
                    ending_pos = data.get("end_pos")
                    
                    if save_to_dir == "" or save_to_dir is None:
                        print("\"Save to Directory:\" cannot be blank, must specify location to save spectra")
                        response = {"type":"ui_update", "target_id": target_id, "text": "Status: ERROR - Overwrite disabled, delete file or rename"}
                    
                    if os.path.exists(save_to_dir):
                        print("Error: Directory already exists, overwrite not yet implemented.")
                        response = {"type":"ui_update", "target_id": target_id, "text": "Error: Directory already exists, overwrite not yet implemented."}
                    else:    
                        if starting_pos.isdigit() == False or ending_pos.isdigit() == False:
                            print("Error: starting or ending position is not a digit. please specify and try again")
                            response = {"type":"ui_update", "target_id": target_id, "text": "Status: ERROR -- starting or ending position is not a digit. please specify and try again"}
                        else:
                            print("Creating directory" + str(save_to_dir))
                            os.makedirs(save_to_dir)
                            
                            hold_time_sec = int(hrs) * 60 * 60 + int(mins) * 60 + int(s)
                    
                            if hold_time_sec < 3:
                                print("Error: time per sample should be longer than or equal to 3 seconds.")
                                response = {"type":"ui_update", "target_id": target_id, "text": "Status: ERROR -- time per sample should be longer than or equal to 3 seconds."}
                            else:
                                asyncio.create_task(timer_program(hold_time_sec, int(starting_pos), int(ending_pos), save_to_dir, target_id))
                                response = {"type":"ui_update", "target_id": target_id, "text": "Status: SUCCESS -- INITIATING TIMER PROGRAM"}
                
                case "start_counts_program":
                    save_to_dir = data.get("save_loc")
                    
                    starting_pos = data.get("start_pos")
                    ending_pos = data.get("end_pos")
                    
                    control_peak_params = data.get("control_peaks")
                    #print(control_peak_params)
                    
                    response = {"nada":""} #default value to send back to JS / browser to prevent error
                    
                    if save_to_dir == "" or save_to_dir is None:
                        print("\"Save to Directory:\" cannot be blank, must specify location to save spectra")
                        response = {"type":"ui_update", "target_id": target_id, "text": "Status: ERROR - Overwrite disabled, delete file or rename"}
                    else:
                        if starting_pos.isdigit() == False or ending_pos.isdigit() == False:
                            print("Error: starting or ending position is not a digit. please specify and try again")
                            response = {"type":"ui_update", "target_id": target_id, "text": "Status: ERROR -- starting or ending position is not a digit. please specify and try again"}
                        else:
                            if os.path.exists(save_to_dir):
                                print("Error: Directory already exists, overwrite not yet implemented.")
                                response = {"type":"ui_update", "target_id": target_id, "text": "Error: Directory already exists, overwrite not yet implemented."}
                            else:
                                print("Creating directory" + str(save_to_dir))
                                os.makedirs(save_to_dir)
                                empty_flag = False
                                for peak in control_peak_params:
                                    print(type(peak))
                                    print(peak)
                                    for param, value in peak.items():
                                        if value == "" or value is None:
                                            empty_flag = True
                                    if empty_flag:
                                        print("Error: One or more fields for your control peak is blank / null, please fix")
                                        response = {"type":"ui_update", "target_id": target_id, "text": "Error: One or more fields for your control peak is blank / null, please fix"}
                                    else:
                                        for i in range(len(control_peak_params)):
                                            this_peak = control_peak_params[i]
                                            #check if all numerical parameters are integres
                                            if not (this_peak.get("Peak Centroid (keV)").isdigit() and this_peak.get("Peak Width (keV)").isdigit() and this_peak.get("Move to Next Sample after").isdigit()):
                                                print("Status: Error -- Centroid, Peak Width and Counts til Next Sample must be integers")
                                                response = {"type":"ui_update", "target_id": target_id, "text": "Status: Error -- Centroid, Peak Width and Counts til Next Sample must be integers"}
                                            else:
                                                comma_separated_regex = re.compile(r"^(\d+)(,\s*\d+)*$") #comma-separated integers only
                                                if not bool(comma_separated_regex.match(this_peak.get("Applies to Samples"))):
                                                    print("Status: Error -- Sample list must be comma-separated")
                                                    response = {"type":"ui_update", "target_id": target_id, "text": "Status: Error -- Sample list must be comma-separated"}
                                                else:
                                                    invalid_sample = -1;
                                                    sample_list = this_peak.get("Applies to Samples").split(",")
                                                    for sample in sample_list:
                                                        sample.strip()
                                                        sample = int(sample)
                                                        if not sample >= 1 and sample <= 12:
                                                            invalid_sample = sample;
                                                    
                                                    if invalid_sample != -1:
                                                        print("Status: Error -- Invalid Sample ID detected: " + str(invalid_sample))
                                                        response = {"type":"ui_update", "target_id": target_id, "text": "Status: Error -- Invalid Sample ID detected: " + str(invalid_sample)}
                                                    else:    
                                                        asyncio.create_task(counts_program(control_peak_params, int(starting_pos), int(ending_pos), save_to_dir, target_id))
                                                        response = {"type":"ui_update", "target_id": target_id, "text": "Status: SUCCESS -- INITIATING COUNTS PROGRAM"}
                
                case "commandOverride":
                    cmd = data.get("commandToSend")
                    async with PLC_LOCK:
                        plc_response = PLC_HANDLER.command_override(cmd)
                    response = {"type":"ui_update", "target_id": target_id, "text": plc_response}
                    
                case "greet":
                    response = execute_greet_handler(target_id)
                case "launchBENDER":
                    #the r prefacing the string below is necessary so that Python acknowledges the "\" in the file
                    #as not representing an escape character preface
                
                    #note also: browsers don't seem to like accessing files from absolute paths stemming from your C drive
                    #but don't mind relative paths from the working directory of this python server file, say
                    message = EXE_SPAWNER.gif_handler(r"media\bender.gif")
                    response = {"type":"ui_update", "target_id": target_id, "text": message}
        
            await websocket.send(json.dumps(response))

    except websockets.ConnectionClosedError:
        pass
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        print(f"[-] Client disconnected. Total: {len(CONNECTED_CLIENTS)}")


# --- Server Initialization & Polling Task Creation ---
async def main():
    asyncio.create_task(broadcast_sensor_data())
    async with websockets.serve(websocket_handler, "localhost", 8000):
        print("WebSocket Server running at ws://localhost:8000")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())