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
# --- Python Handler Functions ---
def execute_greet_handler(target_id: str) -> dict:
    """Standard Python logic executed upon UI request."""
    return {
        "type": "ui_update",
        "target_id": target_id,
        "text": "Hello, World! (From Python)",
    }

async def websocket_handler(websocket):
    CONNECTED_CLIENTS.add(websocket)
    print(f"[+] Client connected. Total: {len(CONNECTED_CLIENTS)}")
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")

            # Match incoming UI trigger requests
            if action == "greet":
                target_id = data.get("target")
                response = execute_greet_handler(target_id)
                await websocket.send(json.dumps(response))
                
            if action == "launchBENDER":
                #the r prefacing the string below is necessary so that Python acknowledges the "\" in the file
                #as not representing an escape character preface
                
                #note also: browsers don't like accessing files from absolute paths stemming from your C drive
                #but don't mind relative paths from the working directory of this python server file, say
                target_id = data.get("target")
                message = EXE_SPAWNER.gif_handler(r"media\bender.gif")
                response = {"type":"ui_update", "target_id": target_id, "text": message}
                await websocket.send(json.dumps(response))
            
            if action == "portScan":
                target_id = data.get("target")
                port_list = PLC_HANDLER.list_COM_ports()
                response = {"type":"get_values_for_handler", "target_id": target_id, "text": port_list}
                await websocket.send(json.dumps(response))
            
            if action == "initSerial":
                target_id = data.get("target")
                com_port = data.get("COMSelected")
                message = PLC_HANDLER.initializeSerialComms(com_port);
                response = {"type":"ui_update", "target_id": target_id, "text": message}
                await websocket.send(json.dumps(response))
            
            if action == "commandOverride":
                target_id = data.get("target")
                cmd = data.get("commandToSend")
                plc_response = PLC_HANDLER.command_override(cmd)
                response = {"type":"ui_update", "target_id": target_id, "text": plc_response}
                await websocket.send(json.dumps(response))

    except websockets.ConnectionClosedError:
        pass
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        print(f"[-] Client disconnected. Total: {len(CONNECTED_CLIENTS)}")


# --- Server Initialization ---
async def main():
    # Start the WebSocket server on port 8000
    async with websockets.serve(websocket_handler, "localhost", 8000):
        print("WebSocket Server running at ws://localhost:8000")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())