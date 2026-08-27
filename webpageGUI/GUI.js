// Open persistent connection to Python server
const socket = new WebSocket('ws://localhost:8000');
socket.onopen = () => console.log('Connected to Python WebSocket Server');
// Unified incoming message dispatcher
socket.onmessage = (event) => {
	const data = JSON.parse(event.data);
	// Handle single UI update response from button click
	if (data.type === 'ui_update') {
		document.getElementById(data.target_id).innerText = data.text;
	}
	
	if (data.type === 'get_values_for_handler') {
		if(data.target_id === 'updateDropdown') {
			updateDropdown(data.text)
		}
	}
	
	if (data.type === 'sensor_poll') {
		posSensors = data.posSense;
		motorFault = data.motorFault;
		position_read = data.pos;
		
		document.getElementById("sensorB-value").innerText = posSensors[0];
		document.getElementById("sensorC-value").innerText = posSensors[1];
		document.getElementById("sensorD-value").innerText = posSensors[2];
		document.getElementById("sensorE-value").innerText = posSensors[3];
		document.getElementById("sensorF-value").innerText = posSensors[4];
		document.getElementById("sensorH-value").innerText = posSensors[5];
		
		document.getElementById("position-value").innerText = position_read;
	}
};

/*WEBPAGE FUNCTIONALITY: SHOW/HIDE UI OPTIONS FOR MANUAL AND AUTOPILOT MODES*/
function showContent(id) {
	// Hide all content boxes
	document.querySelectorAll('.selectable-mode').forEach(el => {
		el.style.display = 'none';
	});
	// Show the selected box
	document.getElementById(id).style.display = 'block';
}
/*MISCELLANEOUS: SILLY FUNCTIONS*/

function triggerPythonGreet() {
	const payload = {
		action: 'greet',
		target: 'greeting-output'
	};
	socket.send(JSON.stringify(payload));
}

function triggerBENDER() {
	const payload = {
		action: 'launchBENDER',
		target: 'bender-out'
	};
	socket.send(JSON.stringify(payload));
}

/*MISCELLANEOUS: COMMAND OVERRIDE*/

function triggerOverride() {
	// 1. Get the value from the text input field
	const inputTextElement = document.getElementById('command-override');
	const overrideCommand = inputTextElement.value;

	// Validation check (optional, but good practice)
	if (!overrideCommand.trim()) {
		document.getElementById('override-response').innerText = "Please enter some text first.";
		return;
	}
	
	const payload = {
		commandToSend: overrideCommand,
		action: 'commandOverride',
		target: 'override-response'
	};
	socket.send(JSON.stringify(payload));
}

/*INITIALIZATION: COM PORT SCAN + SELECTION UTILITY*/
function triggerSerialScan() {
	const payload = {
		action: 'portScan',
		target: 'updateDropdown'
	};
	
	socket.send(JSON.stringify(payload));
}

function updateDropdown(portListing) {
	const dropdown = document.getElementById('port-dropdown');
    const connectStatus = document.getElementById('connect-status');

    if (!portListing || portListing.length === 0) {
        connectStatus.innerText = "No options returned.";
        return;
    }

    // Clear existing options and reset default prompt
    dropdown.innerHTML = '<option value="" disabled selected>Select an option...</option>';

    // Loop through the list received over the WebSocket and inject them
    portListing.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item;
        opt.text = item;
        dropdown.appendChild(opt);
    });
}

function triggerSerialConnect() {
	const dropdown = document.getElementById('port-dropdown');
	const current_dropdown_value = dropdown.value;
	const COMPortValue = current_dropdown_value.slice(0, 4);
	const payload = {
		COMSelected: COMPortValue,
		action: 'initSerial',
		target: 'connect-status'
	};
	
	socket.send(JSON.stringify(payload));
}

/*INITIALIZATION: MOTOR / PLC START-UP*/
function triggerMotorInit() {
	const payload = {
		action: 'initMotor',
		target: 'motor-init-result'
	};
	
	socket.send(JSON.stringify(payload));
}

/*BASIC MOVEMENT FUNCTIONS: PREVIOUS/NEXT/GO-TO-ARBITRARY-POSITION*/
function triggerPrevious() {
	const payload = {
		action: 'prevPos',
		target: 'new-pos'
	};
	
	socket.send(JSON.stringify(payload));
}

function triggerNext() {
	const payload = {
		action: 'nextPos',
		target: 'new-pos'
	};
	
	socket.send(JSON.stringify(payload));
}

function triggerGoToPos() {
	const new_position_entry = document.getElementById('go-to-pos-input');
	const new_pos_value = new_position_entry.value;
	
	const payload = {
		new_position: new_pos_value,
		action: 'goToPos',
		target: 'new-pos'
	};
	
	socket.send(JSON.stringify(payload));
}