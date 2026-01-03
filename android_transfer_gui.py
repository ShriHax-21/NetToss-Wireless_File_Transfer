#!/usr/bin/env python3
"""
Android File Transfer Server - GUI Version
A graphical interface for transferring files between Android and PC
"""

import os
import sys
import socket
import json
import threading
import webbrowser
import zipfile
import io
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import urllib.parse
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

try:    
    import qrcode
    from PIL import Image, ImageTk
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

# Configuration
UPLOAD_DIR = "uploads"
DOWNLOAD_DIR = "downloads"
DEFAULT_PORT_HOTSPOT = 1234
DEFAULT_PORT_INTERNET = 1234

# Create directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# Chill Dark Theme Colors - Relaxing & Professional
class ThemeColors:
    # Primary colors - Deep ocean/night vibes
    BG_DARK = "#0f1419"           # Main background - soft dark
    BG_SECONDARY = "#151b23"      # Secondary background
    BG_CARD = "#1c2630"           # Card/panel background
    BG_HOVER = "#283340"          # Hover state
    
    # Accent colors - Calm teal/cyan
    ACCENT_PRIMARY = "#4fd1c5"    # Primary teal
    ACCENT_SECONDARY = "#81e6d9"  # Light teal
    ACCENT_GRADIENT_START = "#38b2ac"
    ACCENT_GRADIENT_END = "#667eea"
    
    # Text colors - Soft and easy on eyes
    TEXT_PRIMARY = "#e2e8f0"      # Main text - soft white
    TEXT_SECONDARY = "#a0aec0"    # Secondary text
    TEXT_MUTED = "#718096"        # Muted text
    
    # Status colors - Softer, pastel-like
    SUCCESS = "#68d391"           # Soft green
    SUCCESS_DARK = "#48bb78"      # Darker green for contrast
    WARNING = "#f6ad55"           # Soft orange
    ERROR = "#fc8181"             # Soft red/coral
    ERROR_DARK = "#f56565"        # Darker red
    INFO = "#63b3ed"              # Soft blue
    
    # Log colors - Pleasant pastels
    LOG_SUCCESS = "#9ae6b4"       # Mint green for success logs
    LOG_ERROR = "#feb2b2"         # Soft coral for error logs  
    LOG_INFO = "#90cdf4"          # Sky blue for info logs
    LOG_WARNING = "#fbd38d"       # Soft amber for warnings
    LOG_TIME = "#b794f4"          # Soft purple for timestamps
    
    # Border colors - Subtle
    BORDER = "#2d3748"            # Soft border
    BORDER_LIGHT = "#4a5568"      # Lighter border

# Global reference for logging
log_callback = None

# Connection tracking
connection_count = 0
connection_callback = None


def set_log_callback(callback):
    global log_callback
    log_callback = callback


def set_connection_callback(callback):
    global connection_callback
    connection_callback = callback


def increment_connection():
    global connection_count, connection_callback
    connection_count += 1
    if connection_callback:
        connection_callback(connection_count)


def reset_connection_count():
    global connection_count, connection_callback
    connection_count = 0
    if connection_callback:
        connection_callback(connection_count)


def log_message(message):
    global log_callback
    if log_callback:
        log_callback(message)


class HotspotTransferHandler(SimpleHTTPRequestHandler):
    """Handler for WiFi Direct/Hotspot mode transfers"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DOWNLOAD_DIR, **kwargs)

    def log_message(self, format: str, *args):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] {self.client_address[0]} - {format % args}"
        log_message(msg)

    def do_GET(self):
        increment_connection()  # Track connection
        if self.path == "/" or self.path == "/index.html":
            self.show_web_interface()
        elif self.path.startswith("/upload"):
            self.upload_form()
        elif self.path.startswith("/api/files"):
            self.list_files_json()
        elif self.path.startswith("/download-selected"):
            self.download_selected()
        elif self.path.startswith("/download-folder/"):
            self.download_folder()
        elif self.path.startswith("/download/"):
            self.download_file()
        else:
            super().do_GET()

    def do_POST(self):
        increment_connection()  # Track connection
        if self.path.startswith("/upload"):
            self.handle_file_upload()
        else:
            self.send_error(404, "File Upload Error")

    def upload_form(self):
        html = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Android File Transfer - Hotspot Mode</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%2311998e'/><text x='50' y='68' font-size='50' text-anchor='middle' fill='white'>📱</text></svg>">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            min-height: 100vh;
            padding: 15px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 25px;
            text-align: center;
        }
        .header h1 { font-size: 1.8em; margin-bottom: 8px; }
        .header p { opacity: 0.9; font-size: 1em; }
        .mode-badge {
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 8px;
            font-size: 0.9em;
        }
        .content { padding: 20px; }
        .section {
            margin-bottom: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }
        .section h2 {
            color: #11998e;
            margin-bottom: 15px;
            font-size: 1.3em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .upload-area {
            border: 3px dashed #11998e;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: white;
        }
        .upload-area:hover { border-color: #38ef7d; background: #f0fdf4; }
        .upload-area.dragover { background: #d1fae5; border-color: #10b981; }
        .upload-icon { font-size: 2.5em; margin-bottom: 10px; }
        input[type="file"] { display: none; }
        .btn {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 0.95em;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 600;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(17, 153, 142, 0.4); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }
        .btn:active { transform: translateY(0); }
        .file-list {
            list-style: none;
            padding: 0;
            max-height: 350px;
            overflow-y: auto;
            margin: 0;
        }
        .file-item {
            background: white;
            padding: 12px 15px;
            margin: 8px 0;
            border-radius: 12px;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            gap: 12px;
            transition: all 0.2s;
            border: 2px solid transparent;
        }
        .file-item:hover { background: #f0fdf4; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .file-item.selected { background: #d1fae5; border-color: #11998e; }
        .file-checkbox {
            width: 20px;
            height: 20px;
            cursor: pointer;
            accent-color: #11998e;
            flex-shrink: 0;
        }
        .file-icon { font-size: 1.4em; flex-shrink: 0; }
        .file-info { flex-grow: 1; min-width: 0; }
        .file-name {
            font-weight: 600;
            color: #1f2937;
            word-break: break-word;
            cursor: pointer;
            transition: color 0.2s;
        }
        .file-name:hover { color: #11998e; }
        .file-meta {
            color: #6b7280;
            font-size: 0.8em;
            margin-top: 3px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .file-type {
            background: #e5e7eb;
            padding: 2px 8px;
            border-radius: 8px;
            font-size: 0.75em;
            font-weight: 500;
        }
        .file-type.folder { background: #fef3c7; color: #92400e; }
        .btn-download {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85em;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            white-space: nowrap;
            font-weight: 600;
            flex-shrink: 0;
        }
        .btn-download:hover { transform: scale(1.05); box-shadow: 0 4px 15px rgba(17, 153, 142, 0.4); }
        .breadcrumb {
            background: white;
            padding: 10px 15px;
            border-radius: 10px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 5px;
            flex-wrap: wrap;
            font-size: 0.9em;
        }
        .breadcrumb a {
            color: #11998e;
            text-decoration: none;
            padding: 5px 10px;
            border-radius: 8px;
            transition: background 0.2s;
            font-weight: 500;
        }
        .breadcrumb a:hover { background: #d1fae5; }
        .breadcrumb span { color: #9ca3af; }
        .selection-bar {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            padding: 12px 16px;
            border-radius: 12px;
            margin-bottom: 12px;
            display: none;
            align-items: center;
            justify-content: space-between;
            color: white;
            flex-wrap: wrap;
            gap: 10px;
        }
        .selection-bar.show { display: flex; }
        .selection-info { font-weight: 600; }
        .selection-actions { display: flex; gap: 8px; }
        .selection-actions button {
            background: white;
            color: #11998e;
            border: none;
            padding: 8px 14px;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
            font-size: 0.85em;
        }
        .selection-actions button:hover { transform: scale(1.05); }
        .select-all-row {
            margin-bottom: 12px;
            padding: 8px 12px;
            background: white;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .select-all-row label {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            color: #4b5563;
            font-size: 0.9em;
            font-weight: 500;
        }
        .progress {
            width: 100%;
            height: 25px;
            background: #e5e7eb;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 12px;
            display: none;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
            width: 0%;
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.85em;
        }
        .status {
            padding: 12px 16px;
            margin: 12px 0;
            border-radius: 10px;
            display: none;
            font-weight: 500;
        }
        .status.success { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
        .status.error { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #6b7280;
        }
        .empty-state .icon { font-size: 3em; margin-bottom: 10px; opacity: 0.7; }
        .empty-state p { font-size: 0.95em; }
        .btn-row {
            margin-top: 15px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        @media (max-width: 600px) {
            .file-item { padding: 10px 12px; }
            .btn-download { padding: 6px 12px; font-size: 0.8em; }
            .header h1 { font-size: 1.5em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Android File Transfer</h1>
            <p>Upload and download files wirelessly</p>
            <div class="mode-badge">📶 Hotspot Mode</div>
        </div>
        <div class="content">
            <div class="section">
                <h2>📤 Upload Files</h2>
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📁</div>
                    <p><strong>Tap to select files</strong></p>
                    <p style="margin-top: 8px; color: #6b7280; font-size: 0.9em;">or drag and drop here</p>
                </div>
                <input type="file" id="fileInput" multiple>
                <div class="progress" id="uploadProgress">
                    <div class="progress-bar" id="progressBar">0%</div>
                </div>
                <div class="status" id="uploadStatus"></div>
            </div>
            <div class="section">
                <h2>📥 Download Files</h2>
                <div class="breadcrumb" id="breadcrumb">
                    <a href="#" onclick="navigateTo(''); return false;">🏠 Home</a>
                </div>
                <div class="selection-bar" id="selectionBar">
                    <span class="selection-info"><span id="selectedCount">0</span> selected <span id="selectedSize"></span></span>
                    <div class="selection-actions">
                        <button onclick="downloadSelected()">⬇️ Download</button>
                        <button onclick="clearSelection()">✕ Clear</button>
                    </div>
                </div>
                <div class="select-all-row">
                    <label>
                        <input type="checkbox" id="selectAll" onchange="toggleSelectAll()" class="file-checkbox">
                        <span>Select All</span>
                    </label>
                </div>
                <ul class="file-list" id="fileList">
                    <li class="empty-state">
                        <div class="icon">⏳</div>
                        <p>Loading files...</p>
                    </li>
                </ul>
                <div class="btn-row">
                    <button class="btn" onclick="refreshFiles()">🔄 Refresh</button>
                    <button class="btn" id="downloadSelectedBtn" onclick="downloadSelected()" disabled>
                        ⬇️ Download (<span id="selectedCountBtn">0</span>)
                    </button>
                </div>
            </div>
        </div>
    </div>
    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadProgress = document.getElementById('uploadProgress');
        const progressBar = document.getElementById('progressBar');
        const uploadStatus = document.getElementById('uploadStatus');
        const fileList = document.getElementById('fileList');
        const selectionBar = document.getElementById('selectionBar');
        const breadcrumb = document.getElementById('breadcrumb');
        
        let currentPath = '';
        let selectedItems = new Set();
        let currentItems = [];
        
        uploadArea.onclick = () => fileInput.click();
        fileInput.onchange = (e) => uploadFiles(e.target.files);
        uploadArea.ondragover = (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); };
        uploadArea.ondragleave = () => uploadArea.classList.remove('dragover');
        uploadArea.ondrop = (e) => { e.preventDefault(); uploadArea.classList.remove('dragover'); uploadFiles(e.dataTransfer.files); };
        
        async function uploadFiles(files) {
            if (!files.length) return;
            uploadProgress.style.display = 'block';
            uploadStatus.style.display = 'none';
            for (let i = 0; i < files.length; i++) {
                const formData = new FormData();
                formData.append('file', files[i]);
                try {
                    const res = await fetch('/upload', { method: 'POST', body: formData });
                    if (!res.ok) throw new Error('Failed');
                    const pct = Math.round(((i + 1) / files.length) * 100);
                    progressBar.style.width = pct + '%';
                    progressBar.textContent = pct + '%';
                } catch (e) {
                    showStatus('Error: ' + files[i].name, 'error');
                    return;
                }
            }
            showStatus('Uploaded ' + files.length + ' file(s)!', 'success');
            fileInput.value = '';
            setTimeout(() => { uploadProgress.style.display = 'none'; progressBar.style.width = '0%'; }, 2000);
        }
        
        function showStatus(msg, type) {
            uploadStatus.textContent = msg;
            uploadStatus.className = 'status ' + type;
            uploadStatus.style.display = 'block';
            setTimeout(() => uploadStatus.style.display = 'none', 4000);
        }
        
        function updateBreadcrumb() {
            let html = '<a href="#" onclick="navigateTo(\'\'); return false;">🏠 Home</a>';
            if (currentPath) {
                const parts = currentPath.split('/');
                let p = '';
                parts.forEach((part, i) => {
                    p += (i > 0 ? '/' : '') + part;
                    html += ' <span>/</span> <a href="#" onclick="navigateTo(\'' + p + '\'); return false;">' + part + '</a>';
                });
            }
            breadcrumb.innerHTML = html;
        }
        
        function navigateTo(path) {
            currentPath = path;
            selectedItems.clear();
            updateSelectionUI();
            refreshFiles();
        }
        
        function toggleItem(path) {
            if (selectedItems.has(path)) {
                selectedItems.delete(path);
            } else {
                selectedItems.add(path);
            }
            updateSelectionUI();
            renderFiles();
        }
        
        function updateSelectionUI() {
            const count = selectedItems.size;
            document.getElementById('selectedCount').textContent = count;
            document.getElementById('selectedCountBtn').textContent = count;
            document.getElementById('downloadSelectedBtn').disabled = count === 0;
            selectionBar.classList.toggle('show', count > 0);
            const selectAll = document.getElementById('selectAll');
            if (currentItems.length > 0) {
                selectAll.checked = count === currentItems.length;
                selectAll.indeterminate = count > 0 && count < currentItems.length;
            }
        }
        
        function toggleSelectAll() {
            const selectAll = document.getElementById('selectAll');
            if (selectAll.checked) {
                currentItems.forEach(item => selectedItems.add(item.path));
            } else {
                selectedItems.clear();
            }
            updateSelectionUI();
            renderFiles();
        }
        
        function clearSelection() {
            selectedItems.clear();
            document.getElementById('selectAll').checked = false;
            updateSelectionUI();
            renderFiles();
        }
        
        function downloadSelected() {
            if (selectedItems.size === 0) return;
            const selectedPaths = Array.from(selectedItems);
            // If only one item selected and it's a file, download directly
            if (selectedPaths.length === 1) {
                const item = currentItems.find(i => i.path === selectedPaths[0]);
                if (item && item.type === 'file') {
                    window.location.href = '/download/' + encodeURIComponent(item.path);
                    return;
                }
            }
            // Multiple items or folders - use ZIP
            const items = selectedPaths.map(i => encodeURIComponent(i)).join(',');
            window.location.href = '/download-selected?items=' + items;
        }
        
        function renderFiles() {
            if (currentItems.length === 0) {
                fileList.innerHTML = '<li class="empty-state"><div class="icon">📂</div><p>No files here</p></li>';
                return;
            }
            fileList.innerHTML = currentItems.map(item => {
                const isFolder = item.type === 'folder';
                const icon = isFolder ? '📁' : '📄';
                const typeLabel = isFolder ? '<span class="file-type folder">Folder</span>' : '<span class="file-type">File</span>';
                const dlUrl = isFolder ? '/download-folder/' + encodeURIComponent(item.path) : '/download/' + encodeURIComponent(item.path);
                const sel = selectedItems.has(item.path);
                const clickAction = isFolder ? 'navigateTo(\'' + item.path + '\')' : 'window.location.href=\'' + dlUrl + '\'';
                return '<li class="file-item' + (sel ? ' selected' : '') + '">' +
                    '<input type="checkbox" class="file-checkbox" ' + (sel ? 'checked' : '') + ' onclick="toggleItem(\'' + item.path + '\')">' +
                    '<span class="file-icon">' + icon + '</span>' +
                    '<div class="file-info">' +
                        '<div class="file-name" onclick="' + clickAction + '">' + item.name + '</div>' +
                        '<div class="file-meta">' + formatSize(item.size) + ' ' + typeLabel + '</div>' +
                    '</div>' +
                    '<a href="' + dlUrl + '" class="btn-download">⬇️ ' + (isFolder ? 'ZIP' : 'Get') + '</a>' +
                '</li>';
            }).join('');
        }
        
        async function refreshFiles() {
            fileList.innerHTML = '<li class="empty-state"><div class="icon">⏳</div><p>Loading...</p></li>';
            try {
                const url = '/api/files' + (currentPath ? '?path=' + encodeURIComponent(currentPath) : '');
                const res = await fetch(url);
                const data = await res.json();
                currentItems = data.items || [];
                currentItems.sort((a, b) => {
                    if (a.type === 'folder' && b.type !== 'folder') return -1;
                    if (a.type !== 'folder' && b.type === 'folder') return 1;
                    return a.name.localeCompare(b.name);
                });
                updateBreadcrumb();
                renderFiles();
                updateSelectionUI();
            } catch (e) {
                fileList.innerHTML = '<li class="empty-state"><div class="icon">❌</div><p>Error loading</p></li>';
            }
        }
        
        function formatSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024, sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i];
        }
        
        refreshFiles();
    </script>
</body>
</html>'''
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def handle_file_upload(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 500_000_000:
                self.send_error(413, "File too large (max 500MB)")
                return

            boundary = self.headers.get('Content-Type').split('boundary=')[-1]
            data = self.rfile.read(content_length)
            
            parts = data.split(f'--{boundary}'.encode())
            for part in parts:
                if b'Content-Disposition' in part and b'filename=' in part:
                    filename_start = part.find(b'filename="') + 10
                    filename_end = part.find(b'"', filename_start)
                    filename = part[filename_start:filename_end].decode()
                    
                    file_start = part.find(b'\r\n\r\n') + 4
                    file_end = part.rfind(b'\r\n')
                    file_data = part[file_start:file_end]
                    
                    safe_filename = os.path.basename(filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_filename = f"{timestamp}_{safe_filename}"
                    filepath = os.path.join(UPLOAD_DIR, unique_filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(file_data)
                    
                    log_message(f"✓ Uploaded: {unique_filename} ({len(file_data)} bytes)")

            response = json.dumps({"status": "success"}).encode()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', len(response))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response)
            
        except Exception as e:
            log_message(f"✗ Upload error: {e}")
            self.send_error(500, f"Upload failed: {str(e)}")

    def list_files_json(self):
        try:
            # Get optional path parameter for subdirectory browsing
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            subpath = params.get('path', [''])[0]
            
            # Sanitize path to prevent directory traversal
            if subpath:
                subpath = subpath.lstrip('/').replace('..', '')
            
            target_dir = os.path.join(DOWNLOAD_DIR, subpath) if subpath else DOWNLOAD_DIR
            
            if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
                target_dir = DOWNLOAD_DIR
                subpath = ''
            
            items = []
            for filename in os.listdir(target_dir):
                filepath = os.path.join(target_dir, filename)
                relative_path = os.path.join(subpath, filename) if subpath else filename
                
                if os.path.isfile(filepath):
                    items.append({
                        "name": filename,
                        "path": relative_path,
                        "size": os.path.getsize(filepath),
                        "type": "file"
                    })
                elif os.path.isdir(filepath):
                    # Calculate folder size
                    folder_size = self.get_folder_size(filepath)
                    items.append({
                        "name": filename,
                        "path": relative_path,
                        "size": folder_size,
                        "type": "folder"
                    })
            
            response_data = {
                "items": items,
                "currentPath": subpath,
                "parentPath": os.path.dirname(subpath) if subpath else None
            }
            
            response = json.dumps(response_data).encode()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', len(response))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response)
            
        except Exception as e:
            log_message(f"✗ Error listing files: {e}")
            self.send_error(500, f"Error listing files: {str(e)}")
    
    def get_folder_size(self, folder_path):
        """Calculate total size of a folder"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, IOError):
                    pass
        return total_size
    
    def download_folder(self):
        """Download a folder as ZIP"""
        try:
            folder_path = urllib.parse.unquote(self.path.split("/download-folder/")[-1])
            full_path = Path(DOWNLOAD_DIR) / folder_path
            
            if not full_path.exists() or not full_path.is_dir():
                self.send_error(404, "Folder not found")
                return
            
            # Create ZIP in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, full_path)
                        zip_file.write(file_path, arcname)
            
            zip_content = zip_buffer.getvalue()
            zip_filename = f"{full_path.name}.zip"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/zip')
            self.send_header('Content-Disposition', f'attachment; filename="{zip_filename}"')
            self.send_header('Content-Length', len(zip_content))
            self.end_headers()
            self.wfile.write(zip_content)
            
            log_message(f"✓ Downloaded folder: {folder_path}")
            
        except Exception as e:
            log_message(f"✗ Folder download error: {e}")
            self.send_error(500, f"Download failed: {str(e)}")
    
    def download_selected(self):
        """Download multiple selected files/folders as ZIP"""
        try:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            items_param = params.get('items', [''])[0]
            
            if not items_param:
                self.send_error(400, "No items selected")
                return
            
            items = items_param.split(',')
            items = [urllib.parse.unquote(item) for item in items if item]
            
            if not items:
                self.send_error(400, "No items selected")
                return
            
            # Create ZIP in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for item in items:
                    item_path = Path(DOWNLOAD_DIR) / item
                    if not item_path.exists():
                        continue
                    
                    if item_path.is_file():
                        zip_file.write(item_path, item_path.name)
                    elif item_path.is_dir():
                        for root, dirs, files in os.walk(item_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.join(item_path.name, os.path.relpath(file_path, item_path))
                                zip_file.write(file_path, arcname)
            
            zip_content = zip_buffer.getvalue()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"download_{timestamp}.zip"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/zip')
            self.send_header('Content-Disposition', f'attachment; filename="{zip_filename}"')
            self.send_header('Content-Length', len(zip_content))
            self.end_headers()
            self.wfile.write(zip_content)
            
            log_message(f"✓ Downloaded {len(items)} selected items")
            
        except Exception as e:
            log_message(f"✗ Batch download error: {e}")
            self.send_error(500, f"Download failed: {str(e)}")

    def download_file(self):
        try:
            file_path = urllib.parse.unquote(self.path.split("/download/")[-1])
            filepath = Path(DOWNLOAD_DIR) / file_path
            
            if not filepath.exists() or not filepath.is_file():
                self.send_error(404, "File not found")
                return
            
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Get just the filename for the download
            filename = filepath.name
            
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            
            log_message(f"✓ Downloaded: {file_path}")
            
        except Exception as e:
            log_message(f"✗ Download error: {e}")
            self.send_error(500, f"Download failed: {str(e)}")

    def show_web_interface(self):
        self.upload_form()


class InternetTransferHandler(HotspotTransferHandler):
    """Handler for Internet/WiFi mode transfers - inherits from Hotspot with different styling"""
    
    def upload_form(self):
        html = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Android File Transfer - WiFi Mode</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%23667eea'/><text x='50' y='68' font-size='50' text-anchor='middle' fill='white'>📱</text></svg>">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 15px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            text-align: center;
        }
        .header h1 { font-size: 1.8em; margin-bottom: 8px; }
        .header p { opacity: 0.9; font-size: 1em; }
        .mode-badge {
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 8px;
            font-size: 0.9em;
        }
        .content { padding: 20px; }
        .section {
            margin-bottom: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: white;
        }
        .upload-area:hover { border-color: #764ba2; background: #f5f3ff; }
        .upload-area.dragover { background: #ede9fe; border-color: #8b5cf6; }
        .upload-icon { font-size: 2.5em; margin-bottom: 10px; }
        input[type="file"] { display: none; }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 0.95em;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: 600;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }
        .btn:active { transform: translateY(0); }
        .file-list {
            list-style: none;
            padding: 0;
            max-height: 350px;
            overflow-y: auto;
            margin: 0;
        }
        .file-item {
            background: white;
            padding: 12px 15px;
            margin: 8px 0;
            border-radius: 12px;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            gap: 12px;
            transition: all 0.2s;
            border: 2px solid transparent;
        }
        .file-item:hover { background: #f5f3ff; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .file-item.selected { background: #ede9fe; border-color: #667eea; }
        .file-checkbox {
            width: 20px;
            height: 20px;
            cursor: pointer;
            accent-color: #667eea;
            flex-shrink: 0;
        }
        .file-icon { font-size: 1.4em; flex-shrink: 0; }
        .file-info { flex-grow: 1; min-width: 0; }
        .file-name {
            font-weight: 600;
            color: #1f2937;
            word-break: break-word;
            cursor: pointer;
            transition: color 0.2s;
        }
        .file-name:hover { color: #667eea; }
        .file-meta {
            color: #6b7280;
            font-size: 0.8em;
            margin-top: 3px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .file-type {
            background: #e5e7eb;
            padding: 2px 8px;
            border-radius: 8px;
            font-size: 0.75em;
            font-weight: 500;
        }
        .file-type.folder { background: #fef3c7; color: #92400e; }
        .btn-download {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85em;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            white-space: nowrap;
            font-weight: 600;
            flex-shrink: 0;
        }
        .btn-download:hover { transform: scale(1.05); box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); }
        .breadcrumb {
            background: white;
            padding: 10px 15px;
            border-radius: 10px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 5px;
            flex-wrap: wrap;
            font-size: 0.9em;
        }
        .breadcrumb a {
            color: #667eea;
            text-decoration: none;
            padding: 5px 10px;
            border-radius: 8px;
            transition: background 0.2s;
            font-weight: 500;
        }
        .breadcrumb a:hover { background: #ede9fe; }
        .breadcrumb span { color: #9ca3af; }
        .selection-bar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 12px 16px;
            border-radius: 12px;
            margin-bottom: 12px;
            display: none;
            align-items: center;
            justify-content: space-between;
            color: white;
            flex-wrap: wrap;
            gap: 10px;
        }
        .selection-bar.show { display: flex; }
        .selection-info { font-weight: 600; }
        .selection-actions { display: flex; gap: 8px; }
        .selection-actions button {
            background: white;
            color: #667eea;
            border: none;
            padding: 8px 14px;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
            font-size: 0.85em;
        }
        .selection-actions button:hover { transform: scale(1.05); }
        .select-all-row {
            margin-bottom: 12px;
            padding: 8px 12px;
            background: white;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .select-all-row label {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            color: #4b5563;
            font-size: 0.9em;
            font-weight: 500;
        }
        .progress {
            width: 100%;
            height: 25px;
            background: #e5e7eb;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 12px;
            display: none;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.85em;
        }
        .status {
            padding: 12px 16px;
            margin: 12px 0;
            border-radius: 10px;
            display: none;
            font-weight: 500;
        }
        .status.success { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
        .status.error { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #6b7280;
        }
        .empty-state .icon { font-size: 3em; margin-bottom: 10px; opacity: 0.7; }
        .empty-state p { font-size: 0.95em; }
        .btn-row {
            margin-top: 15px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        @media (max-width: 600px) {
            .file-item { padding: 10px 12px; }
            .btn-download { padding: 6px 12px; font-size: 0.8em; }
            .header h1 { font-size: 1.5em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Android File Transfer</h1>
            <p>Upload and download files wirelessly</p>
            <div class="mode-badge">🌐 WiFi Mode</div>
        </div>
        <div class="content">
            <div class="section">
                <h2>📤 Upload Files</h2>
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📁</div>
                    <p><strong>Tap to select files</strong></p>
                    <p style="margin-top: 8px; color: #6b7280; font-size: 0.9em;">or drag and drop here</p>
                </div>
                <input type="file" id="fileInput" multiple>
                <div class="progress" id="uploadProgress">
                    <div class="progress-bar" id="progressBar">0%</div>
                </div>
                <div class="status" id="uploadStatus"></div>
            </div>
            <div class="section">
                <h2>📥 Download Files</h2>
                <div class="breadcrumb" id="breadcrumb">
                    <a href="#" onclick="navigateTo(''); return false;">🏠 Home</a>
                </div>
                <div class="selection-bar" id="selectionBar">
                    <span class="selection-info"><span id="selectedCount">0</span> selected</span>
                    <div class="selection-actions">
                        <button onclick="downloadSelected()">⬇️ Download</button>
                        <button onclick="clearSelection()">✕ Clear</button>
                    </div>
                </div>
                <div class="select-all-row">
                    <label>
                        <input type="checkbox" id="selectAll" onchange="toggleSelectAll()" class="file-checkbox">
                        <span>Select All</span>
                    </label>
                </div>
                <ul class="file-list" id="fileList">
                    <li class="empty-state">
                        <div class="icon">⏳</div>
                        <p>Loading files...</p>
                    </li>
                </ul>
                <div class="btn-row">
                    <button class="btn" onclick="refreshFiles()">🔄 Refresh</button>
                    <button class="btn" id="downloadSelectedBtn" onclick="downloadSelected()" disabled>
                        ⬇️ Download (<span id="selectedCountBtn">0</span>)
                    </button>
                </div>
            </div>
        </div>
    </div>
    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadProgress = document.getElementById('uploadProgress');
        const progressBar = document.getElementById('progressBar');
        const uploadStatus = document.getElementById('uploadStatus');
        const fileList = document.getElementById('fileList');
        const selectionBar = document.getElementById('selectionBar');
        const breadcrumb = document.getElementById('breadcrumb');
        
        let currentPath = '';
        let selectedItems = new Set();
        let currentItems = [];
        
        uploadArea.onclick = () => fileInput.click();
        fileInput.onchange = (e) => uploadFiles(e.target.files);
        uploadArea.ondragover = (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); };
        uploadArea.ondragleave = () => uploadArea.classList.remove('dragover');
        uploadArea.ondrop = (e) => { e.preventDefault(); uploadArea.classList.remove('dragover'); uploadFiles(e.dataTransfer.files); };
        
        async function uploadFiles(files) {
            if (!files.length) return;
            uploadProgress.style.display = 'block';
            uploadStatus.style.display = 'none';
            for (let i = 0; i < files.length; i++) {
                const formData = new FormData();
                formData.append('file', files[i]);
                try {
                    const res = await fetch('/upload', { method: 'POST', body: formData });
                    if (!res.ok) throw new Error('Failed');
                    const pct = Math.round(((i + 1) / files.length) * 100);
                    progressBar.style.width = pct + '%';
                    progressBar.textContent = pct + '%';
                } catch (e) {
                    showStatus('Error: ' + files[i].name, 'error');
                    return;
                }
            }
            showStatus('Uploaded ' + files.length + ' file(s)!', 'success');
            fileInput.value = '';
            setTimeout(() => { uploadProgress.style.display = 'none'; progressBar.style.width = '0%'; }, 2000);
        }
        
        function showStatus(msg, type) {
            uploadStatus.textContent = msg;
            uploadStatus.className = 'status ' + type;
            uploadStatus.style.display = 'block';
            setTimeout(() => uploadStatus.style.display = 'none', 4000);
        }
        
        function updateBreadcrumb() {
            let html = '<a href="#" onclick="navigateTo(\'\'); return false;">🏠 Home</a>';
            if (currentPath) {
                const parts = currentPath.split('/');
                let p = '';
                parts.forEach((part, i) => {
                    p += (i > 0 ? '/' : '') + part;
                    html += ' <span>/</span> <a href="#" onclick="navigateTo(\'' + p + '\'); return false;">' + part + '</a>';
                });
            }
            breadcrumb.innerHTML = html;
        }
        
        function navigateTo(path) {
            currentPath = path;
            selectedItems.clear();
            updateSelectionUI();
            refreshFiles();
        }
        
        function toggleItem(path) {
            if (selectedItems.has(path)) {
                selectedItems.delete(path);
            } else {
                selectedItems.add(path);
            }
            updateSelectionUI();
            renderFiles();
        }
        
        function updateSelectionUI() {
            const count = selectedItems.size;
            document.getElementById('selectedCount').textContent = count;
            document.getElementById('selectedCountBtn').textContent = count;
            document.getElementById('downloadSelectedBtn').disabled = count === 0;
            selectionBar.classList.toggle('show', count > 0);
            const selectAll = document.getElementById('selectAll');
            if (currentItems.length > 0) {
                selectAll.checked = count === currentItems.length;
                selectAll.indeterminate = count > 0 && count < currentItems.length;
            }
        }
        
        function toggleSelectAll() {
            const selectAll = document.getElementById('selectAll');
            if (selectAll.checked) {
                currentItems.forEach(item => selectedItems.add(item.path));
            } else {
                selectedItems.clear();
            }
            updateSelectionUI();
            renderFiles();
        }
        
        function clearSelection() {
            selectedItems.clear();
            document.getElementById('selectAll').checked = false;
            updateSelectionUI();
            renderFiles();
        }
        
        function downloadSelected() {
            if (selectedItems.size === 0) return;
            const selectedPaths = Array.from(selectedItems);
            // If only one item selected and it's a file, download directly
            if (selectedPaths.length === 1) {
                const item = currentItems.find(i => i.path === selectedPaths[0]);
                if (item && item.type === 'file') {
                    window.location.href = '/download/' + encodeURIComponent(item.path);
                    return;
                }
            }
            // Multiple items or folders - use ZIP
            const items = selectedPaths.map(i => encodeURIComponent(i)).join(',');
            window.location.href = '/download-selected?items=' + items;
        }
        
        function renderFiles() {
            if (currentItems.length === 0) {
                fileList.innerHTML = '<li class="empty-state"><div class="icon">📂</div><p>No files here</p></li>';
                return;
            }
            fileList.innerHTML = currentItems.map(item => {
                const isFolder = item.type === 'folder';
                const icon = isFolder ? '📁' : '📄';
                const typeLabel = isFolder ? '<span class="file-type folder">Folder</span>' : '<span class="file-type">File</span>';
                const dlUrl = isFolder ? '/download-folder/' + encodeURIComponent(item.path) : '/download/' + encodeURIComponent(item.path);
                const sel = selectedItems.has(item.path);
                const clickAction = isFolder ? 'navigateTo(\'' + item.path + '\')' : 'window.location.href=\'' + dlUrl + '\'';
                return '<li class="file-item' + (sel ? ' selected' : '') + '">' +
                    '<input type="checkbox" class="file-checkbox" ' + (sel ? 'checked' : '') + ' onclick="toggleItem(\'' + item.path + '\')">' +
                    '<span class="file-icon">' + icon + '</span>' +
                    '<div class="file-info">' +
                        '<div class="file-name" onclick="' + clickAction + '">' + item.name + '</div>' +
                        '<div class="file-meta">' + formatSize(item.size) + ' ' + typeLabel + '</div>' +
                    '</div>' +
                    '<a href="' + dlUrl + '" class="btn-download">⬇️ ' + (isFolder ? 'ZIP' : 'Get') + '</a>' +
                '</li>';
            }).join('');
        }
        
        async function refreshFiles() {
            fileList.innerHTML = '<li class="empty-state"><div class="icon">⏳</div><p>Loading...</p></li>';
            try {
                const url = '/api/files' + (currentPath ? '?path=' + encodeURIComponent(currentPath) : '');
                const res = await fetch(url);
                const data = await res.json();
                currentItems = data.items || [];
                currentItems.sort((a, b) => {
                    if (a.type === 'folder' && b.type !== 'folder') return -1;
                    if (a.type !== 'folder' && b.type === 'folder') return 1;
                    return a.name.localeCompare(b.name);
                });
                updateBreadcrumb();
                renderFiles();
                updateSelectionUI();
            } catch (e) {
                fileList.innerHTML = '<li class="empty-state"><div class="icon">❌</div><p>Error loading</p></li>';
            }
        }
        
        function formatSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024, sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i];
        }
        
        refreshFiles();
    </script>
</body>
</html>'''
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


class AndroidTransferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Android File Transfer")
        self.root.geometry("1050x900")
        self.root.resizable(True, True)
        self.root.minsize(850, 750)
        
        # Set window icon
        self.set_window_icon()
        
        # Center window on screen
        self.center_window(1050, 900)
        
        # Server state
        self.server = None
        self.server_thread = None
        self.is_running = False
        
        # Variables
        self.mode_var = tk.StringVar(value="hotspot")
        self.port_var = tk.StringVar(value=str(DEFAULT_PORT_HOTSPOT))
        
        # Set up log callback
        set_log_callback(self.log)
        
        # Build UI
        self.setup_ui()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self, width, height):
        """Center the window on screen"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def set_window_icon(self):
        """Set custom window icon"""
        try:
            # Create a simple icon using PhotoImage (works on all platforms)
            # 32x32 teal colored icon
            icon_data = """
            #define icon_width 32
            #define icon_height 32
            """
            # Use a built-in approach that works cross-platform
            # Create icon from base64 PNG data
            import base64
            # Simple 16x16 teal icon as base64 PNG
            icon_base64 = (
                "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAA"
                "AlwSFlzAAAA7AAAAOwBeShxvQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5"
                "vuPBoAAAKTSURBVFiF7ZdNaBNBFMd/s5tNNl9NatJqG0kbqRYrVhBBqAcRPHjw4Mmj4M"
                "GLF72IBy8ePHkQD168eBAP4kEQBEUQsVJBrRWrNrVNk26+dpNsdhcPTdOkm7SpePE/7c"
                "y8+c2befMeA/+5CNttUKlUSm1tbWcNw+gHDgNdgFLHMAFZYAGYBp6lUqnnt2/fXt/u+X"
                "K5XK65ufnBYDB4JhAI+EUE27ZRFIWqqiJAWZZJJBJMTU2RTqfvJRKJc9u14ejRo+cHBw"
                "dvKYpCuVzGcRxEBBHBsixKpRKGYZDP55mYmCASiVzZdgQ6OzsHRkZGugOBAIZhUCwWc"
                "V0Xy7JwHIfd3d0cOnSI5uZmVFXdOgKO43QFg0FUVaVUKmGaJo7jYNs2juOwZ88eBgYGa"
                "GtrI5/Pk8/nt45AVVVVAM/z8DwPz/MQEWzb5sCBA/T395NMJmloaGD//v0bIlC7mW5mM"
                "hpIjNHR0dxmDwWwbZtkMklbWxsAqqpuHYGampqaKxaLaJq2+u9GxGIxxsbG0HX9t/T6+"
                "vqac+l0uioC1dXVVXfgN20mk9mwPxAIVHfBYrFYFYGmpqaqO+ALgKqqgI8DVCoVyuVyV"
                "fvl5eWqCBw8eHDDAcrlMpZlVbUvFApVETh8+HDVgZdfT7zUdZ3FxUV0Xfcl4AmAqqrE4"
                "/GqDuhb8LlsNkuxWCSTyTA/P08mk0HTNDRNq9r/LgJBoBuou1vQtT8fwY8cOVIqlexcL"
                "meYpmk7juM4jrNlBDRNA8gD8z9bYGMEtkqmaSoLCwuOYRglIcNisZiLxWJzwIvV/T8Ei"
                "qK4ra2t7vT09MrMzIyjKIpj27a1UwQsy1LK5bIyNzc3B0wBzwFrpwhI6RfvJP/g+vFPy"
                "Xfbk5q+YJ/FpwAAAABJRU5ErkJggg=="
            )
            icon_image = tk.PhotoImage(data=base64.b64decode(icon_base64))
            self.root.iconphoto(True, icon_image)
            self._icon_image = icon_image  # Keep reference
        except Exception:
            pass  # Silently fail if icon can't be set
        
    def setup_ui(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="25")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title Section with icon
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title with gradient effect simulation
        title_label = ttk.Label(
            title_frame, 
            text="⚡ Android File Transfer",
            style="Title.TLabel"
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Transfer files wirelessly between Android and PC",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Version badge
        version_label = ttk.Label(
            title_frame,
            text="v2.0 • Dark Mode",
            style="Muted.TLabel"
        )
        version_label.pack(pady=(3, 0))
        version_label.configure(background=ThemeColors.BG_DARK)
        
        # Top row: Mode Selection + QR Code side by side
        top_row = ttk.Frame(main_frame)
        top_row.pack(fill=tk.X, pady=(0, 15))
        top_row.columnconfigure(0, weight=1)
        top_row.columnconfigure(1, weight=0)
        
        # Left side - Mode Selection Frame
        mode_frame = ttk.LabelFrame(top_row, text="  ⚙️ Transfer Mode  ", padding="15")
        mode_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        # Hotspot mode
        hotspot_radio = ttk.Radiobutton(
            mode_frame,
            text="📶  WiFi Direct / Hotspot Mode",
            variable=self.mode_var,
            value="hotspot",
            command=self.on_mode_change
        )
        hotspot_radio.pack(anchor=tk.W, pady=(5, 2))
        
        hotspot_desc = ttk.Label(
            mode_frame,
            text="      Android creates hotspot, PC connects",
            style="Muted.TLabel"
        )
        hotspot_desc.pack(anchor=tk.W)
        
        # Internet mode
        internet_radio = ttk.Radiobutton(
            mode_frame,
            text="🌐  Same Network / WiFi Mode",
            variable=self.mode_var,
            value="internet",
            command=self.on_mode_change
        )
        internet_radio.pack(anchor=tk.W, pady=(12, 2))
        
        internet_desc = ttk.Label(
            mode_frame,
            text="      Both devices on same WiFi network",
            style="Muted.TLabel"
        )
        internet_desc.pack(anchor=tk.W)
        
        # Port inside mode frame
        ttk.Separator(mode_frame, orient='horizontal').pack(fill=tk.X, pady=12)
        
        port_inner = ttk.Frame(mode_frame)
        port_inner.pack(fill=tk.X)
        port_inner.configure(style="TFrame")
        
        port_label = ttk.Label(port_inner, text="🔌 Port:", style="CardText.TLabel")
        port_label.pack(side=tk.LEFT)
        
        self.port_entry = ttk.Entry(port_inner, textvariable=self.port_var, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Enable keyboard shortcuts for port entry
        self.port_entry.bind("<Control-a>", lambda e: self.select_all_entry(e))
        self.port_entry.bind("<Control-A>", lambda e: self.select_all_entry(e))
        self.port_entry.bind("<Control-BackSpace>", lambda e: self.delete_all_entry(e))
        
        port_hint = ttk.Label(port_inner, text="(1-65535)", style="Muted.TLabel")
        port_hint.pack(side=tk.LEFT, padx=(10, 0))
        
        # Right side - QR Code Frame (fixed size)
        qr_frame = ttk.LabelFrame(top_row, text="  📱 QR Code  ", padding="15")
        qr_frame.grid(row=0, column=1, sticky="ns")
        
        qr_container = tk.Frame(qr_frame, width=140, height=140, bg=ThemeColors.BG_SECONDARY,
                                highlightbackground=ThemeColors.BORDER, highlightthickness=2)
        qr_container.pack(padx=5, pady=5)
        qr_container.pack_propagate(False)
        
        self.qr_label = tk.Label(qr_container, text="Start server\nto generate",
                                  bg=ThemeColors.BG_SECONDARY, fg=ThemeColors.TEXT_MUTED,
                                  font=("Segoe UI", 10), justify="center")
        self.qr_label.pack(expand=True, fill=tk.BOTH)
        
        # Server Control Frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(5, 15))
        
        # Button container for centering
        btn_container = ttk.Frame(control_frame)
        btn_container.pack(expand=True)
        
        self.start_btn = ttk.Button(
            btn_container,
            text="▶  Start Server",
            command=self.toggle_server,
            style="Success.TButton",
            width=20
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.open_browser_btn = ttk.Button(
            btn_container,
            text="🌐  Open in Browser",
            command=self.open_browser,
            state=tk.DISABLED,
            style="Secondary.TButton",
            width=20
        )
        self.open_browser_btn.pack(side=tk.LEFT)
        
        # Status and Log Side by Side Frame
        status_log_frame = ttk.Frame(main_frame)
        status_log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        status_log_frame.columnconfigure(0, weight=1)
        status_log_frame.columnconfigure(1, weight=2)
        status_log_frame.rowconfigure(0, weight=1)
        
        # Left side - Server Status
        status_frame = ttk.LabelFrame(status_log_frame, text="Server Status", padding="10")
        status_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        self.status_label = ttk.Label(
            status_frame,
            text="⚪ Server stopped",
            font=("Helvetica", 11)
        )
        self.status_label.pack(anchor=tk.W)
        
        # Connection counter display
        self.connection_frame = ttk.Frame(status_frame)
        self.connection_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.connection_label = ttk.Label(
            self.connection_frame,
            text="📊 Connections: 0",
            font=("Segoe UI", 10),
            foreground=ThemeColors.ACCENT_PRIMARY
        )
        self.connection_label.pack(side=tk.LEFT)
        
        # Set up connection callback
        set_connection_callback(self.update_connection_count)
        
        # URL display frame with copy button
        url_frame = ttk.Frame(status_frame)
        url_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.url_var = tk.StringVar(value="")
        self.url_entry = tk.Entry(
            url_frame,
            textvariable=self.url_var,
            font=("Consolas", 10),
            fg=ThemeColors.ACCENT_SECONDARY,
            bg=ThemeColors.BG_SECONDARY,
            readonlybackground=ThemeColors.BG_SECONDARY,
            relief="flat",
            state="readonly",
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=ThemeColors.BORDER,
            highlightcolor=ThemeColors.ACCENT_PRIMARY
        )
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.url_entry.bind("<Button-1>", lambda e: self.open_browser())
        
        self.copy_btn = ttk.Button(
            url_frame,
            text="📋 Copy",
            command=self.copy_url,
            style="Secondary.TButton",
            width=8
        )
        self.copy_btn.pack(side=tk.RIGHT, padx=(5, 0))
        self.copy_btn.pack_forget()  # Hide initially
        
        # Folder Management inside status frame
        ttk.Separator(status_frame, orient='horizontal').pack(fill=tk.X, pady=8)
        
        folder_label = ttk.Label(status_frame, text="📂 Folders", font=("Helvetica", 9, "bold"))
        folder_label.pack(anchor=tk.W)
        
        # Upload folder
        upload_row = ttk.Frame(status_frame)
        upload_row.pack(fill=tk.X, pady=(5, 2))
        
        ttk.Label(upload_row, text="📥 Uploads:", font=("Helvetica", 9)).pack(side=tk.LEFT)
        ttk.Button(upload_row, text="Open", command=lambda: self.open_folder(UPLOAD_DIR), width=6).pack(side=tk.RIGHT)
        
        # Download folder
        download_row = ttk.Frame(status_frame)
        download_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(download_row, text="📁 Downloads:", font=("Helvetica", 9)).pack(side=tk.LEFT)
        ttk.Button(download_row, text="Open", command=lambda: self.open_folder(DOWNLOAD_DIR), width=6).pack(side=tk.RIGHT)
        
        # Right side - Activity Log
        log_frame = ttk.LabelFrame(status_log_frame, text="Activity Log", padding="10")
        log_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Create frame for text and scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        # Styled text widget with dark theme
        self.log_text = tk.Text(
            log_container, 
            height=8, 
            font=("JetBrains Mono", 9),
            wrap=tk.WORD,
            bg=ThemeColors.BG_SECONDARY,
            fg=ThemeColors.TEXT_SECONDARY,
            insertbackground=ThemeColors.ACCENT_PRIMARY,
            selectbackground=ThemeColors.ACCENT_PRIMARY,
            selectforeground=ThemeColors.TEXT_PRIMARY,
            relief="flat",
            padx=12,
            pady=8,
            highlightthickness=1,
            highlightbackground=ThemeColors.BORDER,
            highlightcolor=ThemeColors.ACCENT_PRIMARY
        )
        log_scrollbar = ttk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Configure color tags for different log types
        self.log_text.tag_configure("timestamp", foreground=ThemeColors.LOG_TIME)
        self.log_text.tag_configure("success", foreground=ThemeColors.LOG_SUCCESS)
        self.log_text.tag_configure("error", foreground=ThemeColors.LOG_ERROR)
        self.log_text.tag_configure("info", foreground=ThemeColors.LOG_INFO)
        self.log_text.tag_configure("warning", foreground=ThemeColors.LOG_WARNING)
        self.log_text.tag_configure("normal", foreground=ThemeColors.TEXT_SECONDARY)
        
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).pack(anchor=tk.E, pady=(5, 0))
        
    def on_mode_change(self):
        """Update default port when mode changes"""
        if self.mode_var.get() == "hotspot":
            self.port_var.set(str(DEFAULT_PORT_HOTSPOT))
        else:
            self.port_var.set(str(DEFAULT_PORT_INTERNET))
    
    def log(self, message):
        """Add message to log with color coding"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Insert timestamp with purple color
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Determine message type and color
        msg_lower = message.lower()
        if "✓" in message or "success" in msg_lower or "started" in msg_lower or "uploaded" in msg_lower or "downloaded" in msg_lower or "copied" in msg_lower:
            tag = "success"
        elif "✗" in message or "error" in msg_lower or "failed" in msg_lower:
            tag = "error"
        elif "warning" in msg_lower:
            tag = "warning"
        elif "mode:" in msg_lower or "info" in msg_lower:
            tag = "info"
        else:
            tag = "normal"
        
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def toggle_server(self):
        """Start or stop the server"""
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        """Start the HTTP server"""
        try:
            port = int(self.port_var.get())
            if not (1 <= port <= 65535):
                raise ValueError("Port out of range")
        except ValueError:
            messagebox.showerror("Error", "Invalid port number. Please enter a value between 1 and 65535.")
            return
        
        mode = self.mode_var.get()
        handler = HotspotTransferHandler if mode == "hotspot" else InternetTransferHandler
        
        # Custom HTTPServer with SO_REUSEADDR to allow immediate port reuse
        class ReusableHTTPServer(HTTPServer):
            allow_reuse_address = True
            
            def server_close(self):
                self.socket.close()
        
        try:
            self.server = ReusableHTTPServer(('0.0.0.0', port), handler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.is_running = True
            self.url = f"http://{get_local_ip()}:{port}"
            
            # Update UI with modern styling
            self.start_btn.config(text="⏹  Stop Server", style="Danger.TButton")
            self.open_browser_btn.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.DISABLED)
            
            mode_text = "📶 Hotspot" if mode == "hotspot" else "🌐 WiFi"
            self.status_label.config(text=f"🟢  Server running ({mode_text})")
            self.url_var.set(self.url)
            self.copy_btn.pack(side=tk.RIGHT, padx=(5, 0))  # Show copy button
            
            # Generate QR code
            self.generate_qr(self.url)
            
            self.log(f"Server started on {self.url}")
            self.log(f"Mode: {mode_text}")
            
        except OSError as e:
            if "Address already in use" in str(e):
                messagebox.showerror("Error", f"Port {port} is already in use. Try a different port.")
            else:
                messagebox.showerror("Error", f"Failed to start server: {e}")
    
    def stop_server(self):
        """Stop the HTTP server"""
        if self.server:
            server_to_close = self.server
            self.server = None
            
            # Shutdown synchronously to ensure port is released
            try:
                server_to_close.shutdown()
            except Exception:
                pass
            try:
                server_to_close.server_close()
            except Exception:
                pass
        
        self.is_running = False
        
        # Update UI with modern styling
        self.start_btn.config(text="▶  Start Server", style="Success.TButton")
        self.open_browser_btn.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.NORMAL)
        self.status_label.config(text="⚫  Server stopped")
        self.url_var.set("")
        self.copy_btn.pack_forget()  # Hide copy button
        self.qr_label.config(image="", text="Start server\nto generate", bg=ThemeColors.BG_SECONDARY, fg=ThemeColors.TEXT_MUTED)
        reset_connection_count()  # Reset connection counter
        
        self.log("Server stopped")
    
    def update_connection_count(self, count):
        """Update the connection counter display"""
        self.connection_label.config(text=f"📊 Connections: {count}")
    
    def generate_qr(self, url):
        """Generate and display QR code with dark theme"""
        if not HAS_QRCODE:
            self.qr_label.config(text="QR unavailable\npip install qrcode[pil]",
                                bg=ThemeColors.BG_SECONDARY, fg=ThemeColors.TEXT_MUTED)
            return
        
        try:
            qr = qrcode.QRCode(version=1, box_size=5, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            
            # Dark theme QR code colors
            img = qr.make_image(fill_color=ThemeColors.ACCENT_SECONDARY, back_color=ThemeColors.BG_SECONDARY)
            
            # Use compatible resize method (works with older PIL versions)
            try:
                img = img.resize((130, 130), Image.Resampling.LANCZOS)
            except AttributeError:
                # Fallback for older PIL versions
                img = img.resize((130, 130), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS)
            
            self.qr_image = ImageTk.PhotoImage(img)
            self.qr_label.config(image=self.qr_image, text="", bg=ThemeColors.BG_SECONDARY)
            
            # Also save QR code
            qr_path = "connection_qr.png"
            img.save(qr_path)
            
        except Exception as e:
            self.qr_label.config(text=f"QR Error:\n{str(e)[:30]}",
                                bg=ThemeColors.BG_SECONDARY, fg=ThemeColors.ERROR)
    
    def open_browser(self):
        """Open the server URL in browser"""
        if self.is_running:
            webbrowser.open(self.url)
    
    def copy_url(self):
        """Copy server URL to clipboard"""
        if self.is_running and self.url:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.url)
            self.root.update()  # Required for clipboard to work
            # Show feedback
            original_text = self.copy_btn.cget("text")
            self.copy_btn.config(text="✓ Copied!")
            self.root.after(1500, lambda: self.copy_btn.config(text=original_text))
            self.log(f"URL copied to clipboard: {self.url}")
    
    def select_all_entry(self, event):
        """Select all text in an Entry widget"""
        event.widget.select_range(0, tk.END)
        event.widget.icursor(tk.END)
        return "break"  # Prevent default behavior
    
    def delete_all_entry(self, event):
        """Delete all text in an Entry widget (Ctrl+Backspace)"""
        event.widget.delete(0, tk.END)
        return "break"  # Prevent default behavior
    
    def open_folder(self, folder):
        """Open folder in file manager"""
        path = os.path.abspath(folder)
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')
    
    def on_closing(self):
        """Handle window close"""
        if self.is_running:
            self.stop_server()
        self.root.destroy()


def apply_modern_theme(root):
    """Apply modern dark blue theme to the application"""
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configure main window
    root.configure(bg=ThemeColors.BG_DARK)
    
    # Frame styles
    style.configure(
        "TFrame",
        background=ThemeColors.BG_DARK
    )
    
    style.configure(
        "Card.TFrame",
        background=ThemeColors.BG_CARD,
        relief="flat"
    )
    
    # Label styles
    style.configure(
        "TLabel",
        background=ThemeColors.BG_DARK,
        foreground=ThemeColors.TEXT_PRIMARY,
        font=("Segoe UI", 10)
    )
    
    style.configure(
        "Title.TLabel",
        background=ThemeColors.BG_DARK,
        foreground=ThemeColors.TEXT_PRIMARY,
        font=("Segoe UI", 26, "bold")
    )
    
    style.configure(
        "Subtitle.TLabel",
        background=ThemeColors.BG_DARK,
        foreground=ThemeColors.TEXT_SECONDARY,
        font=("Segoe UI", 11)
    )
    
    style.configure(
        "Header.TLabel",
        background=ThemeColors.BG_CARD,
        foreground=ThemeColors.TEXT_PRIMARY,
        font=("Segoe UI", 12, "bold")
    )
    
    style.configure(
        "Status.TLabel",
        background=ThemeColors.BG_CARD,
        foreground=ThemeColors.TEXT_PRIMARY,
        font=("Segoe UI", 11)
    )
    
    style.configure(
        "URL.TLabel",
        background=ThemeColors.BG_CARD,
        foreground=ThemeColors.ACCENT_SECONDARY,
        font=("Segoe UI", 10, "underline")
    )
    
    style.configure(
        "Muted.TLabel",
        background=ThemeColors.BG_CARD,
        foreground=ThemeColors.TEXT_MUTED,
        font=("Segoe UI", 9)
    )
    
    style.configure(
        "CardTitle.TLabel",
        background=ThemeColors.BG_CARD,
        foreground=ThemeColors.TEXT_PRIMARY,
        font=("Segoe UI", 9, "bold")
    )
    
    style.configure(
        "CardText.TLabel",
        background=ThemeColors.BG_CARD,
        foreground=ThemeColors.TEXT_SECONDARY,
        font=("Segoe UI", 9)
    )
    
    # LabelFrame styles (cards)
    style.configure(
        "TLabelframe",
        background=ThemeColors.BG_CARD,
        foreground=ThemeColors.TEXT_PRIMARY,
        bordercolor=ThemeColors.BORDER,
        relief="flat",
        borderwidth=2
    )
    
    style.configure(
        "TLabelframe.Label",
        background=ThemeColors.BG_CARD,
        foreground=ThemeColors.ACCENT_SECONDARY,
        font=("Segoe UI", 11, "bold")
    )
    
    # Modern Button style
    style.configure(
        "TButton",
        background=ThemeColors.ACCENT_PRIMARY,
        foreground=ThemeColors.TEXT_PRIMARY,
        bordercolor=ThemeColors.ACCENT_PRIMARY,
        focuscolor=ThemeColors.ACCENT_SECONDARY,
        lightcolor=ThemeColors.ACCENT_SECONDARY,
        darkcolor=ThemeColors.ACCENT_GRADIENT_START,
        borderwidth=0,
        focusthickness=0,
        padding=(20, 12),
        font=("Segoe UI", 10, "bold")
    )
    
    style.map(
        "TButton",
        background=[
            ("pressed", ThemeColors.ACCENT_GRADIENT_START),
            ("active", ThemeColors.ACCENT_SECONDARY),
            ("disabled", ThemeColors.BG_HOVER)
        ],
        foreground=[
            ("disabled", ThemeColors.TEXT_MUTED)
        ]
    )
    
    # Secondary Button style
    style.configure(
        "Secondary.TButton",
        background=ThemeColors.BG_HOVER,
        foreground=ThemeColors.TEXT_PRIMARY,
        bordercolor=ThemeColors.BORDER,
        borderwidth=1,
        padding=(15, 8),
        font=("Segoe UI", 9)
    )
    
    style.map(
        "Secondary.TButton",
        background=[
            ("pressed", ThemeColors.BORDER),
            ("active", ThemeColors.BORDER_LIGHT)
        ]
    )
    
    # Success Button style - Soft teal
    style.configure(
        "Success.TButton",
        background=ThemeColors.ACCENT_PRIMARY,
        foreground=ThemeColors.BG_DARK,
        padding=(20, 12),
        font=("Segoe UI", 10, "bold")
    )
    
    style.map(
        "Success.TButton",
        background=[
            ("pressed", ThemeColors.ACCENT_GRADIENT_START),
            ("active", ThemeColors.ACCENT_SECONDARY)
        ]
    )
    
    # Danger Button style - Soft coral
    style.configure(
        "Danger.TButton",
        background=ThemeColors.ERROR,
        foreground=ThemeColors.BG_DARK,
        padding=(20, 12),
        font=("Segoe UI", 10, "bold")
    )
    
    style.map(
        "Danger.TButton",
        background=[
            ("pressed", ThemeColors.ERROR_DARK),
            ("active", "#fca5a5")
        ]
    )
    
    # Radiobutton styles
    style.configure(
        "TRadiobutton",
        background=ThemeColors.BG_CARD,
        foreground=ThemeColors.TEXT_PRIMARY,
        focuscolor=ThemeColors.BG_CARD,
        font=("Segoe UI", 10)
    )
    
    style.map(
        "TRadiobutton",
        background=[
            ("active", ThemeColors.BG_CARD)
        ],
        indicatorcolor=[
            ("selected", ThemeColors.ACCENT_PRIMARY),
            ("!selected", ThemeColors.BORDER_LIGHT)
        ]
    )
    
    # Entry styles
    style.configure(
        "TEntry",
        fieldbackground=ThemeColors.BG_SECONDARY,
        foreground=ThemeColors.TEXT_PRIMARY,
        insertcolor=ThemeColors.ACCENT_PRIMARY,
        bordercolor=ThemeColors.BORDER,
        lightcolor=ThemeColors.BORDER,
        darkcolor=ThemeColors.BORDER,
        borderwidth=2,
        padding=(10, 8)
    )
    
    style.map(
        "TEntry",
        bordercolor=[
            ("focus", ThemeColors.ACCENT_PRIMARY)
        ],
        lightcolor=[
            ("focus", ThemeColors.ACCENT_PRIMARY)
        ]
    )
    
    # Separator style
    style.configure(
        "TSeparator",
        background=ThemeColors.BORDER
    )
    
    # Scrollbar style
    style.configure(
        "TScrollbar",
        background=ThemeColors.BG_SECONDARY,
        troughcolor=ThemeColors.BG_DARK,
        bordercolor=ThemeColors.BG_DARK,
        arrowcolor=ThemeColors.TEXT_MUTED
    )
    
    style.map(
        "TScrollbar",
        background=[
            ("active", ThemeColors.ACCENT_PRIMARY),
            ("pressed", ThemeColors.ACCENT_SECONDARY)
        ]
    )


def main():
    # Check for required modules
    missing = []
    try:
        import tkinter
    except ImportError:
        missing.append("tkinter")
    
    if missing:
        print("Missing required modules:", ", ".join(missing))
        print("Please install them and try again.")
        sys.exit(1)
    
    # Install qrcode if missing
    if not HAS_QRCODE:
        print("Installing qrcode library...")
        import subprocess
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "qrcode[pil]"], 
                          check=True, capture_output=True)
            print("QR code library installed. Please restart the application.")
        except:
            print("Warning: QR code generation will be unavailable")
    
    root = tk.Tk()
    
    # Apply modern dark blue theme
    apply_modern_theme(root)
    
    app = AndroidTransferGUI(root)
    root.mainloop()


if __name__ == "__main__":
    # Fork/spawn process to return control to terminal
    if sys.platform == "win32":
        # Windows: use subprocess to detach
        import subprocess
        if not os.environ.get("ANDROID_TRANSFER_CHILD"):
            subprocess.Popen(
                [sys.executable, __file__],
                env={**os.environ, "ANDROID_TRANSFER_CHILD": "1"},
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True
            )
            sys.exit(0)
    elif sys.platform == "darwin":
        # macOS: use fork
        if os.fork() > 0:
            sys.exit(0)
    else:
        # Linux: use fork
        if os.fork() > 0:
            sys.exit(0)
    main()
