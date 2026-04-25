// ============================================================
// MOCK DATA — Replace with real API calls in production
// ============================================================

const MOCK_USER = {
  name: "Alex Johnson",
  email: "alex.johnson@lawfirm.com",
  organization: "Johnson & Partners LLP",
  role: "Legal Tech Associate",
  plan: "free",
  memberSince: "January 2025",
  totalDocuments: 12,
  totalQueries: 89
};

const MOCK_DOCUMENTS = [
  { id: 1, name: "Software_License_Agreement_2024.pdf", size: "2.4 MB", uploadDate: "Jan 15, 2025", clauses: 23, queries: 12, status: "processed" },
  { id: 2, name: "Employment_Contract_TechCorp.pdf", size: "1.1 MB", uploadDate: "Jan 10, 2025", clauses: 18, queries: 5, status: "processed" },
  { id: 3, name: "NDA_Acme_Corp_2025.pdf", size: "0.8 MB", uploadDate: "Jan 5, 2025", clauses: 12, queries: 3, status: "processed" },
  { id: 4, name: "Partnership_Agreement_Draft.pdf", size: "3.2 MB", uploadDate: "Dec 28, 2024", clauses: 0, queries: 0, status: "failed" },
  { id: 5, name: "Vendor_Agreement_Q4.pdf", size: "1.9 MB", uploadDate: "Dec 20, 2024", clauses: 27, queries: 8, status: "processed" }
];

const MOCK_STATS = {
  totalDocuments: 12,
  clausesDetected: 347,
  queriesMade: 89,
  contractsReviewed: 8
};

const MOCK_CLAUSES = [
  { type: "Termination", count: 4, confidence: 0.94, color: "#DDEEFF", border: "#2C5F9E", keywords: ["terminate", "termination", "expire"], className: "clause-termination" },
  { type: "Confidentiality", count: 6, confidence: 0.91, color: "#DFFFD6", border: "#2E7D5B", keywords: ["confidential", "non-disclosure", "secret"], className: "clause-confidentiality" },
  { type: "Payment Terms", count: 3, confidence: 0.88, color: "#FFF8DC", border: "#D4A843", keywords: ["payment", "fee", "compensation"], className: "clause-payment" },
  { type: "Governing Law", count: 2, confidence: 0.97, color: "#EDE0FF", border: "#7B2FC0", keywords: ["governing law", "jurisdiction"], className: "clause-governing-law" },
  { type: "Indemnification", count: 2, confidence: 0.85, color: "#FFE0E0", border: "#C0392B", keywords: ["indemnify", "hold harmless"], className: "clause-indemnification" },
  { type: "Warranties", count: 3, confidence: 0.82, color: "#FFE8CC", border: "#D4700A", keywords: ["warrant", "warranty"], className: "clause-warranty" },
  { type: "Assignment", count: 1, confidence: 0.79, color: "#E0F7FA", border: "#0097A7", keywords: ["assign", "transfer"], className: "clause-assignment" },
  { type: "Data Protection", count: 2, confidence: 0.90, color: "#E8EAF6", border: "#3F51B5", keywords: ["gdpr", "personal data", "privacy"], className: "clause-data-protection" }
];

const MOCK_ENTITIES = [
  { type: "PERSON", count: 3, examples: ["John Smith", "Sarah Lee", "Michael Chen"] },
  { type: "ORG", count: 5, examples: ["Acme Corp", "TechSoft Inc", "LexAI Solutions"] },
  { type: "DATE", count: 8, examples: ["January 1, 2024", "30 days", "fiscal year 2025"] },
  { type: "GPE", count: 2, examples: ["California", "United States"] },
  { type: "MONEY", count: 4, examples: ["$50,000", "$200 per hour", "$10,000,000"] }
];

const MOCK_QA_RESPONSES = {
  "termination": {
    answer: "The contract specifies the following termination conditions:\n\n• Either party may terminate with 30 days written notice.\n• Immediate termination is allowed in case of material breach.\n• Termination is effective upon receipt of written notice.",
    sources: [
      { name: "Software_License_Agreement_2024.pdf", chunk: 4, score: 0.923 },
      { name: "Software_License_Agreement_2024.pdf", chunk: 7, score: 0.841 }
    ],
    latency: "1.2s",
    backend: "Gemini 2.0 Flash"
  },
  "governing law": {
    answer: "This agreement is governed by the laws of the State of California, United States, without regard to its conflict of law provisions. Disputes shall be resolved in the courts of San Francisco County.",
    sources: [
      { name: "Software_License_Agreement_2024.pdf", chunk: 12, score: 0.971 },
      { name: "Software_License_Agreement_2024.pdf", chunk: 15, score: 0.812 }
    ],
    latency: "0.9s",
    backend: "Gemini 2.0 Flash"
  },
  "default": {
    answer: "Based on the provided contract excerpts, the relevant information indicates that the parties have agreed to specific terms outlined in Section 3 of the agreement. The contract contains standard provisions that would apply to this query.",
    sources: [
      { name: "Software_License_Agreement_2024.pdf", chunk: 2, score: 0.754 },
      { name: "Software_License_Agreement_2024.pdf", chunk: 9, score: 0.612 }
    ],
    latency: "1.5s",
    backend: "Gemini 2.0 Flash"
  }
};

const MOCK_DUMMY_CONTRACT_TEXT = `
SOFTWARE LICENSE AGREEMENT

This Software License Agreement ("Agreement") is entered into as of January 1, 2024, 
by and between TechSoft Inc., a Delaware corporation ("Licensor"), and Acme Corp, 
a California corporation ("Licensee").

1. GRANT OF LICENSE
Licensor hereby grants to Licensee a non-exclusive, non-transferable, limited license 
to use the Software solely for Licensee's internal business purposes...

2. CONFIDENTIALITY
<span class="clause-confidentiality" data-bs-toggle="tooltip" data-bs-title="Confidence: 91% | Keyword: 'confidentiality'">Each party agrees to maintain the confidentiality of the other party's proprietary 
information and not to disclose such information to third parties without prior 
written consent. This obligation of confidentiality shall survive the termination 
of this Agreement for a period of five (5) years...</span>

3. PAYMENT TERMS
<span class="clause-payment" data-bs-toggle="tooltip" data-bs-title="Confidence: 88% | Keyword: 'payment'">Licensee agrees to pay Licensor a license fee of $50,000 per year, payable in 
advance on the first day of each calendar year. Late payments shall incur interest 
at the rate of 1.5% per month...</span>

4. TERMINATION
<span class="clause-termination" data-bs-toggle="tooltip" data-bs-title="Confidence: 94% | Keyword: 'termination'">Either party may terminate this Agreement upon thirty (30) days written notice 
to the other party. Licensor may terminate this Agreement immediately upon written 
notice if Licensee breaches any material term of this Agreement...</span>

5. GOVERNING LAW
<span class="clause-governing-law" data-bs-toggle="tooltip" data-bs-title="Confidence: 97% | Keyword: 'governing law'">This Agreement shall be governed by and construed in accordance with the laws of 
the State of California, without regard to its conflict of law provisions. Any 
disputes arising hereunder shall be resolved in the courts of San Francisco County...</span>

6. INDEMNIFICATION
<span class="clause-indemnification" data-bs-toggle="tooltip" data-bs-title="Confidence: 85% | Keyword: 'indemnify'">Licensee shall indemnify, defend, and hold harmless Licensor and its officers, 
directors, employees, and agents from any claims, damages, liabilities, costs, 
and expenses arising from Licensee's use of the Software...</span>

7. WARRANTIES
<span class="clause-warranty" data-bs-toggle="tooltip" data-bs-title="Confidence: 82% | Keyword: 'warrants'">Licensor warrants that the Software will perform substantially in accordance with 
the documentation for a period of ninety (90) days from delivery. EXCEPT FOR THE 
FOREGOING, THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND...</span>
`;

// ============================================================
// APP LOGIC
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  // 0. Check Auth
  checkAuthAndLoadUser();

  // 1. Sidebar Active State
  setActiveSidebarItem();

  // 2. Initialize Bootstrap Tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

  // 3. Setup form handles
  setupForms();

  // 4. Setup Upload Drag & Drop
  if (document.getElementById('drop-zone')) {
    initDragDrop();
  }

  // 5. Setup Processing Page logic
  if (document.getElementById('processing-steps')) {
    startProcessingSimulation();
  }

  // 6. QA Chat logic
  if (document.getElementById('chat-input')) {
    setupChat();
  }

  // 7. Inject mock data if on dashboard
  populateDashboard();
  
  // 8. Inject dummy document text
  if (document.getElementById('document-text-container')) {
    document.getElementById('document-text-container').innerHTML = MOCK_DUMMY_CONTRACT_TEXT;
  }
});

function setActiveSidebarItem() {
  const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
  document.querySelectorAll('.sidebar-nav-item').forEach(item => {
    // exact match or simple includes for the specific page
    if (item.getAttribute('href') && item.getAttribute('href').includes(currentPage)) {
      item.classList.add('active');
    }
  });
}

function setupForms() {
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      
      const email = document.getElementById('login-email').value;
      const pwd = document.getElementById('login-password').value;
      
      const storedUserJSON = localStorage.getItem('lexai_user');
      if (!storedUserJSON) {
        alert("No account found. Please register first.");
        return;
      }
      
      const storedUser = JSON.parse(storedUserJSON);
      if (storedUser.email !== email || storedUser.password !== pwd) {
        alert("Invalid email or password.");
        return;
      }

      const btn = document.getElementById('login-btn');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Signing In...';
      btn.disabled = true;
      setTimeout(() => {
        window.location.href = 'dashboard/dashboard.html';
      }, 1500);
    });
  }

  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    const pwdInput = document.getElementById('reg-password');
    if (pwdInput) {
      pwdInput.addEventListener('input', (e) => checkPasswordStrength(e.target.value));
    }
    
    // Remove native validation to handle it manually with alerts
    registerForm.setAttribute('novalidate', true);
    
    registerForm.addEventListener('submit', (e) => {
      e.preventDefault();
      
      // Manual Validation
      const inputs = registerForm.querySelectorAll('input[required]');
      let isValid = true;
      inputs.forEach(input => {
        if (!input.value && input.type !== 'checkbox') {
          isValid = false;
        }
      });
      
      if (!isValid) {
        alert("Please fill out all required fields (Name, Email, Password).");
        return;
      }
      
      const termsCheckbox = document.getElementById('terms');
      if (termsCheckbox && !termsCheckbox.checked) {
        alert("Please agree to the Terms of Service and Privacy Policy.");
        return;
      }

      const pwd = document.getElementById('reg-password').value;
      const confirmPwd = document.getElementById('reg-confirm-password').value;
      
      if (pwd !== confirmPwd) {
        alert("Passwords do not match. Please try again.");
        return;
      }
      
      const btn = document.getElementById('register-btn');
      btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating Account...';
      btn.disabled = true;
      
      const name = document.getElementById('reg-name').value;
      const email = document.getElementById('reg-email').value;
      
      localStorage.setItem('lexai_user', JSON.stringify({
        name: name,
        email: email,
        password: pwd
      }));
      
      setTimeout(() => {
        alert("Account created successfully!");
        window.location.href = 'dashboard/dashboard.html';
      }, 2000);
    });
  }
}

function checkPasswordStrength(password) {
  let strength = 0;
  if (password.length >= 8) strength++;
  if (/[A-Z]/.test(password)) strength++;
  if (/[0-9]/.test(password)) strength++;
  if (/[^A-Za-z0-9]/.test(password)) strength++;
  
  const bar = document.getElementById('password-strength-fill');
  if (!bar) return;
  
  if (strength === 0) {
    bar.style.width = '0%';
    bar.style.backgroundColor = 'transparent';
  } else if (strength <= 2) {
    bar.style.width = '33%';
    bar.style.backgroundColor = 'var(--danger)';
  } else if (strength === 3) {
    bar.style.width = '66%';
    bar.style.backgroundColor = 'var(--accent)';
  } else {
    bar.style.width = '100%';
    bar.style.backgroundColor = 'var(--success)';
  }
}

function initDragDrop() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-upload');

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
  });

  dropZone.addEventListener('drop', handleDrop, false);
  dropZone.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', function() {
    if (this.files.length > 0) {
      showFilePreview(this.files[0]);
    }
  });

  function handleDrop(e) {
    let dt = e.dataTransfer;
    let files = dt.files;
    if (files.length > 0) {
      showFilePreview(files[0]);
    }
  }

  function showFilePreview(file) {
    const previewContainer = document.getElementById('file-preview');
    if (previewContainer) {
      previewContainer.innerHTML = `
        <div class="card p-3 d-flex flex-row align-items-center justify-content-between">
          <div class="d-flex align-items-center gap-3">
            <i class="bi bi-file-earmark-pdf fs-2 text-danger"></i>
            <div>
              <h6 class="mb-0">${file.name}</h6>
              <small class="text-muted">${(file.size / 1024 / 1024).toFixed(2)} MB</small>
            </div>
          </div>
          <button class="btn btn-sm btn-outline-danger" onclick="document.getElementById('file-preview').innerHTML=''">×</button>
        </div>
      `;
    }
  }

  const processBtn = document.getElementById('btn-process');
  if (processBtn) {
    processBtn.addEventListener('click', () => {
      setTimeout(() => { window.location.href = 'processing.html'; }, 500);
    });
  }
}

const processingSteps = [
  { id: 'step-1', label: 'Document Uploaded Successfully' },
  { id: 'step-2', label: 'Text Extracted (14,280 characters)' },
  { id: 'step-3', label: 'Detecting Legal Clauses...' },
  { id: 'step-4', label: 'Running Named Entity Recognition' },
  { id: 'step-5', label: 'Generating Semantic Embeddings' }
];

let currentProcessingStep = 0;

function startProcessingSimulation() {
  setTimeout(advanceProcessingStep, 2000);
}

function advanceProcessingStep() {
  const container = document.getElementById('processing-steps');
  const progressBar = document.getElementById('processing-progress-bar');
  const progressLabel = document.getElementById('processing-progress-label');
  
  if (!container) return;

  // Mark current as complete
  const prevStepEl = document.getElementById(\`step-\${currentProcessingStep}\`);
  if (prevStepEl) {
    prevStepEl.classList.remove('active');
    prevStepEl.classList.add('completed');
    prevStepEl.innerHTML = \`<i class="bi bi-check-circle-fill text-success step-icon"></i> <span>\${processingSteps[currentProcessingStep].label}</span>\`;
  }

  currentProcessingStep++;
  
  if (currentProcessingStep < processingSteps.length) {
    // Activate next
    const stepEl = document.getElementById(\`step-\${currentProcessingStep}\`);
    if (stepEl) {
      stepEl.classList.add('active');
      stepEl.innerHTML = \`<div class="lex-spinner-sm me-2"></div> <span class="fw-bold">\${processingSteps[currentProcessingStep].label}</span>\`;
    }
    
    // Update progress
    const pct = ((currentProcessingStep) / processingSteps.length) * 100;
    progressBar.style.width = \`\${pct}%\`;
    progressBar.setAttribute('aria-valuenow', pct);
    progressLabel.innerText = \`Processing Step \${currentProcessingStep + 1} of \${processingSteps.length}\`;
    
    setTimeout(advanceProcessingStep, 2000);
  } else {
    // Finish
    progressBar.style.width = '100%';
    progressBar.classList.remove('progress-bar-animated');
    progressBar.classList.add('bg-success');
    progressLabel.innerText = 'Completed!';
    
    document.getElementById('processing-status-heading').innerText = '✅ Document Processed Successfully!';
    document.getElementById('processing-spinner').style.display = 'none';
    
    const actions = document.getElementById('processing-actions');
    actions.style.display = 'flex';
    
    let countdown = 3;
    const btn = document.getElementById('auto-redirect-btn');
    const interval = setInterval(() => {
      countdown--;
      btn.innerText = \`View Document (\${countdown}s) →\`;
      if (countdown <= 0) {
        clearInterval(interval);
        window.location.href = 'document-viewer.html';
      }
    }, 1000);
  }
}

function setupChat() {
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');
  const chatMessages = document.getElementById('chat-messages');

  function sendMessage(question) {
    if (!question.trim()) return;
    
    // Append user msg
    const userHtml = \`
      <div class="chat-bubble chat-bubble-user page-fade">
        \${question}
      </div>
      <div class="clearfix"></div>
    \`;
    chatMessages.insertAdjacentHTML('beforeend', userHtml);
    chatInput.value = '';
    scrollToBottom();

    // Show typing
    const typingId = 'typing-' + Date.now();
    const typingHtml = \`
      <div id="\${typingId}" class="chat-bubble chat-bubble-ai page-fade" style="width: auto;">
        <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
      </div>
      <div class="clearfix"></div>
    \`;
    chatMessages.insertAdjacentHTML('beforeend', typingHtml);
    scrollToBottom();

    setTimeout(() => {
      document.getElementById(typingId).parentElement.remove(); // remove typing + clearfix
      const response = getAIResponse(question);
      
      let sourcesHtml = '';
      if (response.sources && response.sources.length > 0) {
        sourcesHtml = '<div class="mt-3"><small class="text-muted fw-bold">📄 Sources:</small>';
        response.sources.forEach((src, idx) => {
          const w = src.score * 100;
          sourcesHtml += \`
            <div class="source-card">
              <div class="d-flex justify-content-between">
                <span>Source \${idx + 1}: \${src.name}</span>
                <span>Chunk #\${src.chunk}</span>
              </div>
              <div class="d-flex align-items-center mt-1">
                <span class="me-2" style="font-size:0.75rem;">Relevance: \${src.score.toFixed(3)}</span>
                <div class="relevance-bar flex-grow-1"><div class="relevance-fill" style="width: \${w}%"></div></div>
              </div>
              <a href="#" class="text-decoration-none small mt-1 d-block">View Chunk →</a>
            </div>
          \`;
        });
        sourcesHtml += '</div>';
      }

      const aiHtml = \`
        <div class="chat-bubble chat-bubble-ai page-fade">
          <div class="fw-bold mb-2">🤖 LexAI Answer</div>
          <div>\${response.answer.replace(/\\n/g, '<br>')}</div>
          \${sourcesHtml}
          <div class="text-muted small mt-3 border-top pt-2">
            ⏱ Generated in \${response.latency} | Backend: \${response.backend}
          </div>
        </div>
        <div class="clearfix"></div>
      \`;
      chatMessages.insertAdjacentHTML('beforeend', aiHtml);
      scrollToBottom();
    }, 2000);
  }

  function getAIResponse(question) {
    const q = question.toLowerCase();
    if (q.includes('terminat')) return MOCK_QA_RESPONSES.termination;
    if (q.includes('govern') || q.includes('law')) return MOCK_QA_RESPONSES['governing law'];
    return MOCK_QA_RESPONSES.default;
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  sendBtn.addEventListener('click', () => sendMessage(chatInput.value));
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage(chatInput.value);
  });

  // chips
  document.querySelectorAll('.chat-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      chatInput.value = chip.innerText;
      sendMessage(chip.innerText);
    });
  });
}

function toggleClause(clauseTypeClass, isActive) {
  const elements = document.querySelectorAll('.' + clauseTypeClass);
  const clauseInfo = MOCK_CLAUSES.find(c => c.className === clauseTypeClass);
  
  elements.forEach(el => {
    if (isActive) {
      el.style.backgroundColor = clauseInfo.color;
      el.style.borderBottom = \`2px solid \${clauseInfo.border}\`;
    } else {
      el.style.backgroundColor = 'transparent';
      el.style.borderBottom = 'none';
    }
  });
}

// Ensure global access for inline onclicks
window.toggleClause = toggleClause;

function populateDashboard() {
  if (document.getElementById('docs-table-body')) {
    const tbody = document.getElementById('docs-table-body');
    let html = '';
    MOCK_DOCUMENTS.forEach(doc => {
      let badgeClass = 'status-processed';
      let statusText = 'Processed';
      if (doc.status === 'failed') { badgeClass = 'status-failed'; statusText = 'Failed'; }
      html += \`
        <tr>
          <td>\${doc.name}</td>
          <td>\${doc.uploadDate}</td>
          <td><span class="badge badge-pill \${badgeClass}">\${statusText}</span></td>
          <td>\${doc.clauses}</td>
          <td>
            <a href="document-viewer.html" class="btn btn-sm btn-outline-primary">View</a>
            <a href="qa-chat.html" class="btn btn-sm btn-primary">Ask AI</a>
          </td>
        </tr>
      \`;
    });
    tbody.innerHTML = html;
  }
}

// ============================================================
// AUTHENTICATION LOGIC
// ============================================================

function checkAuthAndLoadUser() {
  const isDashboardPage = window.location.pathname.includes('dashboard/');
  const storedUserJSON = localStorage.getItem('lexai_user');
  
  if (isDashboardPage && !storedUserJSON) {
    window.location.href = '../login.html';
    return;
  }
  
  if (storedUserJSON) {
    const user = JSON.parse(storedUserJSON);
    const firstName = user.name.split(' ')[0] || user.name;
    const initials = user.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    
    // Update dashboard UI elements
    const nameEls = document.querySelectorAll('.sidebar-user-name');
    nameEls.forEach(el => { el.innerText = user.name; });
    
    const avatarEls = document.querySelectorAll('.sidebar-avatar');
    avatarEls.forEach(el => { el.innerText = initials; });
    
    const welcomeEl = document.getElementById('welcome-user-name');
    if (welcomeEl) {
      welcomeEl.innerText = `Good morning, ${firstName} 👋`;
    }
  }
  
  // Setup logout logic
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      localStorage.removeItem('lexai_user');
      window.location.href = '../login.html';
    });
  }
}
