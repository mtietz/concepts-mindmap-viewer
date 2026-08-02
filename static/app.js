const stage = document.querySelector('#stage');
const image = document.querySelector('#mindmap');
const title = document.querySelector('#title');
const meta = document.querySelector('#meta');
const zoomOutput = document.querySelector('#zoom');
const documentList = document.querySelector('#documents');
const search = document.querySelector('#search');
const sidebarToggle = document.querySelector('#sidebar-toggle');
const chooseFolderButton = document.querySelector('#choose-folder');

if (localStorage.getItem('mindmap-sidebar-collapsed') === 'true') {
  document.body.classList.add('sidebar-collapsed');
}

let documents = [];
let current = null;
let scale = 1;
// Concepts stores the canvas orientation opposite to browser image coordinates.
// Keep that correction separate so the user-facing rotation still starts at 0°.
const baseRotation = 180;
let rotation = 0;
let x = 0;
let y = 0;
let drag = null;

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const formatSize = bytes => `${(bytes / 1024 / 1024).toFixed(1)} MB`;

const effectiveRotation = () => rotation + baseRotation;
const radians = () => effectiveRotation() * Math.PI / 180;

function rotateVector(vx, vy, angle = radians()) {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  return { x: vx * cos - vy * sin, y: vx * sin + vy * cos };
}

function screenToWorld(px, py) {
  const local = rotateVector(px - x, py - y, -radians());
  return { x: local.x / scale, y: local.y / scale };
}

function renderTransform() {
  image.style.transform = `translate(${x}px, ${y}px) rotate(${effectiveRotation()}deg) scale(${scale})`;
  zoomOutput.value = `${Math.round(scale * 100)}%`;
  document.querySelector('#rotation').value = `${Math.round(rotation)}°`;
}

function fit() {
  if (!image.naturalWidth) return;
  const padding = 54;
  const angle = radians();
  const cos = Math.abs(Math.cos(angle));
  const sin = Math.abs(Math.sin(angle));
  const rotatedWidth = image.naturalWidth * cos + image.naturalHeight * sin;
  const rotatedHeight = image.naturalWidth * sin + image.naturalHeight * cos;
  scale = clamp(Math.min(
    (stage.clientWidth - padding * 2) / rotatedWidth,
    (stage.clientHeight - padding * 2) / rotatedHeight,
    1
  ), 0.05, 8);
  const half = rotateVector(image.naturalWidth * scale / 2, image.naturalHeight * scale / 2);
  x = stage.clientWidth / 2 - half.x;
  y = stage.clientHeight / 2 - half.y;
  renderTransform();
}

function zoomAt(nextScale, clientX, clientY) {
  const rect = stage.getBoundingClientRect();
  const px = clientX - rect.left;
  const py = clientY - rect.top;
  const world = screenToWorld(px, py);
  scale = clamp(nextScale, 0.05, 8);
  const projected = rotateVector(world.x * scale, world.y * scale);
  x = px - projected.x;
  y = py - projected.y;
  renderTransform();
}

function rotateBy(degrees) {
  if (!image.naturalWidth) return;
  const px = stage.clientWidth / 2;
  const py = stage.clientHeight / 2;
  const world = screenToWorld(px, py);
  rotation = ((((rotation + degrees + 180) % 360) + 360) % 360) - 180;
  const projected = rotateVector(world.x * scale, world.y * scale);
  x = px - projected.x;
  y = py - projected.y;
  renderTransform();
}

function renderList(filter = '') {
  const term = filter.trim().toLocaleLowerCase();
  const matches = documents.filter(doc =>
    `${doc.name} ${doc.relativePath}`.toLocaleLowerCase().includes(term)
  );
  documentList.replaceChildren(...matches.map(doc => {
    const button = document.createElement('button');
    button.className = `document${current?.id === doc.id ? ' active' : ''}`;
    button.innerHTML = `<strong></strong><small></small>`;
    button.querySelector('strong').textContent = doc.name;
    button.querySelector('small').textContent = doc.relativePath;
    button.addEventListener('click', () => selectDocument(doc));
    return button;
  }));
}

function selectDocument(doc) {
  current = doc;
  rotation = 0;
  title.textContent = doc.name;
  meta.textContent = `${doc.relativePath} · ${formatSize(doc.size)}`;
  image.style.visibility = 'hidden';
  document.querySelector('#empty').textContent = 'Rendering the full mindmap…';
  document.querySelector('#empty').hidden = false;
  image.onload = () => {
    document.querySelector('#empty').hidden = true;
    image.style.visibility = 'visible';
    fit();
  };
  image.onerror = () => {
    document.querySelector('#empty').textContent = 'This document has no readable preview.';
  };
  image.src = `/api/render?id=${doc.id}&t=${doc.modified}`;
  renderList(search.value);
}

stage.addEventListener('wheel', event => {
  event.preventDefault();
  zoomAt(scale * Math.exp(-event.deltaY * 0.0015), event.clientX, event.clientY);
}, { passive: false });

stage.addEventListener('pointerdown', event => {
  if (event.button !== 0) return;
  drag = { clientX: event.clientX, clientY: event.clientY, x, y };
  stage.classList.add('dragging');
  stage.setPointerCapture(event.pointerId);
});
stage.addEventListener('pointermove', event => {
  if (!drag) return;
  x = drag.x + event.clientX - drag.clientX;
  y = drag.y + event.clientY - drag.clientY;
  renderTransform();
});
stage.addEventListener('pointerup', () => {
  drag = null;
  stage.classList.remove('dragging');
});
stage.addEventListener('dblclick', fit);

function toggleSidebar() {
  const collapsed = document.body.classList.toggle('sidebar-collapsed');
  localStorage.setItem('mindmap-sidebar-collapsed', String(collapsed));
  sidebarToggle.setAttribute('aria-expanded', String(!collapsed));
  requestAnimationFrame(fit);
}

sidebarToggle.setAttribute('aria-expanded', String(!document.body.classList.contains('sidebar-collapsed')));
sidebarToggle.addEventListener('click', toggleSidebar);

document.querySelector('#rotate-left').addEventListener('click', () => rotateBy(-90));
document.querySelector('#rotate-right').addEventListener('click', () => rotateBy(90));
document.querySelector('#rotation').addEventListener('click', () => {
  rotateBy(-rotation);
});
document.addEventListener('keydown', event => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'b') {
    event.preventDefault();
    toggleSidebar();
    return;
  }
  if (event.target.matches('input')) return;
  if (event.key === '[') rotateBy(-90);
  if (event.key === ']') rotateBy(90);
});

document.querySelector('#zoom-in').addEventListener('click', () => {
  const rect = stage.getBoundingClientRect();
  zoomAt(scale * 1.25, rect.left + rect.width / 2, rect.top + rect.height / 2);
});
document.querySelector('#zoom-out').addEventListener('click', () => {
  const rect = stage.getBoundingClientRect();
  zoomAt(scale / 1.25, rect.left + rect.width / 2, rect.top + rect.height / 2);
});
document.querySelector('#fit').addEventListener('click', fit);
document.querySelector('#reveal').addEventListener('click', () => {
  if (current) fetch(`/api/reveal?id=${current.id}`);
});

window.addEventListener('pywebviewready', () => {
  chooseFolderButton.hidden = false;
});
chooseFolderButton.addEventListener('click', async () => {
  chooseFolderButton.disabled = true;
  try {
    const selection = await window.pywebview.api.choose_folder();
    if (selection) window.location.reload();
  } finally {
    chooseFolderButton.disabled = false;
  }
});
search.addEventListener('input', () => renderList(search.value));
window.addEventListener('resize', fit);

fetch('/api/documents')
  .then(response => response.json())
  .then(data => {
    documents = data.documents;
    document.querySelector('#source').textContent = data.source;
    document.querySelector('#source').title = data.source;
    renderList();
    if (documents.length) {
      selectDocument(documents[0]);
    } else {
      title.textContent = 'No Concepts documents found';
      meta.textContent = 'Choose another folder from the toolbar.';
      document.querySelector('#empty').textContent = 'This folder contains no .concept documents.';
    }
  })
  .catch(error => {
    title.textContent = 'Could not load documents';
    meta.textContent = error.message;
  });
