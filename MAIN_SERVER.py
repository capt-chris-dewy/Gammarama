#base / "vanilla" python library imports
import asyncio
import json
import random

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
SENSOR_POLL_INTERVAL = 0.5 #seconds

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
    global SENSOR_POLL_INTERVAL
    while True:
        await asyncio.sleep(SENSOR_POLL_INTERVAL)
        if SYSTEM_OPERATIONAL == 1 and CONNECTED_CLIENTS:
            async with PLC_LOCK:
                position = PLC_HANDLER.readPosition()
                pos_sense_bit_array = PLC_HANDLER.readPosSensors()
                motor_fault_state = PLC_HANDLER.readMotorFault()
            sensor_info = {
                "type": "sensor_poll",
                "pos": position,
                "posSense": pos_sense_bit_array,
                "motorFault": motor_fault_state,
            }
            websockets.broadcast(CONNECTED_CLIENTS, json.dumps(sensor_info))
            
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
                    match result:
                        case 0:
                            message = "SerialException: Device not found"
                        case 1:
                            message = "Serial connection established, system online"
                            SYSTEM_OPERATIONAL = 1
                        case 2:
                            message = "Error: PLC returned invalid positon < 0 or > 12"
                    
                    response = {"type":"ui_update", "target_id": target_id, "text": message}
                    
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