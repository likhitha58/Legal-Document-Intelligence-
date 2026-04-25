const chatMessages = document.getElementById('chat-messages');
const queryInput = document.getElementById('query-input');
const sendBtn = document.getElementById('send-btn');
const statusText = document.getElementById('status-text');
const backendStatus = document.getElementById('backend-status');
const metadataPanel = document.getElementById('metadata-panel');
const sourcesList = document.getElementById('sources-list');
const uploadBtn = document.getElementById('upload-btn');
const uploadInput = document.getElementById('upload-input');
const uploadStatus = document.getElementById('upload-status');
const activeDocBadge = document.getElementById('active-doc-badge');
const activeDocName = document.getElementById('active-doc-name');
const clearDocBtn = document.getElementById('clear-doc-btn');

const API_URL = 'http://localhost:5000/api';
const DEFAULT_PLACEHOLDER = 'Ask anything about the contracts...';

let activeDocId = null;
let activeDocFilename = '';

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

function setQueryPlaceholder() {
    if (activeDocFilename) {
        queryInput.placeholder = `Ask anything about ${activeDocFilename}...`;
    } else {
        queryInput.placeholder = DEFAULT_PLACEHOLDER;
    }
}

function showUploadStatus(message, isError = false) {
    if (!uploadStatus) return;
    uploadStatus.textContent = message;
    uploadStatus.classList.toggle('error', isError);
}

function setActiveDocument(docId, docName) {
    activeDocId = docId;
    activeDocFilename = docName || '';
    if (activeDocId && activeDocFilename) {
        activeDocName.textContent = activeDocFilename;
        activeDocBadge.style.display = 'inline-flex';
        showUploadStatus(`Indexed ${activeDocFilename}`);
    } else {
        activeDocName.textContent = '';
        activeDocBadge.style.display = 'none';
        showUploadStatus('');
    }
    setQueryPlaceholder();
}

async function handleUpload(file) {
    if (!file) return;

    showUploadStatus('Indexing document...');
    uploadBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (!response.ok || result.error) {
            showUploadStatus(result.error || 'Upload failed', true);
            return;
        }

        setActiveDocument(result.doc_id, result.doc_name);
    } catch (err) {
        showUploadStatus('Could not upload document. Check backend connection.', true);
    } finally {
        uploadBtn.disabled = false;
        uploadInput.value = '';
    }
}

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
            body: JSON.stringify({
                question,
                ...(activeDocId ? { doc_id: activeDocId } : {})
            })
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

uploadBtn.addEventListener('click', () => {
    uploadInput.click();
});

uploadInput.addEventListener('change', (e) => {
    const file = e.target.files && e.target.files[0];
    handleUpload(file);
});

clearDocBtn.addEventListener('click', () => {
    setActiveDocument(null, '');
    showUploadStatus('Switched to global CUAD search.');
});

setQueryPlaceholder();
