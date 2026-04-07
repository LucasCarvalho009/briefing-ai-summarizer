// Configuração da API
const API_URL = 'http://localhost:8000';

// Estado da aplicação
let currentFile = null;
let apiHealthy = false;

// Elementos DOM
const elements = {
    // Tabs
    tabButtons: document.querySelectorAll('.tab-button'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Text input
    textInput: document.getElementById('text-input'),
    charCount: document.getElementById('char-count'),
    
    // File upload
    uploadArea: document.getElementById('upload-area'),
    fileInput: document.getElementById('file-input'),
    filePreview: document.getElementById('file-preview'),
    fileName: document.getElementById('file-name'),
    fileSize: document.getElementById('file-size'),
    removeFileBtn: document.getElementById('remove-file'),
    
    // Actions
    summarizeBtn: document.getElementById('summarize-btn'),
    newSummaryBtn: document.getElementById('new-summary-btn'),
    copyAllBtn: document.getElementById('copy-all-btn'),
    retryBtn: document.getElementById('retry-btn'),
    
    // Sections
    inputSection: document.querySelector('.input-section'),
    loadingSection: document.getElementById('loading-section'),
    resultsSection: document.getElementById('results-section'),
    errorSection: document.getElementById('error-section'),
    
    // Results
    methodBadge: document.getElementById('method-badge'),
    summaryText: document.getElementById('summary-text'),
    bulletPoints: document.getElementById('bullet-points'),
    errorMessage: document.getElementById('error-message'),
    
    // Footer
    apiStatus: document.getElementById('api-status'),
    apiStatusText: document.getElementById('api-status-text'),
    
    // Toast
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toast-message')
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeTextInput();
    initializeFileUpload();
    initializeButtons();
    checkAPIHealth();
});

// ===== TABS =====
function initializeTabs() {
    elements.tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Atualizar botões
    elements.tabButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Atualizar conteúdo
    elements.tabContents.forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
    
    // Limpar estado
    resetInput();
}

// ===== TEXT INPUT =====
function initializeTextInput() {
    elements.textInput.addEventListener('input', updateCharCount);
    updateCharCount();
}

function updateCharCount() {
    const count = elements.textInput.value.length;
    elements.charCount.textContent = count;
    
    // Mudar cor baseado no comprimento
    if (count < 50) {
        elements.charCount.style.color = 'var(--error-color)';
    } else if (count < 100) {
        elements.charCount.style.color = 'var(--warning-color)';
    } else {
        elements.charCount.style.color = 'var(--success-color)';
    }
}

// ===== FILE UPLOAD =====
function initializeFileUpload() {
    // Click para selecionar arquivo
    elements.uploadArea.addEventListener('click', () => {
        elements.fileInput.click();
    });
    
    // Mudança de arquivo
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleDrop);
    
    // Remover arquivo
    elements.removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        removeFile();
    });
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        validateAndSetFile(file);
    }
}

function handleDragOver(e) {
    e.preventDefault();
    elements.uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    if (file) {
        validateAndSetFile(file);
    }
}

function validateAndSetFile(file) {
    // Validar tipo
    const validTypes = ['application/pdf', 'text/plain'];
    if (!validTypes.includes(file.type)) {
        showToast('Formato não suportado. Use PDF ou TXT.', 'error');
        return;
    }
    
    // Validar tamanho (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('Arquivo muito grande. Máximo: 10MB', 'error');
        return;
    }
    
    currentFile = file;
    showFilePreview(file);
}

function showFilePreview(file) {
    elements.uploadArea.style.display = 'none';
    elements.filePreview.style.display = 'block';
    
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);
}

function removeFile() {
    currentFile = null;
    elements.fileInput.value = '';
    elements.uploadArea.style.display = 'block';
    elements.filePreview.style.display = 'none';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ===== BUTTONS =====
function initializeButtons() {
    elements.summarizeBtn.addEventListener('click', handleSummarize);
    elements.newSummaryBtn.addEventListener('click', resetApp);
    elements.copyAllBtn.addEventListener('click', copyAllResults);
    elements.retryBtn.addEventListener('click', handleSummarize);
    
    // Copy buttons
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const type = e.currentTarget.dataset.copy;
            copyToClipboard(type);
        });
    });
}

// ===== SUMMARIZE =====
async function handleSummarize() {
    // Validar entrada
    const activeTab = document.querySelector('.tab-button.active').dataset.tab;
    
    if (activeTab === 'text') {
        const text = elements.textInput.value.trim();
        if (text.length < 50) {
            showToast('Texto muito curto. Mínimo: 50 caracteres', 'error');
            return;
        }
        await summarizeText(text);
    } else {
        if (!currentFile) {
            showToast('Selecione um arquivo primeiro', 'error');
            return;
        }
        await summarizeFile(currentFile);
    }
}

async function summarizeText(text) {
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('text', text);
        
        const response = await fetch(`${API_URL}/summarize`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao processar texto');
        }
        
        const result = await response.json();
        showResults(result);
        
    } catch (error) {
        showError(error.message);
    }
}

async function summarizeFile(file) {
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_URL}/summarize`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao processar arquivo');
        }
        
        const result = await response.json();
        showResults(result);
        
    } catch (error) {
        showError(error.message);
    }
}

// ===== UI STATES =====
function showLoading() {
    elements.inputSection.style.display = 'none';
    elements.resultsSection.style.display = 'none';
    elements.errorSection.style.display = 'none';
    elements.loadingSection.style.display = 'block';
}

function showResults(result) {
    elements.loadingSection.style.display = 'none';
    elements.errorSection.style.display = 'none';
    elements.resultsSection.style.display = 'block';
    
    // Atualizar badge do método
    elements.methodBadge.textContent = result.method === 'ai' ? '🤖 IA' : '⚡ Fallback';
    elements.methodBadge.className = `method-badge ${result.method}`;
    
    // Atualizar resumo
    elements.summaryText.textContent = result.summary;
    
    // Atualizar bullet points
    elements.bulletPoints.innerHTML = '';
    result.bullet_points.forEach(point => {
        const li = document.createElement('li');
        li.textContent = point;
        elements.bulletPoints.appendChild(li);
    });
    
    showToast('Resumo gerado com sucesso!', 'success');
}

function showError(message) {
    elements.loadingSection.style.display = 'none';
    elements.resultsSection.style.display = 'none';
    elements.errorSection.style.display = 'block';
    
    elements.errorMessage.textContent = message;
}

function resetApp() {
    elements.resultsSection.style.display = 'none';
    elements.errorSection.style.display = 'none';
    elements.inputSection.style.display = 'block';
    
    resetInput();
}

function resetInput() {
    elements.textInput.value = '';
    updateCharCount();
    removeFile();
}

// ===== COPY FUNCTIONS =====
function copyToClipboard(type) {
    let text = '';
    
    if (type === 'summary') {
        text = elements.summaryText.textContent;
    } else if (type === 'bullets') {
        const bullets = Array.from(elements.bulletPoints.children)
            .map(li => '• ' + li.textContent)
            .join('\n');
        text = bullets;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copiado para a área de transferência!', 'success');
    }).catch(() => {
        showToast('Erro ao copiar', 'error');
    });
}

function copyAllResults() {
    const summary = elements.summaryText.textContent;
    const bullets = Array.from(elements.bulletPoints.children)
        .map(li => '• ' + li.textContent)
        .join('\n');
    
    const text = `RESUMO:\n${summary}\n\nPONTOS-CHAVE:\n${bullets}`;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Tudo copiado para a área de transferência!', 'success');
    }).catch(() => {
        showToast('Erro ao copiar', 'error');
    });
}

// ===== API HEALTH CHECK =====
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        
        if (response.ok) {
            const data = await response.json();
            apiHealthy = true;
            elements.apiStatus.textContent = '🟢';
            elements.apiStatusText.textContent = 'Online';
            
            // Mostrar informação do modelo
            if (data.model_status) {
                const modelInfo = data.model_status.using_fallback ? 
                    'Fallback' : 'IA Carregada';
                elements.apiStatusText.textContent = `Online (${modelInfo})`;
            }
        } else {
            throw new Error('API não respondeu');
        }
    } catch (error) {
        apiHealthy = false;
        elements.apiStatus.textContent = '🔴';
        elements.apiStatusText.textContent = 'Offline';
        console.error('Erro ao verificar API:', error);
    }
}

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info') {
    elements.toastMessage.textContent = message;
    elements.toast.className = `toast ${type}`;
    elements.toast.style.display = 'block';
    
    setTimeout(() => {
        elements.toast.style.display = 'none';
    }, 3000);
}

// Verificar API a cada 30 segundos
setInterval(checkAPIHealth, 30000);

// Made with Bob
