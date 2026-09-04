import subprocess
import asyncio

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
        
    async def acquire_until_counts(self, counts, centroid, width):
        print("STARTING Data Acquisition, waiting for " + str(counts) + " counts of " + str(centroid) + " keV gammas" + "...")
        exe_path = r"C:\GENIE2K\EXEFILES\startmca.exe"
        arg0 = "det:GEOLOGY"
        arg1= "/INTPRESET=" + str(counts) + "," + str(int(centroid) - int(width)) + "," + str(int(centroid) + int(width))
        wait_process1 = await asyncio.create_subprocess_exec(exe_path, arg0, arg1)
        return_code = await wait_process1.wait()
        
        exe_path = r"C:\GENIE2K\EXEFILES\wait.exe"
        arg0 = "det:GEOLOGY"
        arg1 = "/ACQ"
        wait_process2 = await asyncio.create_subprocess_exec(exe_path, arg0, arg1)
        #wait_process = await asyncio.create_subprocess_exec(exe_path, arg0, arg1, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        return_code = await wait_process2.wait()
        #stdout, stderr = await wait_process.communicate()

    def save_spectrum(self, input_path):
        print("Saving Spectrum to " + input_path)
        exe_path = r"C:\GENIE2K\EXEFILES\movedata.exe"
        arg0 = "det:GEOLOGY"
        arg1 = input_path
        arg2 = "/DATA"
        this_process = subprocess.Popen([exe_path, arg0, arg1, arg2],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        stdout, stderr = this_process.communicate()
        print("STDOUT: " + stdout) #contains the good stuff
        print("STDERR: " + stderr) #may or may not be used by GENIE outputting to console
        return stdout
    
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