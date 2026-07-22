/**
 * Upload Module
 * 
 * Handles document upload with drag-and-drop, file validation,
 * XHR progress tracking, and per-file status updates.
 */

let selectedFiles = [];

/**
 * Initialize the upload module.
 */
function initUpload() {
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadModal = document.getElementById('uploadModal');
    const uploadModalClose = document.getElementById('uploadModalClose');
    const uploadCancelBtn = document.getElementById('uploadCancelBtn');
    const uploadSubmitBtn = document.getElementById('uploadSubmitBtn');
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    // Open modal
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            selectedFiles = [];
            renderUploadFileList();
            uploadModal.classList.add('active');
        });
    }

    // Close modal
    const closeModal = () => {
        uploadModal.classList.remove('active');
        selectedFiles = [];
        renderUploadFileList();
    };

    uploadModalClose.addEventListener('click', closeModal);
    uploadCancelBtn.addEventListener('click', closeModal);
    uploadModal.addEventListener('click', (e) => {
        if (e.target === uploadModal) closeModal();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        addFiles(e.target.files);
        fileInput.value = ''; // Reset so same file can be re-selected
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        addFiles(e.dataTransfer.files);
    });

    // Upload submit
    uploadSubmitBtn.addEventListener('click', uploadFiles);
}

/**
 * Add files to the selected list with validation.
 */
function addFiles(fileList) {
    const allowed = ['.pdf', '.docx', '.txt', '.csv', '.xlsx'];
    const maxSize = 50 * 1024 * 1024; // 50MB

    for (const file of fileList) {
        const ext = '.' + file.name.split('.').pop().toLowerCase();

        if (!allowed.includes(ext)) {
            showToast('warning', 'Invalid File', `"${file.name}" is not a supported file type. Use PDF, DOCX, TXT, CSV, or XLSX.`);
            continue;
        }

        if (file.size > maxSize) {
            showToast('warning', 'File Too Large', `"${file.name}" exceeds the 50MB limit.`);
            continue;
        }

        // Avoid duplicates
        if (selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
            continue;
        }

        selectedFiles.push(file);
    }

    renderUploadFileList();
}

/**
 * Render the list of selected files in the upload modal.
 */
function renderUploadFileList() {
    const list = document.getElementById('uploadFileList');
    const submitBtn = document.getElementById('uploadSubmitBtn');

    submitBtn.disabled = selectedFiles.length === 0;

    if (selectedFiles.length === 0) {
        list.innerHTML = '';
        return;
    }

    list.innerHTML = selectedFiles.map((file, i) => {
        const ext = file.name.split('.').pop().toLowerCase();
        const iconClass = ext === 'pdf' ? 'pdf' : ext === 'docx' ? 'docx' : (ext === 'csv' || ext === 'xlsx') ? 'xlsx' : 'txt';
        const size = formatFileSize(file.size);

        return `
            <div class="upload-file-item" id="uploadItem${i}">
                <div class="upload-file-icon doc-icon ${iconClass}">${ext.toUpperCase()}</div>
                <div class="upload-file-info">
                    <div class="upload-file-name">${escapeHtml(file.name)}</div>
                    <div class="upload-file-size">${size}</div>
                    <div class="progress-bar" id="progress${i}" style="display:none;">
                        <div class="progress-fill" id="progressFill${i}"></div>
                    </div>
                </div>
                <button class="doc-delete-btn" onclick="removeSelectedFile(${i})" style="opacity:1;" title="Remove">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
                <span class="upload-file-status" id="status${i}"></span>
            </div>
        `;
    }).join('');
}

/**
 * Remove a file from the selected list.
 */
function removeSelectedFile(index) {
    selectedFiles.splice(index, 1);
    renderUploadFileList();
}

/**
 * Upload all selected files using XHR for progress tracking.
 */
async function uploadFiles() {
    if (selectedFiles.length === 0) return;

    const submitBtn = document.getElementById('uploadSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px;"></div> Uploading...';

    // Remove delete buttons during upload
    document.querySelectorAll('.upload-file-item .doc-delete-btn').forEach(btn => btn.style.display = 'none');

    const formData = new FormData();
    selectedFiles.forEach(file => formData.append('files', file));

    const token = localStorage.getItem('token');

    // Show progress bars
    selectedFiles.forEach((_, i) => {
        const progressBar = document.getElementById(`progress${i}`);
        const status = document.getElementById(`status${i}`);
        if (progressBar) progressBar.style.display = 'block';
        if (status) { status.textContent = 'Uploading...'; status.className = 'upload-file-status processing'; }
    });

    try {
        // Use XHR for upload progress
        const result = await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${API_BASE}/upload`);
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const pct = Math.round((e.loaded / e.total) * 100);
                    selectedFiles.forEach((_, i) => {
                        const fill = document.getElementById(`progressFill${i}`);
                        if (fill) fill.style.width = pct + '%';
                    });
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    try {
                        const err = JSON.parse(xhr.responseText);
                        reject(new Error(err.detail || 'Upload failed'));
                    } catch {
                        reject(new Error('Upload failed'));
                    }
                }
            };

            xhr.onerror = () => reject(new Error('Network error'));
            xhr.send(formData);
        });

        // Update status for each file
        result.forEach((doc, i) => {
            const status = document.getElementById(`status${i}`);
            const fill = document.getElementById(`progressFill${i}`);
            if (fill) fill.style.width = '100%';
            if (status) {
                status.textContent = doc.status === 'ready' ? '✓ Ready' : doc.status === 'error' ? '✗ Error' : '⟳ Processing';
                status.className = `upload-file-status ${doc.status === 'ready' ? 'success' : doc.status === 'error' ? 'error' : 'processing'}`;
            }
        });

        showToast('success', 'Upload Complete', `${result.length} document(s) processed successfully.`);

        // Refresh document list
        loadDocuments();

        // Close modal after delay
        setTimeout(() => {
            document.getElementById('uploadModal').classList.remove('active');
            selectedFiles = [];
            renderUploadFileList();
        }, 1500);

    } catch (error) {
        showToast('error', 'Upload Failed', error.message);

        selectedFiles.forEach((_, i) => {
            const status = document.getElementById(`status${i}`);
            if (status) { status.textContent = '✗ Error'; status.className = 'upload-file-status error'; }
        });
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            Upload
        `;
    }
}

/**
 * Format file size to human-readable string.
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
