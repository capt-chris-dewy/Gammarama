// Open persistent connection to Python server
const socket = new WebSocket('ws://localhost:8000');
socket.onopen = () => console.log('Connected to Python WebSocket Server');
// Unified incoming message dispatcher
socket.onmessage = (event) => {
	const data = JSON.parse(event.data);
	// Handle single UI update response from button click
	if (data.type === 'ui_update') {
		document.getElementById(data.target_id).innerText = data.text;
		//update_elements document.querySelectorAll(); //retrieves list of elements matching search criteria (class or ID)
		//update_elements.forEach(element => {element.innerText = data.text});
		if ('status_rgb' in data) {
			let {r, g, b} = data.status_rgb;
			document.getElementById(data.target_id).style.color = `rgb(${r}, ${g}, ${b})`;
		}
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
		
		const positionDisplays = document.querySelectorAll(".position-value");
		positionDisplays.forEach(posDisplay => {
			posDisplay.innerText = position_read;
		});
		//innerText = position_read;
	}
};

/*WEBPAGE FUNCTIONALITY: SHOW/HIDE UI OPTIONS FOR MANUAL AND AUTOPILOT MODES*/
showContent('manual-mode') //by default hide all other modes besides manual

let peakCount = 0;

function showContent(id) {
	// Hide all content boxes
	document.querySelectorAll('.selectable-mode').forEach(el => {
		el.style.display = 'none';
	});
	// Show the selected box
	document.getElementById(id).style.display = 'block';
}

function addPeak() {
	const controlPeaksParent = document.getElementById('controlPeakList');
	peakCount = peakCount + 1;
	controlPeaksParent.appendChild(createControlPeak(peakCount));
}

function createControlPeak(n) {
	const PARAM_NAMES = ['Name', 'Peak Centroid (keV)', 'Peak Width (keV)', 'Move to Next Sample after', 'Applies to Samples'];

    const peakBlock = document.createElement('div');
    peakBlock.className = 'peak-block';
    peakBlock.dataset.object = n; // used later to identify/extract this block

    const header = document.createElement('div');
    header.className = 'peak-header';
    header.innerHTML = `<span>Control Peak ${n}</span>`;

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
	removeBtn.className = 'remove-btn';
    removeBtn.textContent = 'Remove Peak';
	
    // Listener attached right when the button is created, so no
    // delegation needed here — the element exists by the time we bind it.
    removeBtn.addEventListener('click', () => {
		peakCount -= 1;
		const peakNumberRemoved = peakBlock.dataset.object;
		document.querySelectorAll('.peak-block').forEach(block => {
		  const data = { objectId: block.dataset.object };
		  console.log(data.objectId);
		  if (data.objectId > peakNumberRemoved) {
			block.dataset.object = data.objectId - 1; //decrement to keep numbers in order
			let thisBlockHeader = block.querySelector('.peak-header');
			thisHeaderSpan= thisBlockHeader.querySelector('span');
			thisHeaderSpan.textContent = `Control Peak ${block.dataset.object}`;
		  }
		});
		peakBlock.remove();
	});
    header.appendChild(removeBtn);
    peakBlock.appendChild(header);

    PARAM_NAMES.forEach((paramKey, i) => {
	  let this_input;
	  let add_suffix = "";
	  const row = document.createElement('div');
      row.className = 'row';
      row.innerHTML = `
        <span>${PARAM_NAMES[i]}:</span>
        `;
	  this_input = document.createElement('input');
	  //<input type="text" class="control-peak-input" placeholder= "..." data-param="${paramKey}" oninput="this.style.width = this.value.length + 1 + 'ch'">
	  this_input.type = "text"
	  this_input.className = "control-peak-input"
	  this_input.oninput = "this.style.width = this.value.length + 1 + 'ch'"
	  this_input.setAttribute('data-param', `${paramKey}`)
	  
	  switch(PARAM_NAMES[i]) {
		case "Name":
			this_input.placeholder="ex: 60Co"
			break;
		case "Peak Centroid (keV)":
			this_input.placeholder="ex: 1332"
			break;
		
		case "Peak Width (keV)":
			this_input.placeholder="ex: 5"
			break;
			
		case "Move to Next Sample after":
			this_input.placeholder="ex: 10000"
			add_suffix = "counts";
			break;
			
		case "Applies to Samples":
			this_input.placeholder="ex: 2,3,4,5"
			break;
			
	  }
	  row.appendChild(this_input);
	  if (add_suffix != "") {
		row.insertAdjacentHTML('beforeend', '<span> counts </span>')  
	  }
      peakBlock.appendChild(row);
    });

    return peakBlock;
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

function triggerGenieLaunch() {
	const payload = {
		action: 'launch_genie'
	};
	
	socket.send(JSON.stringify(payload));
}

function trigger_MANUAL_START_MCA() {
	const payload = {
		action: 'manual_start_mca'
	};
	
	socket.send(JSON.stringify(payload));
}

function trigger_MANUAL_STOP_MCA() {
	const payload = {
		action: 'manual_stop_mca'
	};
	
	socket.send(JSON.stringify(payload));
}

function triggerManualSave() {
	const user_path = document.getElementById("manual-save-location").value;
	const path_prefix = "C:\\Users\\User\\Desktop\\" //double back slash to not be escape chars
	const path = path_prefix + user_path;
	const payload = {
		action: 'manual_save',
		target: 'manual-error',
		the_path: path
	};
	
	socket.send(JSON.stringify(payload));
}

function triggerTimerStart() {
	const hrs = document.getElementById('timer-hrs').value;
	const mins = document.getElementById('timer-mins').value;
	const secs = document.getElementById('timer-secs').value;
	
	const start_position = document.getElementById('start-pos-timer').value;
	const end_position = document.getElementById('end-pos-timer').value;
	
	const user_directory = document.getElementById('timer-save-location').value;
	const path_prefix = "C:\\Users\\User\\Desktop\\";
	const path = path_prefix + user_directory;
	
	const payload = {
		action: 'start_timer_program',
		target: 'timer-error',
		hold_time_hrs: hrs,
		hold_time_mins: mins,
		hold_time_secs: secs,
		save_loc: path,
		start_pos: start_position,
		end_pos: end_position
	};
	
	socket.send(JSON.stringify(payload));
}
function triggerCountsStart() {
	const start_position = document.getElementById('start-pos-counts').value;
	const end_position = document.getElementById('end-pos-counts').value;
	
	const user_directory = document.getElementById('counts-save-location').value;
	const path_prefix = "C:\\Users\\User\\Desktop\\";
	const path = path_prefix + user_directory;
	
	let peaksAndParams = [];
	
	//obtain parameters for control peaks
	document.querySelectorAll('.peak-block').forEach(controlPeak =>{
		const thisPeakParams = {};
		const controlPeakParams = {objectId: controlPeak.dataset.object};
		controlPeak.querySelectorAll('.control-peak-input').forEach(inputParam => {
			const thisParamType = inputParam.getAttribute('data-param');
			thisPeakParams[thisParamType] = inputParam.value;
		});
		peaksAndParams.push(thisPeakParams);
	});
	
	const payload = {
		action: 'start_counts_program',
		target: 'counts-error',
		save_loc: path,
		start_pos: start_position,
		end_pos: end_position,
		control_peaks: peaksAndParams
	};
	
	socket.send(JSON.stringify(payload));
}

