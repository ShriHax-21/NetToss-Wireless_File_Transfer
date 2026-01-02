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
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
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

# Global reference for logging
log_callback = None


def set_log_callback(callback):
    global log_callback
    log_callback = callback


def log_message(message):
    global log_callback
    if log_callback:
        log_callback(message)
    print(message)


class HotspotTransferHandler(SimpleHTTPRequestHandler):
    """Handler for WiFi Direct/Hotspot mode transfers"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DOWNLOAD_DIR, **kwargs)

    def log_message(self, format: str, *args):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] {self.client_address[0]} - {format % args}"
        log_message(msg)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.show_web_interface()
        elif self.path.startswith("/upload"):
            self.upload_form()
        elif self.path.startswith("/api/files"):
            self.list_files_json()
        elif self.path.startswith("/download/"):
            self.download_file()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/upload"):
            self.handle_file_upload()
        else:
            self.send_error(404, "File Upload Error")

    def upload_form(self):
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Android File Transfer - Hotspot Mode</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .mode-badge {
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 10px;
        }
        .content { padding: 30px; }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .section h2 { color: #11998e; margin-bottom: 15px; font-size: 1.5em; }
        .upload-area {
            border: 3px dashed #11998e;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: white;
        }
        .upload-area:hover { border-color: #38ef7d; background: #f8f9fa; }
        .upload-area.dragover { background: #e8f5e9; border-color: #4caf50; }
        .upload-icon { font-size: 3em; margin-bottom: 10px; }
        input[type="file"] { display: none; }
        .btn {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s;
            margin: 5px;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(17, 153, 142, 0.4); }
        .file-list { list-style: none; padding: 0; }
        .file-item {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            flex-wrap: wrap;
            gap: 10px;
        }
        .file-info { flex-grow: 1; min-width: 150px; }
        .file-name { font-weight: bold; color: #333; word-break: break-word; display: flex; align-items: center; gap: 8px; }
        .file-name::before { content: '📄'; }
        .file-size { color: #666; font-size: 0.85em; margin-top: 4px; }
        .btn-download {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 0.95em;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            white-space: nowrap;
        }
        .btn-download:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(17, 153, 142, 0.4); }
        .btn-download::before { content: '⬇️'; }
        .progress {
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 10px;
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
            font-weight: bold;
        }
        .status { padding: 15px; margin: 15px 0; border-radius: 10px; display: none; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
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
                <h2>📤 Upload Files from Android</h2>
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📁</div>
                    <p><strong>Tap here to select files</strong></p>
                    <p style="margin-top: 10px; color: #666;">or drag and drop files here</p>
                </div>
                <input type="file" id="fileInput" multiple>
                <div class="progress" id="uploadProgress">
                    <div class="progress-bar" id="progressBar">0%</div>
                </div>
                <div class="status" id="uploadStatus"></div>
            </div>
            <div class="section">
                <h2>📥 Download Files to Android</h2>
                <p style="margin-bottom: 15px; color: #666;">Available files from PC:</p>
                <ul class="file-list" id="fileList">
                    <li style="text-align: center; color: #666;">Loading files...</li>
                </ul>
                <button class="btn" onclick="refreshFiles()">🔄 Refresh List</button>
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
        uploadArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => uploadFiles(e.target.files));
        uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop', (e) => { e.preventDefault(); uploadArea.classList.remove('dragover'); uploadFiles(e.dataTransfer.files); });
        async function uploadFiles(files) {
            if (files.length === 0) return;
            uploadProgress.style.display = 'block';
            uploadStatus.style.display = 'none';
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const formData = new FormData();
                formData.append('file', file);
                try {
                    const response = await fetch('/upload', { method: 'POST', body: formData });
                    const progress = Math.round(((i + 1) / files.length) * 100);
                    progressBar.style.width = progress + '%';
                    progressBar.textContent = progress + '%';
                    if (!response.ok) throw new Error('Upload failed');
                } catch (error) {
                    showStatus('Error uploading ' + file.name, 'error');
                    return;
                }
            }
            showStatus('Successfully uploaded ' + files.length + ' file(s)!', 'success');
            fileInput.value = '';
            setTimeout(() => { uploadProgress.style.display = 'none'; progressBar.style.width = '0%'; }, 2000);
        }
        function showStatus(message, type) {
            uploadStatus.textContent = message;
            uploadStatus.className = 'status ' + type;
            uploadStatus.style.display = 'block';
            setTimeout(() => uploadStatus.style.display = 'none', 5000);
        }
        async function refreshFiles() {
            try {
                const response = await fetch('/api/files');
                const files = await response.json();
                if (files.length === 0) {
                    fileList.innerHTML = '<li style="text-align: center; color: #666;">No files available</li>';
                    return;
                }
                fileList.innerHTML = files.map(file => '<li class="file-item"><div class="file-info"><div class="file-name">' + file.name + '</div><div class="file-size">' + formatSize(file.size) + '</div></div><a href="/download/' + encodeURIComponent(file.name) + '" class="btn-download" download>Download</a></li>').join('');
            } catch (error) {
                fileList.innerHTML = '<li style="text-align: center; color: #d32f2f;">Error loading files</li>';
            }
        }
        function formatSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }
        refreshFiles();
    </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
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
            files = []
            for filename in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(filepath):
                    files.append({
                        "name": filename,
                        "size": os.path.getsize(filepath)
                    })
            
            response = json.dumps(files).encode()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', len(response))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response)
            
        except Exception as e:
            log_message(f"✗ Error listing files: {e}")
            self.send_error(500, f"Error listing files: {str(e)}")

    def download_file(self):
        try:
            filename = urllib.parse.unquote(self.path.split("/download/")[-1])
            filepath = Path(DOWNLOAD_DIR) / filename
            
            if not filepath.exists() or not filepath.is_file():
                self.send_error(404, "File not found")
                return
            
            with open(filepath, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            
            log_message(f"✓ Downloaded: {filename}")
            
        except Exception as e:
            log_message(f"✗ Download error: {e}")
            self.send_error(500, f"Download failed: {str(e)}")

    def show_web_interface(self):
        self.upload_form()


class InternetTransferHandler(HotspotTransferHandler):
    """Handler for Internet/WiFi mode transfers - inherits from Hotspot with different styling"""
    
    def upload_form(self):
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Android File Transfer - WiFi Mode</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .mode-badge {
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 10px;
        }
        .content { padding: 30px; }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .section h2 { color: #667eea; margin-bottom: 15px; font-size: 1.5em; }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: white;
        }
        .upload-area:hover { border-color: #764ba2; background: #f8f9fa; }
        .upload-area.dragover { background: #e8eaf6; border-color: #5c6bc0; }
        .upload-icon { font-size: 3em; margin-bottom: 10px; }
        input[type="file"] { display: none; }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s;
            margin: 5px;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        .file-list { list-style: none; padding: 0; }
        .file-item {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            flex-wrap: wrap;
            gap: 10px;
        }
        .file-info { flex-grow: 1; min-width: 150px; }
        .file-name { font-weight: bold; color: #333; word-break: break-word; display: flex; align-items: center; gap: 8px; }
        .file-name::before { content: '📄'; }
        .file-size { color: #666; font-size: 0.85em; margin-top: 4px; }
        .btn-download {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 0.95em;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            white-space: nowrap;
        }
        .btn-download:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        .btn-download::before { content: '⬇️'; }
        .progress {
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 10px;
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
            font-weight: bold;
        }
        .status { padding: 15px; margin: 15px 0; border-radius: 10px; display: none; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
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
                <h2>📤 Upload Files from Android</h2>
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📁</div>
                    <p><strong>Tap here to select files</strong></p>
                    <p style="margin-top: 10px; color: #666;">or drag and drop files here</p>
                </div>
                <input type="file" id="fileInput" multiple>
                <div class="progress" id="uploadProgress">
                    <div class="progress-bar" id="progressBar">0%</div>
                </div>
                <div class="status" id="uploadStatus"></div>
            </div>
            <div class="section">
                <h2>📥 Download Files to Android</h2>
                <p style="margin-bottom: 15px; color: #666;">Available files from PC:</p>
                <ul class="file-list" id="fileList">
                    <li style="text-align: center; color: #666;">Loading files...</li>
                </ul>
                <button class="btn" onclick="refreshFiles()">🔄 Refresh List</button>
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
        uploadArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => uploadFiles(e.target.files));
        uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop', (e) => { e.preventDefault(); uploadArea.classList.remove('dragover'); uploadFiles(e.dataTransfer.files); });
        async function uploadFiles(files) {
            if (files.length === 0) return;
            uploadProgress.style.display = 'block';
            uploadStatus.style.display = 'none';
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const formData = new FormData();
                formData.append('file', file);
                try {
                    const response = await fetch('/upload', { method: 'POST', body: formData });
                    const progress = Math.round(((i + 1) / files.length) * 100);
                    progressBar.style.width = progress + '%';
                    progressBar.textContent = progress + '%';
                    if (!response.ok) throw new Error('Upload failed');
                } catch (error) {
                    showStatus('Error uploading ' + file.name, 'error');
                    return;
                }
            }
            showStatus('Successfully uploaded ' + files.length + ' file(s)!', 'success');
            fileInput.value = '';
            setTimeout(() => { uploadProgress.style.display = 'none'; progressBar.style.width = '0%'; }, 2000);
        }
        function showStatus(message, type) {
            uploadStatus.textContent = message;
            uploadStatus.className = 'status ' + type;
            uploadStatus.style.display = 'block';
            setTimeout(() => uploadStatus.style.display = 'none', 5000);
        }
        async function refreshFiles() {
            try {
                const response = await fetch('/api/files');
                const files = await response.json();
                if (files.length === 0) {
                    fileList.innerHTML = '<li style="text-align: center; color: #666;">No files available</li>';
                    return;
                }
                fileList.innerHTML = files.map(file => '<li class="file-item"><div class="file-info"><div class="file-name">' + file.name + '</div><div class="file-size">' + formatSize(file.size) + '</div></div><a href="/download/' + encodeURIComponent(file.name) + '" class="btn-download" download>Download</a></li>').join('');
            } catch (error) {
                fileList.innerHTML = '<li style="text-align: center; color: #d32f2f;">Error loading files</li>';
            }
        }
        function formatSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }
        refreshFiles();
    </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
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
        self.root.title("📱 Android File Transfer")
        self.root.geometry("700x750")
        self.root.resizable(True, True)
        
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
        
    def setup_ui(self):
        # Main container with padding (no need for scrollbar with this layout)
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(
            title_frame, 
            text="📱 Android File Transfer",
            font=("Helvetica", 24, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Transfer files wirelessly between Android and PC",
            font=("Helvetica", 11)
        )
        subtitle_label.pack()
        
        # Top row: Mode Selection + QR Code side by side
        top_row = ttk.Frame(main_frame)
        top_row.pack(fill=tk.X, pady=(0, 10))
        top_row.columnconfigure(0, weight=1)
        top_row.columnconfigure(1, weight=0)
        
        # Left side - Mode Selection Frame
        mode_frame = ttk.LabelFrame(top_row, text="Transfer Mode", padding="10")
        mode_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Hotspot mode
        ttk.Radiobutton(
            mode_frame,
            text="📶 WiFi Direct / Hotspot Mode",
            variable=self.mode_var,
            value="hotspot",
            command=self.on_mode_change
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Label(
            mode_frame,
            text="    (Android creates hotspot, PC connects)",
            font=("Helvetica", 8),
            foreground="gray"
        ).pack(anchor=tk.W)
        
        # Internet mode
        ttk.Radiobutton(
            mode_frame,
            text="🌐 Same Network / WiFi Mode",
            variable=self.mode_var,
            value="internet",
            command=self.on_mode_change
        ).pack(anchor=tk.W, pady=(5, 2))
        
        ttk.Label(
            mode_frame,
            text="    (Both devices on same WiFi)",
            font=("Helvetica", 8),
            foreground="gray"
        ).pack(anchor=tk.W)
        
        # Port inside mode frame
        ttk.Separator(mode_frame, orient='horizontal').pack(fill=tk.X, pady=8)
        
        port_inner = ttk.Frame(mode_frame)
        port_inner.pack(fill=tk.X)
        
        ttk.Label(port_inner, text="Port:").pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(port_inner, textvariable=self.port_var, width=8)
        self.port_entry.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(port_inner, text="(1-65535)", font=("Helvetica", 8), foreground="gray").pack(side=tk.LEFT, padx=(5, 0))
        
        # Right side - QR Code Frame (fixed size)
        qr_frame = ttk.LabelFrame(top_row, text="QR Code", padding="10")
        qr_frame.grid(row=0, column=1, sticky="ns")
        
        qr_container = ttk.Frame(qr_frame, width=150, height=150)
        qr_container.pack()
        qr_container.pack_propagate(False)
        
        self.qr_label = ttk.Label(qr_container, text="Start server\nto generate", anchor="center", justify="center")
        self.qr_label.pack(expand=True, fill=tk.BOTH)
        
        # Server Control Frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(
            control_frame,
            text="▶️ Start Server",
            command=self.toggle_server,
            width=18
        )
        self.start_btn.pack(side=tk.LEFT)
        
        self.open_browser_btn = ttk.Button(
            control_frame,
            text="🌐 Open in Browser",
            command=self.open_browser,
            state=tk.DISABLED,
            width=18
        )
        self.open_browser_btn.pack(side=tk.LEFT, padx=(10, 0))
        
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
        
        self.url_label = ttk.Label(
            status_frame,
            text="",
            font=("Helvetica", 10),
            foreground="blue",
            cursor="hand2"
        )
        self.url_label.pack(anchor=tk.W, pady=(5, 0))
        self.url_label.bind("<Button-1>", lambda e: self.open_browser())
        
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
        
        # Text widget with scrollbar on the right side
        self.log_text = tk.Text(log_container, height=8, font=("Consolas", 9), wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
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
        """Add message to log"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
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
        
        try:
            self.server = HTTPServer(('0.0.0.0', port), handler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.is_running = True
            self.url = f"http://{get_local_ip()}:{port}"
            
            # Update UI
            self.start_btn.config(text="⏹️ Stop Server")
            self.open_browser_btn.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.DISABLED)
            
            mode_text = "📶 Hotspot" if mode == "hotspot" else "🌐 WiFi"
            self.status_label.config(text=f"🟢 Server running ({mode_text})")
            self.url_label.config(text=f"🔗 {self.url}")
            
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
            # Run shutdown in a separate thread to prevent GUI blocking
            def shutdown_server():
                try:
                    self.server.shutdown()
                except Exception:
                    pass
            
            shutdown_thread = threading.Thread(target=shutdown_server, daemon=True)
            shutdown_thread.start()
            self.server = None
        
        self.is_running = False
        
        # Update UI
        self.start_btn.config(text="▶️ Start Server")
        self.open_browser_btn.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.NORMAL)
        self.status_label.config(text="⚪ Server stopped")
        self.url_label.config(text="")
        self.qr_label.config(image="", text="Start server to generate QR code")
        
        self.log("Server stopped")
    
    def generate_qr(self, url):
        """Generate and display QR code"""
        if not HAS_QRCODE:
            self.qr_label.config(text="QR code unavailable\n(install: pip install qrcode pillow)")
            return
        
        try:
            qr = qrcode.QRCode(version=1, box_size=5, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((150, 150), Image.Resampling.LANCZOS)
            
            self.qr_image = ImageTk.PhotoImage(img)
            self.qr_label.config(image=self.qr_image, text="")
            
            # Also save QR code
            qr_path = "connection_qr.png"
            img.save(qr_path)
            
        except Exception as e:
            self.qr_label.config(text=f"QR generation failed: {e}")
    
    def open_browser(self):
        """Open the server URL in browser"""
        if self.is_running:
            webbrowser.open(self.url)
    
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
    
    # Set style
    style = ttk.Style()
    style.theme_use('clam')
    
    app = AndroidTransferGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
