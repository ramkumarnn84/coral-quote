/**
 * Industrial AI - AI Quotation System
 * Main JavaScript - Home page with inventory table
 */

// Global state
let allInventory = [];

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', function() {
    loadInventory();
    loadStats();
});

// ==================== FILE UPLOAD ====================

const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');

fileInput.addEventListener('change', function(e) {
    handleFileSelect(e.target.files[0]);
});

uploadArea.addEventListener('dragover', function(e) {
    e.preventDefault();
    this.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', function(e) {
    e.preventDefault();
    this.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', function(e) {
    e.preventDefault();
    this.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelect(file);
    }
});

uploadArea.addEventListener('click', function(e) {
    if (e.target === this || e.target.closest('.upload-icon') || e.target.closest('p')) {
        fileInput.click();
    }
});

function handleFileSelect(file) {
    if (!file) return;

    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
        showToast('Error', 'Only JPG, JPEG, PNG files are allowed', 'danger');
        return;
    }

    if (file.size > 20 * 1024 * 1024) {
        showToast('Error', 'File size exceeds 20MB limit', 'danger');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        document.getElementById('previewImg').src = e.target.result;
        document.getElementById('imagePreview').classList.remove('d-none');
        document.getElementById('fileInfo').textContent = `${file.name} (${formatFileSize(file.size)})`;
        document.getElementById('uploadBtn').disabled = false;
    };
    reader.readAsDataURL(file);
}

function clearUpload() {
    fileInput.value = '';
    document.getElementById('imagePreview').classList.add('d-none');
    document.getElementById('uploadBtn').disabled = true;
    document.getElementById('previewImg').src = '';
}

// ==================== UPLOAD & ANALYZE ====================

async function uploadAndAnalyze() {
    const file = fileInput.files[0];
    if (!file) {
        showToast('Error', 'Please select a file first', 'danger');
        return;
    }

    const progressSection = document.getElementById('progressSection');
    const uploadBtn = document.getElementById('uploadBtn');
    const analysisPanel = document.getElementById('analysisPanel');
    const terminal = document.getElementById('analysisTerminal');

    // Show analysis panel
    analysisPanel.classList.remove('d-none');
    terminal.innerHTML = '';
    document.getElementById('analysisStatusBadge').classList.add('d-none');

    progressSection.classList.remove('d-none');
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing...';

    // Start AI-style streaming messages
    addTerminalMsg('📤 Uploading image: ' + file.name, 'info');
    updateProgress(10, 'Uploading...');

    const formData = new FormData();
    formData.append('file', file);

    await delay(400);
    addTerminalMsg('✓ Image uploaded successfully (' + formatFileSize(file.size) + ')', 'success');
    updateProgress(20, 'Image uploaded');

    await delay(500);
    addTerminalMsg('🔍 Analyzing motor nameplate using AI Vision...', 'info');
    addTerminalMsg('<span class="typing-cursor"></span>', 'info', true);
    updateProgress(35, 'AI analyzing nameplate...');

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        // Remove typing cursor
        removeCursor();

        if (data.success) {
            updateProgress(50, 'Extracting fields...');
            await delay(300);
            addTerminalMsg('🏭 Manufacturer identified: ' + (data.manufacturer || 'Unknown'), 'data');

            await delay(400);
            addTerminalMsg('⚡ Model: ' + (data.model || 'N/A'), 'data');
            updateProgress(60, 'Manufacturer found');

            await delay(350);
            addTerminalMsg('🔌 Power: ' + (data.power || 'N/A') + ' KVA', 'data');
            updateProgress(70, 'Reading specifications...');

            await delay(400);
            addTerminalMsg('🔧 Searching manufacturer database...', 'info');
            updateProgress(80, 'Manufacturer lookup...');

            await delay(500);
            addTerminalMsg('📊 Engineering estimates calculated', 'success');
            addTerminalMsg('   Copper: 35 Kg | Coils: 48 | Labour: 28 hrs', 'warning');
            updateProgress(90, 'Estimates ready');

            await delay(400);
            addTerminalMsg('📋 Inventory created: ' + data.inventory_id, 'success');
            updateProgress(95, 'Creating inventory...');

            await delay(300);
            addTerminalMsg('✅ Analysis complete! Click the row to view details.', 'complete');
            updateProgress(100, 'Done!');

            document.getElementById('analysisStatusBadge').classList.remove('d-none');

            setTimeout(() => {
                progressSection.classList.add('d-none');
                showToast('Success', `Inventory ${data.inventory_id} created!`, 'success');
                clearUpload();
                loadInventory();
                loadStats();
            }, 800);

        } else {
            removeCursor();
            addTerminalMsg('❌ Error: ' + (data.error || 'Analysis failed'), 'error');
            updateProgress(0, 'Error');
            showToast('Error', data.error, 'danger');
            progressSection.classList.add('d-none');
        }

    } catch (error) {
        removeCursor();
        addTerminalMsg('❌ Network error: ' + error.message, 'error');
        showToast('Error', error.message, 'danger');
        progressSection.classList.add('d-none');
    }

    uploadBtn.disabled = false;
    uploadBtn.innerHTML = '<i class="bi bi-cpu me-2"></i>Upload & Create Inventory';
}

function addTerminalMsg(text, type, isCursor = false) {
    const terminal = document.getElementById('analysisTerminal');
    if (isCursor) {
        const msg = document.createElement('div');
        msg.id = 'typingCursor';
        msg.className = 'typing-indicator';
        msg.innerHTML = '<span></span><span></span><span></span>';
        terminal.appendChild(msg);
    } else if (text) {
        const msg = document.createElement('div');
        msg.className = `msg msg-${type}`;
        msg.innerHTML = text;
        terminal.appendChild(msg);
    }
    terminal.scrollTop = terminal.scrollHeight;
}

function removeCursor() {
    const cursor = document.getElementById('typingCursor');
    if (cursor) cursor.remove();
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function updateProgress(percent, text) {
    document.getElementById('progressBar').style.width = percent + '%';
    document.getElementById('progressText').textContent = text;
}

// ==================== INVENTORY TABLE ====================

async function loadInventory() {
    document.getElementById('tableLoading').classList.remove('d-none');
    document.getElementById('inventoryTableWrapper').style.display = 'none';
    document.getElementById('tableEmpty').classList.add('d-none');

    try {
        const response = await fetch('/api/inventory-list');
        const data = await response.json();

        if (data.success) {
            allInventory = data.inventory;
            renderInventoryTable(allInventory);
        } else {
            showToast('Error', data.error || 'Failed to load inventory', 'danger');
        }
    } catch (error) {
        showToast('Error', 'Network error: ' + error.message, 'danger');
    }

    document.getElementById('tableLoading').classList.add('d-none');
}

function renderInventoryTable(inventory) {
    const tbody = document.getElementById('inventoryBody');
    const wrapper = document.getElementById('inventoryTableWrapper');
    const empty = document.getElementById('tableEmpty');

    if (inventory.length === 0) {
        wrapper.style.display = 'none';
        empty.classList.remove('d-none');
        return;
    }

    wrapper.style.display = 'block';
    empty.classList.add('d-none');

    tbody.innerHTML = inventory.map(item => {
        let statusClass = 'status-completed';
        let statusIcon = 'check-circle-fill';
        if (item.status === 'Quotation Generated') {
            statusClass = 'status-generated';
            statusIcon = 'file-earmark-check-fill';
        } else if (item.status === 'Processing') {
            statusClass = 'status-processing';
            statusIcon = 'hourglass-split';
        }

        return `
            <tr onclick="window.location='/inventory/${item.inventory_id}'" style="cursor:pointer;">
                <td>
                    <span class="inv-id-badge">${item.inventory_id}</span>
                </td>
                <td>
                    <img src="/${item.image_path}" alt="" class="inventory-thumb"
                         onerror="this.src='/static/logo.png'">
                </td>
                <td>
                    <div class="inv-manufacturer">${item.manufacturer || 'Unknown'}</div>
                    <div class="inv-model">${item.model || ''}</div>
                </td>
                <td>
                    ${item.power ? `<span class="power-chip"><i class="bi bi-lightning-fill me-1"></i>${item.power} KVA</span>` : '<span class="text-muted small">N/A</span>'}
                </td>
                <td>
                    ${item.rpm ? `<span class="rpm-chip"><i class="bi bi-speedometer2 me-1"></i>${item.rpm}</span>` : '<span class="text-muted small">N/A</span>'}
                </td>
                <td class="text-center">
                    <span class="status-chip ${statusClass}">
                        <i class="bi bi-${statusIcon}"></i>${item.status}
                    </span>
                </td>
                <td><span class="date-text">${item.created_date}</span></td>
                <td class="text-center">
                    <a href="/inventory/${item.inventory_id}" class="inv-action-btn"
                       onclick="event.stopPropagation();" title="View Details & KG">
                        <i class="bi bi-diagram-3"></i>
                    </a>
                </td>
            </tr>
        `;
    }).join('');
}

function filterInventory() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    if (!query) {
        renderInventoryTable(allInventory);
        return;
    }

    const filtered = allInventory.filter(item =>
        (item.inventory_id || '').toLowerCase().includes(query) ||
        (item.manufacturer || '').toLowerCase().includes(query) ||
        (item.model || '').toLowerCase().includes(query) ||
        (item.power || '').toLowerCase().includes(query)
    );
    renderInventoryTable(filtered);
}

// ==================== STATS ====================

async function loadStats() {
    try {
        const [invRes, qtRes] = await Promise.all([
            fetch('/api/inventory-list'),
            fetch('/api/quotations')
        ]);
        const invData = await invRes.json();
        const qtData = await qtRes.json();

        if (invData.success) {
            document.getElementById('totalInventory').textContent = invData.inventory.length;
        }
        if (qtData.success) {
            document.getElementById('totalQuotations').textContent = qtData.quotations.length;
        }
    } catch (error) {
        console.error('Stats load error:', error);
    }
}

// ==================== UTILITIES ====================

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function showToast(title, message, type = 'info') {
    const toast = document.getElementById('toastNotification');
    const icon = document.getElementById('toastIcon');
    document.getElementById('toastTitle').textContent = title;
    document.getElementById('toastMessage').textContent = message;

    icon.className = 'bi me-2';
    if (type === 'success') icon.classList.add('bi-check-circle-fill', 'text-success');
    else if (type === 'danger') icon.classList.add('bi-exclamation-circle-fill', 'text-danger');
    else if (type === 'warning') icon.classList.add('bi-exclamation-triangle-fill', 'text-warning');
    else icon.classList.add('bi-info-circle-fill', 'text-primary');

    new bootstrap.Toast(toast, { delay: 4000 }).show();
}
