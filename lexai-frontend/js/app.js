const chatMessages = document.getElementById('chat-messages');
const queryInput = document.getElementById('query-input');
const sendBtn = document.getElementById('send-btn');
const statusText = document.getElementById('status-text');
const backendStatus = document.getElementById('backend-status');
const metadataPanel = document.getElementById('metadata-panel');
const sourcesList = document.getElementById('sources-list');

const API_URL = 'http://localhost:5000/api';

// Check backend status
async function checkStatus() {
    try {
        const response = await fetch(`${API_URL}/status`);
        const data = await response.json();
        if (data.status === 'ready') {
            statusText.innerText = 'Online';
            backendStatus.classList.add('online');
        } else {
            statusText.innerText = 'Initializing...';
        }
    } catch (err) {
        statusText.innerText = 'Offline';
        backendStatus.classList.remove('online');
    }
}

setInterval(checkStatus, 5000);
checkStatus();

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.classList.add('message', sender);
    
    // Simple markdown-ish bold support
    const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    div.innerHTML = `<p>${formattedText.replace(/\n/g, '<br>')}</p>`;
    
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function handleQuery() {
    const question = queryInput.value.trim();
    if (!question) return;

    queryInput.value = '';
    addMessage(question, 'user');

    // Loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('message', 'ai', 'loading');
    loadingDiv.innerHTML = '<p>Analyzing contracts...</p>';
    chatMessages.appendChild(loadingDiv);

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const result = await response.json();
        chatMessages.removeChild(loadingDiv);

        if (result.error) {
            addMessage(`Error: ${result.error}`, 'ai');
        } else {
            addMessage(result.answer, 'ai');
            displaySources(result.sources);
        }
    } catch (err) {
        chatMessages.removeChild(loadingDiv);
        addMessage("Sorry, I couldn't connect to the legal engine. Please make sure the backend is running.", "ai");
    }
}

function displaySources(sources) {
    if (!sources || sources.length === 0) {
        metadataPanel.style.display = 'none';
        return;
    }

    metadataPanel.style.display = 'block';
    sourcesList.innerHTML = '';

    sources.forEach(source => {
        const item = document.createElement('div');
        item.classList.add('source-item');
        item.innerHTML = `
            <h4>${source.name}</h4>
            <p>Chunk Index: ${source.idx}</p>
            <span class="badge">Relevance: ${(source.score * 100).toFixed(1)}%</span>
        `;
        sourcesList.appendChild(item);
    });
}

sendBtn.addEventListener('click', handleQuery);
queryInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleQuery();
});
