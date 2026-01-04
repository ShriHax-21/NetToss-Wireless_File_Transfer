# 📱 Android File Transfer - GUI Version

A modern, feature-rich graphical application for wireless file transfer between Android devices and PC. Built with Python and Tkinter, featuring a beautiful **Chill Dark Theme** and easy-to-use web interface.

![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

### 🖥️ Desktop Application
- **Modern Dark Theme** - Chill, relaxing teal/cyan color scheme that's easy on the eyes
- **📶 Dual Transfer Modes**:
  - **Hotspot Mode** - Connect via WiFi Direct/Mobile Hotspot (no internet needed)
  - **WiFi Mode** - Connect over local WiFi network
- **📷 QR Code Generation** - Scan QR code from your phone for instant connection
- **📊 Real-time Logging** - Color-coded logs (success, error, info, warnings)
- **🔢 Connection Counter** - Track the number of active connections
- **📋 One-Click URL Copy** - Copy server URL to clipboard instantly
- **🌐 Open in Browser** - Launch web interface directly from the app

### 🌐 Web Interface
- **📱 Responsive Design** - Works beautifully on mobile, tablet, and desktop
- **📁 Drag & Drop Upload** - Simply drag files to upload
- **☑️ Multi-file Selection** - Select multiple files for batch operations
- **📂 Folder Navigation** - Browse through folder structures with breadcrumb navigation
- **📦 ZIP Download** - Download multiple files/folders as a single ZIP archive
- **📊 Progress Indicators** - Visual feedback for upload progress
- **🔄 Auto-refresh** - Real-time file list updates

## 📋 Requirements

- Python 3.6 or higher
- **Required packages:**
  ```
  qrcode[pil]
  Pillow
  ```
- tkinter (usually included with Python)

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/File-Transfer.git
   cd File-Transfer
   ```

2. **Install dependencies**:
   ```bash
   pip install qrcode[pil] Pillow
   ```

3. **Run the application**:
   ```bash
   python android_transfer_gui.py
   ```

> **Note:** The application will automatically attempt to install the QR code library if it's missing on first run.

## 📖 Usage

### Starting the Server

1. Launch the application
2. Select your transfer mode:
   - **📶 Hotspot Mode**: Use when Android creates a mobile hotspot
   - **🌐 WiFi Mode**: Use when both devices are on the same WiFi network
3. Adjust the port if needed (default: 1234)
4. Click **"▶️ Start Server"**

### Connecting from Android

**Option 1 - QR Code (Recommended)**:
- Scan the QR code displayed in the app with your Android camera/browser

**Option 2 - Manual**:
- Open your Android browser
- Navigate to the URL shown (e.g., `http://192.168.x.x:1234`)

### Transferring Files

**Upload (Android → PC)**:
1. Open the web interface on your phone
2. Tap the upload area or drag & drop files
3. Select files from your Android device
4. Files are saved to the `uploads/` folder on PC

**Download (PC → Android)**:
1. Place files in the `downloads/` folder on your PC
2. Files will appear in the web interface
3. **Single file**: Tap file name or download button
4. **Multiple files**: Use checkboxes to select, then click "Download" for ZIP
5. **Folders**: Click folder to browse, or download entire folder as ZIP

## 📁 Folder Structure

```
File-Transfer/
├── android_transfer_gui.py   # Main application
├── uploads/                  # Files uploaded from Android (auto-created)
├── downloads/                # Files available for download (auto-created)
├── connection_qr.png         # Generated QR code image
└── README.md
```

## 📦 Web API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/upload` | GET/POST | Upload form and file upload handler |
| `/api/files` | GET | JSON list of files/folders |
| `/download/<path>` | GET | Download single file |
| `/download-folder/<path>` | GET | Download folder as ZIP |
| `/download-selected` | GET | Download selected items as ZIP |

### 📦 Max Upload Size Limits

The max upload size can be changed in `android_transfer_gui.py` at line 317. The practical limit depends on your PC's available RAM since files are loaded into memory during upload.

**Recommended limits based on RAM:**

| Available RAM | Safe Max Upload |
|---------------|-----------------|
| 4 GB | ~1-2 GB |
| 8 GB | ~3-4 GB |
| 16 GB | ~8-10 GB |
| 32 GB+ | ~15-20 GB |

> ⚠️ **Note**: For very large files (2GB+), you may experience slower transfers, browser timeouts, or high memory usage.

## 🛠️ Troubleshooting

### "Address already in use" error
- Change the port number to an unused port (try 8080, 8000, etc.)
- Wait a few seconds and try again
- Check if another application is using the port

### Can't connect from Android
- Ensure both devices are on the same network (WiFi mode)
- Check if firewall is blocking the connection
- Verify the IP address is correct
- Try disabling VPN on either device

### QR Code not displaying
- Install the qrcode library: `pip install qrcode[pil] Pillow`
- Restart the application

### Files not appearing
- Refresh the file list using the "🔄 Refresh" button
- Ensure files are placed in the `downloads/` folder
- Check file permissions


## 🤝 Contributing

Contributions are welcome! Feel free to:
- 🐛 Report bugs
- 💡 Suggest new features
- 🔧 Submit pull requests
<p align="center">
Made with ❤️ for easy Android-PC file transfers by ShriHax
</p>
