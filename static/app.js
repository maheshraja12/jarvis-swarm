// J.A.R.V.I.S. Swarm HUD Dashboard JS Controller

// Determine the API base URL. If hosted on a third-party domain like Vercel, connect to the local JARVIS API.
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') 
    ? '' 
    : 'http://127.0.0.1:8000';

document.addEventListener("DOMContentLoaded", () => {
    // 1. Clock Telemetry Loop
    updateClock();
    setInterval(updateClock, 1000);

    // 2. Poll Status Loop
    pollSystemStatus();
    setInterval(pollSystemStatus, 2000);

    // 3. Load Memory & Tools List
    loadMemories();
    loadTools();

    // 4. Command Input Handler
    const cmdInput = document.getElementById("command-input");
    const sendBtn = document.getElementById("send-btn");
    
    sendBtn.addEventListener("click", executeCommand);
    cmdInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            executeCommand();
        }
    });

    // 5. Memory Search Filter
    const searchInput = document.getElementById("memory-search-input");
    searchInput.addEventListener("input", filterMemories);

    // 6. Soundwave Visualizer Setup
    initSoundwave();

    // 7. Browser Speech Recognition & Synthesis Init
    initBrowserSpeech();
});

// CLOCK HANDLER
function updateClock() {
    const dateEl = document.getElementById("hud-date");
    const timeEl = document.getElementById("hud-time");
    
    const now = new Date();
    
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    dateEl.textContent = now.toLocaleDateString('en-US', options).toUpperCase();
    
    timeEl.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
}

// SYSTEM STATUS POLLING
let currentStatus = "STANDBY";
async function pollSystemStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        if (!response.ok) return;
        
        const data = await response.json();
        
        // Update gauges
        document.getElementById("cpu-val").textContent = `${data.cpu}%`;
        document.getElementById("cpu-bar").style.width = `${data.cpu}%`;
        
        document.getElementById("ram-val").textContent = `${data.ram}%`;
        document.getElementById("ram-bar").style.width = `${data.ram}%`;
        
        document.getElementById("battery-val").textContent = `${data.battery.charge}%`;
        document.getElementById("battery-bar").style.width = `${data.battery.charge}%`;
        
        // Update Swarm Actor visual states
        updateSwarmActors(data.swarm_state);
        
        // Update Audio Visual Status
        const audioStatus = data.audio_status.toUpperCase();
        const statusBox = document.getElementById("speaker-status");
        statusBox.textContent = audioStatus;
        statusBox.className = "voice-status " + data.audio_status.toLowerCase();
        
        // Update Stark Neural Core reactor state & telemetry
        const arcReactor = document.querySelector(".arc-reactor");
        if (arcReactor) {
            arcReactor.setAttribute("data-status", data.audio_status.toLowerCase());
        }
        const coreStatusText = document.querySelector(".core-status-text");
        if (coreStatusText) {
            coreStatusText.textContent = `CORE: ${audioStatus}`;
        }
        const coreFrequency = document.querySelector(".core-frequency");
        if (coreFrequency) {
            // Generate a technical-looking oscillating frequency
            const freq = (95.0 + Math.sin(Date.now() / 1000) * 3.5).toFixed(1);
            coreFrequency.textContent = `FREQ: ${freq} MHz`;
        }
        
        currentStatus = audioStatus;

        // Auto-scroll logs to bottom if new entries added
        const logsBox = document.getElementById("console-logs-feed");
        const isNearBottom = logsBox.scrollHeight - logsBox.clientHeight - logsBox.scrollTop < 100;
        
        // Dynamic loading of newly generated tools if counts mismatch
        const customToolsCount = document.querySelectorAll(".tool-item.custom").length;
        if (data.custom_tools_count !== customToolsCount) {
            loadTools();
        }
        
    } catch (e) {
        console.warn("Telemetry polling failed:", e);
    }
}

function updateSwarmActors(state) {
    const orchestrator = document.getElementById("actor-orchestrator");
    const engineer = document.getElementById("actor-engineer");
    const critic = document.getElementById("actor-critic");
    
    // Reset classes
    orchestrator.className = "actor-card";
    engineer.className = "actor-card";
    critic.className = "actor-card";
    
    if (state === "orchestrating") {
        orchestrator.className = "actor-card active";
    } else if (state === "coding") {
        orchestrator.className = "actor-card active";
        engineer.className = "actor-card active thinking";
    } else if (state === "critiquing") {
        orchestrator.className = "actor-card active";
        critic.className = "actor-card active thinking";
    } else {
        orchestrator.className = "actor-card active"; // default standby
    }
}

// EXECUTE MANUALLY TYPED COMMANDS
async function executeCommand() {
    const cmdInput = document.getElementById("command-input");
    const cmd = cmdInput.value.trim();
    if (!cmd) return;
    
    cmdInput.value = "";
    
    // Append user input to logs
    appendLog(cmd, "user");
    
    try {
        const response = await fetch(`${API_BASE}/api/command`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: cmd })
        });
        
        const data = await response.json();
        if (response.ok) {
            appendLog(data.response, "system");
            speakTextBrowser(data.response);
            
            // If command asked to store something or create a tool, refresh panels
            if (cmd.toLowerCase().includes("remember") || cmd.toLowerCase().includes("memory")) {
                loadMemories();
            }
            if (cmd.toLowerCase().includes("tool") || cmd.toLowerCase().includes("create")) {
                loadTools();
            }
        } else {
            appendLog(`Execution Error: ${data.detail || "Server communication failed"}`, "error");
        }
    } catch (e) {
        appendLog(`Nervous link failure: ${e}`, "error");
    }
}

function appendLog(text, type) {
    const feed = document.getElementById("console-logs-feed");
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
    
    const entry = document.createElement("div");
    entry.className = `log-entry ${type}`;
    entry.innerHTML = `[${timestamp}] ${text}`;
    
    feed.appendChild(entry);
    feed.scrollTop = feed.scrollHeight;
}

// LONG-TERM MEMORY LOADING & MANAGEMENT
let localMemories = [];
async function loadMemories() {
    try {
        const response = await fetch(`${API_BASE}/api/memory`);
        if (!response.ok) return;
        
        const data = await response.json();
        localMemories = Object.entries(data.memories || {});
        renderMemoryTable(localMemories);
    } catch (e) {
        console.error("Failed to load memories:", e);
    }
}

function renderMemoryTable(memList) {
    const tbody = document.getElementById("memory-db-body");
    tbody.innerHTML = "";
    
    if (memList.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" class="empty-msg">No memories stored in database, sir.</td></tr>`;
        return;
    }
    
    memList.forEach(([key, val]) => {
        const tr = document.createElement("tr");
        
        const keyTd = document.createElement("td");
        keyTd.textContent = key;
        keyTd.title = key;
        
        const valTd = document.createElement("td");
        valTd.textContent = val;
        valTd.title = val;
        
        const actionTd = document.createElement("td");
        const delBtn = document.createElement("button");
        delBtn.className = "delete-mem-btn";
        delBtn.textContent = "DELETE";
        delBtn.onclick = () => deleteMemory(key);
        actionTd.appendChild(delBtn);
        
        tr.appendChild(keyTd);
        tr.appendChild(valTd);
        tr.appendChild(actionTd);
        tbody.appendChild(tr);
    });
}

async function deleteMemory(key) {
    if (!confirm(`Confirm deletion of memory fact for '${key}'?`)) return;
    try {
        const response = await fetch(`${API_BASE}/api/memory/${encodeURIComponent(key)}`, {
            method: "DELETE"
        });
        if (response.ok) {
            appendLog(`Deleted memory fact: '${key}', sir.`, "system");
            loadMemories();
        }
    } catch (e) {
        appendLog(`Failed to delete memory: ${e}`, "error");
    }
}

function filterMemories() {
    const query = document.getElementById("memory-search-input").value.toLowerCase().strip;
    const queryStr = document.getElementById("memory-search-input").value.trim().toLowerCase();
    
    const filtered = localMemories.filter(([key, val]) => {
        return key.includes(queryStr) || val.toLowerCase().includes(queryStr);
    });
    renderMemoryTable(filtered);
}

// TOOLS LIST MANAGEMENT
async function loadTools() {
    try {
        const response = await fetch(`${API_BASE}/api/tools`);
        if (!response.ok) return;
        
        const data = await response.json();
        const listContainer = document.getElementById("custom-tools-list");
        
        // Keep only built-in tools and clear others
        const builtins = listContainer.querySelectorAll(".tool-item.builtin");
        listContainer.innerHTML = "";
        builtins.forEach(b => listContainer.appendChild(b));
        
        // Add dynamic tools
        const customTools = data.custom_tools || [];
        customTools.forEach(tool => {
            const item = document.createElement("div");
            item.className = "tool-item custom";
            
            const name = document.createElement("div");
            name.className = "tool-name";
            name.textContent = `${tool.name} (Custom)`;
            
            const desc = document.createElement("div");
            desc.className = "tool-desc";
            desc.textContent = tool.description;
            
            item.appendChild(name);
            item.appendChild(desc);
            listContainer.appendChild(item);
        });
    } catch (e) {
        console.error("Failed to load tools:", e);
    }
}

// SOUNDWAVE SVG ANIMATION LOOP
function initSoundwave() {
    const wavePath = document.getElementById("wave-path");
    let t = 0;
    
    function animate() {
        t += 0.15;
        let points = [];
        let amp = 0;
        let freq = 0.05;
        
        if (currentStatus === "LISTENING") {
            amp = 18;  // Fast jagged mic capture waves
            freq = 0.22;
        } else if (currentStatus === "SPEAKING") {
            amp = 25;  // Broad smooth bass output waves
            freq = 0.10;
        } else {
            amp = 0;   // Standby flat state
        }
        
        for (let x = 10; x <= 390; x += 5) {
            // Apply sine logic based on time, amplitude, and wave position index
            let y = 50;
            if (amp > 0) {
                // Apply a gaussian-like envelope so waves taper down at the left and right edges
                const envelope = Math.exp(-Math.pow((x - 200) / 100, 2));
                y += Math.sin(x * freq + t) * amp * envelope;
            }
            points.push(`${x},${y}`);
        }
        
        wavePath.setAttribute("d", `M ${points.join(" L ")}`);
        requestAnimationFrame(animate);
    }
    
    animate();
}

// BROWSER SPEECH RECOGNITION AND SYNTHESIS SYSTEM
let recognitionInstance = null;
let speechVoicesLoaded = false;

function initBrowserSpeech() {
    const micBtn = document.getElementById("mic-btn");
    const cmdInput = document.getElementById("command-input");
    
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognitionInstance = new SpeechRecognition();
        recognitionInstance.continuous = false;
        recognitionInstance.interimResults = false;
        recognitionInstance.lang = 'en-US';
        
        recognitionInstance.onstart = () => {
            micBtn.classList.add("recording");
            const arcReactor = document.querySelector(".arc-reactor");
            if (arcReactor) arcReactor.setAttribute("data-status", "listening");
            const statusBox = document.getElementById("speaker-status");
            statusBox.textContent = "LISTENING";
            statusBox.className = "voice-status listening";
            currentStatus = "LISTENING";
        };
        
        recognitionInstance.onerror = (event) => {
            console.error("Speech recognition error", event.error);
            micBtn.classList.remove("recording");
            appendLog(`Voice error: ${event.error}`, "error");
        };
        
        recognitionInstance.onend = () => {
            micBtn.classList.remove("recording");
            setTimeout(() => {
                const arcReactor = document.querySelector(".arc-reactor");
                if (arcReactor && arcReactor.getAttribute("data-status") === "listening") {
                    arcReactor.setAttribute("data-status", "standby");
                }
                const statusBox = document.getElementById("speaker-status");
                if (statusBox.textContent === "LISTENING") {
                    statusBox.textContent = "STANDBY";
                    statusBox.className = "voice-status";
                    currentStatus = "STANDBY";
                }
            }, 600);
        };
        
        recognitionInstance.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            cmdInput.value = transcript;
            appendLog(`[Voice Input]: ${transcript}`, "user");
            executeCommand();
        };
        
        micBtn.addEventListener("click", () => {
            try {
                if (micBtn.classList.contains("recording")) {
                    recognitionInstance.stop();
                } else {
                    recognitionInstance.start();
                }
            } catch (e) {
                console.error("Recognition start failed", e);
            }
        });
    } else {
        micBtn.style.display = "none";
    }

    // Pre-load voices if speech synthesis is available
    if ('speechSynthesis' in window) {
        window.speechSynthesis.getVoices();
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = () => {
                speechVoicesLoaded = true;
            };
        }
    }
}

function speakTextBrowser(text) {
    if ('speechSynthesis' in window) {
        // Cancel any active speech
        window.speechSynthesis.cancel();
        
        // Strip markdown and link syntax
        let cleanText = text.replace(/\*\*|`|\*/g, "");
        cleanText = cleanText.replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1");
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        const voices = window.speechSynthesis.getVoices();
        // Look for Google US English, Microsoft David, or general natural English voices
        let selectedVoice = voices.find(v => v.lang.includes("en-US") && v.name.toLowerCase().includes("natural"));
        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.includes("en") && v.name.toLowerCase().includes("david"));
        }
        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.includes("en") && v.name.toLowerCase().includes("google"));
        }
        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.includes("en"));
        }
        
        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }
        utterance.rate = 1.05;
        
        utterance.onstart = () => {
            const arcReactor = document.querySelector(".arc-reactor");
            if (arcReactor) arcReactor.setAttribute("data-status", "speaking");
            const statusBox = document.getElementById("speaker-status");
            statusBox.textContent = "SPEAKING";
            statusBox.className = "voice-status speaking";
            currentStatus = "SPEAKING";
        };
        
        utterance.onend = () => {
            const arcReactor = document.querySelector(".arc-reactor");
            if (arcReactor && arcReactor.getAttribute("data-status") === "speaking") {
                arcReactor.setAttribute("data-status", "standby");
            }
            const statusBox = document.getElementById("speaker-status");
            if (statusBox.textContent === "SPEAKING") {
                statusBox.textContent = "STANDBY";
                statusBox.className = "voice-status";
                currentStatus = "STANDBY";
            }
        };
        
        window.speechSynthesis.speak(utterance);
    }
}
