/**
 * MedReport AI — Client-side JavaScript
 * Handles drag-and-drop, file selection, upload, and UI interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const clearFile = document.getElementById('clearFile');
    const submitBtn = document.getElementById('submitBtn');
    const uploadForm = document.getElementById('uploadForm');

    if (!uploadZone || !fileInput) return;

    const ALLOWED_TYPES = [
        'application/pdf',
        'image/png', 'image/jpeg', 'image/jpg',
        'image/tiff', 'image/bmp'
    ];
    const ALLOWED_EXTS = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'];

    // --- Drag & Drop ---
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
        uploadZone.addEventListener(evt, e => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    ['dragenter', 'dragover'].forEach(evt => {
        uploadZone.addEventListener(evt, () => {
            uploadZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(evt => {
        uploadZone.addEventListener(evt, () => {
            uploadZone.classList.remove('dragover');
        });
    });

    uploadZone.addEventListener('drop', e => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (isValidFile(file)) {
                fileInput.files = files;
                showFileInfo(file);
            } else {
                showAlert('Please upload a valid file (PDF, PNG, JPG, JPEG, TIFF, or BMP)', 'danger');
            }
        }
    });

    // --- Click to Browse ---
    uploadZone.addEventListener('click', () => {
        fileInput.click();
    });

    // --- File Selection ---
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            if (isValidFile(file)) {
                showFileInfo(file);
            } else {
                clearFileSelection();
                showAlert('Please upload a valid file (PDF, PNG, JPG, JPEG, TIFF, or BMP)', 'danger');
            }
        }
    });

    // --- Clear File ---
    if (clearFile) {
        clearFile.addEventListener('click', e => {
            e.stopPropagation();
            clearFileSelection();
        });
    }

    // --- Form Submit ---
    if (uploadForm) {
        uploadForm.addEventListener('submit', () => {
            if (submitBtn) {
                submitBtn.disabled = true;
                const btnText = submitBtn.querySelector('.btn-text');
                const btnLoading = submitBtn.querySelector('.btn-loading');
                if (btnText) btnText.classList.add('d-none');
                if (btnLoading) btnLoading.classList.remove('d-none');
            }
        });
    }

    // --- Helper Functions ---
    function isValidFile(file) {
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        return ALLOWED_EXTS.includes(ext);
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function showFileInfo(file) {
        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = formatFileSize(file.size);
        if (fileInfo) fileInfo.classList.remove('d-none');
        if (submitBtn) submitBtn.disabled = false;
        uploadZone.style.display = 'none';
    }

    function clearFileSelection() {
        fileInput.value = '';
        if (fileInfo) fileInfo.classList.add('d-none');
        if (submitBtn) submitBtn.disabled = true;
        uploadZone.style.display = 'block';
    }

    function showAlert(message, type) {
        const container = document.querySelector('.container.mt-3') || document.querySelector('.container');
        if (!container) return;

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show flash-alert shadow-sm mt-3`;
        alert.innerHTML = `
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        container.insertBefore(alert, container.firstChild);

        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    }

    // --- Auto-dismiss Flash Messages ---
    document.querySelectorAll('.flash-alert').forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    });
});
