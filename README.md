# 📱 Android File Transfer

A Python-based GUI application for wirelessly transferring files between Android devices and PC over WiFi.

![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- **🖥️ Modern GUI** - Clean, user-friendly Tkinter interface
- **📶 Dual Transfer Modes**:
  - **Hotspot Mode** - Android creates hotspot, PC connects (no internet needed)
  - **WiFi Mode** - Both devices on the same network
- **📤 Upload** - Transfer files from Android to PC
- **📥 Download** - Transfer files from PC to Android
- **📷 QR Code** - Scan to instantly connect from your Android device
- **🌐 Web Interface** - Beautiful, mobile-optimized web UI
- **📁 Drag & Drop** - Easy file selection on mobile browser
- **🔄 Real-time Logging** - Track all transfer activity

## 📋 Requirements

- Python 3.6+
- tkinter (usually included with Python)
- qrcode (optional, for QR code generation)
- Pillow (optional, for QR code display)

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/Android-file-transfer.git
   cd Android-file-transfer
   ```

2. **Install dependencies** (optional, for QR code support):
   ```bash
   pip install qrcode[pil]
   ```

3. **Run the application**:
   ```bash
   python android_transfer_gui.py
   ```

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
- Tap the upload area in the web interface
- Select files from your Android device
- Files are saved to the `uploads/` folder

**Download (PC → Android)**:
- Place files in the `downloads/` folder on your PC
- Files will appear in the web interface
- Tap "Download" to save to your Android device

## 📁 Folder Structure

```
Android-file-transfer/
├── android_transfer_gui.py   # Main application
├── uploads/                  # Files uploaded from Android
├── downloads/                # Files available for Android to download
└── README.md
```

## 🔧 Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Hotspot Port | 1234 | Port for hotspot mode connections |
| WiFi Port | 1234 | Port for same-network connections |
| Max Upload Size | 500 MB | Maximum file size for uploads |

## 🛠️ Troubleshooting

### "Address already in use" error
- Change the port number to an unused port (try 8080, 8000, etc.)

### Can't connect from Android
- Ensure both devices are on the same network (WiFi mode)
- Check if firewall is blocking the connection
- Verify the IP address is correct

### QR Code not displaying
- Install the qrcode library: `pip install qrcode[pil]`
- Restart the application

### Files not appearing
- Refresh the file list using the "🔄 Refresh" button
- Ensure files are placed in the correct folder

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built with Python and Tkinter
- QR code generation powered by [python-qrcode](https://github.com/lincolnloop/python-qrcode)

---

Made with ❤️ for easy Android-PC file transfers
