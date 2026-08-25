Hello and welcome to the control system source code for UMass Lowell's Instrumental Neutron Activation Analysis 
(INAA) laboratory facility. The setup includes an HPGe detector paired with a Canberra DSA1000 all-in-one
pre-amp + detector biasing power supply / digitizer setup, alongside a custom Opto-22 PLC rig controlling a Sample
Changer turntable and associated logic + sensors. Genie 2000 softare from Canberra interfaces with the DSA1000 to
build gamma ray spectra for samples undergoing INAA to be analyzed for chemical forensics / elemental analysis.

This Github repo version controls the Graphical User Interface (GUI) built in HTML/CSS + JavaScript with a
Python back-end handling behind-the-scenes logic and communication with the Opto-22 PLC. The eventual hope is 
to create a "turnkey" software allowing for completely hands-off data collection control system, alongside 
automating much of the data pre-processing + analysis process.

Thank you for reading, and happy coding / referencing.

---------------------------------------------------------------------------------------------------------
Dependencies:

The Python code is predominantly built on standard libraries / packages included in contemporary (2026)
default installations of Python. However, the creation of a virtual environment (venv) is essential at this time
for managing the following packages

Simply look up the instructions to create and run a python venv on your operating system and run the following
commands once activated:

pip install pyserial (Note: handles serial comms with the Opto-22 PLC)
pip install websockets (Note: handles communication between the web browser JavaScript and the back-end python)
