import subprocess

class EXESpawner():
    def __init__(self, name):
        self.name = name
    
    def launch_genie2000(self):
        print("Launching Genie...")
        exe_path = r"C:\GENIE2K\EXEFILES\putview.exe"
        arg0 = "det:GEOLOGY"
        subprocess.Popen([exe_path, arg0])
        
    def manual_start_acquisition(self):
        print("STARTING Data Acquisition...")
        exe_path = r"C:\GENIE2K\EXEFILES\startmca.exe"
        arg0 = "det:GEOLOGY"
        arg1 = "/LIVEPRESET=86400" #starts a 24hr acquisition -- ideally longer than you would ever need
        subprocess.Popen([exe_path, arg0, arg1])
        
    def manual_stop_acquisition(self):
        print("STOPPING Data Acquisition...")
        exe_path = r"C:\GENIE2K\EXEFILES\stopmca.exe"
        arg0 = "det:GEOLOGY"
        subprocess.Popen([exe_path, arg0])
        
    def gif_handler(self, path_to_gif):
        #using file explorer for gifs (explore.exe) works for opening gifs if the default media viewer
        #for gifs is photos -- it may work for others I just haven't tested it
        exe_path = "explorer.exe"
        """Spawns an external .exe file and returns GIF metadata to the client."""
        try:
            # Popen spawns the process in the background and DOES NOT block asyncio
            subprocess.Popen([exe_path, path_to_gif])
            print(f"[!] Successfully launched: " + str(exe_path))
            return "Doing a gif!"
        except Exception as e:
            print(f"[X] Failed to launch executable: {e}")
            return "No GIF for you!"