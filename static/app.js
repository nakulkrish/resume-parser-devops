const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const spinner = document.getElementById('spinner');
const resultArea = document.getElementById('resultArea');
const jsonCode = document.getElementById('jsonCode');
const downloadJson = document.getElementById('downloadJson');
const downloadCsv = document.getElementById('downloadCsv');
const errorArea = document.getElementById('errorArea');
const dropZone = document.getElementById('dropZone');
const fileName = document.getElementById('fileName');
const uploadProgress = document.getElementById('uploadProgress');
const nameText = document.getElementById('nameText');
const emailText = document.getElementById('emailText');
const domainBadge = document.getElementById('domainBadge');
const skillsDiv = document.getElementById('skills');
const scoreCircle = document.getElementById('scoreCircle');
const copyJson = document.getElementById('copyJson');

let currentFile = null;

// Drag & drop handlers
['dragenter', 'dragover'].forEach(evt => {
  dropZone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });
});
['dragleave', 'drop'].forEach(evt => {
  dropZone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
  });
});

dropZone.addEventListener('drop', (e) => {
  const f = e.dataTransfer.files[0];
  if (f) handleFileSelection(f);
});

fileInput.addEventListener('change', (e) => {
  const f = e.target.files[0];
  if (f) handleFileSelection(f);
});

function handleFileSelection(f) {
  currentFile = f;
  fileName.textContent = `${f.name} • ${Math.round(f.size/1024)} KB`;
}

uploadBtn.addEventListener('click', () => {
  clearError();
  if (!currentFile) return showError('Please select a PDF file first.');
  uploadBtn.disabled = true;
  spinner.classList.remove('d-none');
  startUpload(currentFile);
});

function startUpload(file) {
  const xhr = new XMLHttpRequest();
  const fd = new FormData();
  fd.append('file', file);

  xhr.open('POST', '/api/process');

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      const percent = Math.round((e.loaded / e.total) * 100);
      uploadProgress.style.width = percent + '%';
    }
  };

  xhr.onload = () => {
    uploadBtn.disabled = false;
    spinner.classList.add('d-none');
    uploadProgress.style.width = '0%';

    try {
      const resp = JSON.parse(xhr.responseText);
      if (xhr.status !== 200) return showError(resp.error || 'Server error');
      renderResult(resp.result, resp.downloads);
    } catch (err) {
      showError('Invalid server response');
    }
  };

  xhr.onerror = () => {
    uploadBtn.disabled = false;
    spinner.classList.add('d-none');
    uploadProgress.style.width = '0%';
    showError('Network error during upload');
  };

  xhr.send(fd);
}

function renderResult(result, downloads) {
  resultArea.classList.remove('d-none');
  nameText.textContent = (result.name || 'Unknown').replace(/\b\w/g, c => c.toUpperCase());
  emailText.textContent = result.email || '';
  domainBadge.textContent = result.predicted_domain || '';

  // Skills
  skillsDiv.innerHTML = '';
  (result.top_skills || []).slice(0, 12).forEach(s => {
    const span = document.createElement('span');
    span.className = 'skill-chip me-2 mb-1';
    span.textContent = s;
    skillsDiv.appendChild(span);
  });

  // Score (number)
  const scoreVal = Math.min(100, typeof result.score === 'number' ? result.score : 0);
  scoreCircle.textContent = Math.round(scoreVal) + '%';
  scoreCircle.style.background = `conic-gradient(#198754 ${scoreVal * 3.6}deg, #e9ecef 0deg)`;

  // Downloads
  downloadJson.href = downloads.json;
  downloadCsv.href = downloads.csv;

  // Score breakdown UI
  const breakdownList = document.getElementById('breakdownList');
  breakdownList.innerHTML = '';
  const breakdown = result.score_breakdown || {};
  const entries = Object.entries(breakdown);
  if (entries.length === 0) {
    const none = document.createElement('div');
    none.className = 'text-muted small';
    none.textContent = 'No breakdown available';
    breakdownList.appendChild(none);
  } else {
    entries.forEach(([k, v]) => {
      const item = document.createElement('div');
      item.className = 'list-group-item bg-transparent border-0 p-2';
      item.innerHTML = `
        <div class="d-flex w-100 justify-content-between">
          <div class="fw-medium text-white">${capitalize(k.replace(/_/g, ' '))}</div>
          <small class="text-muted">${v}</small>
        </div>
        <div class="progress mt-2" style="height:8px; background: rgba(255,255,255,0.04)">
          <div class="progress-bar bg-info" role="progressbar" style="width: ${Math.min(100, v)}%"></div>
        </div>
      `;
      breakdownList.appendChild(item);
    });
  }

  // JSON display
  const pretty = JSON.stringify(result, null, 2);
  jsonCode.textContent = pretty;
  if (window.Prism) Prism.highlightElement(jsonCode);

  copyJson.onclick = async () => {
    await navigator.clipboard.writeText(pretty);
    copyJson.textContent = 'Copied ✓';
    setTimeout(() => copyJson.innerHTML = '<i class="bi bi-clipboard"></i> Copy JSON', 1500);
  };
}

function capitalize(s) {
  return s.replace(/(^|\s)\S/g, t => t.toUpperCase());
}

function showError(msg) {
  errorArea.textContent = msg;
  errorArea.classList.remove('d-none');
}

function clearError() {
  errorArea.classList.add('d-none');
  errorArea.textContent = '';
}
