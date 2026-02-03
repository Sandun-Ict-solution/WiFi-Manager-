# WiFi Manager & QR Code Generator 📶

A Streamlit web application that helps you find WiFi networks, retrieve saved passwords, and generate QR codes for easy WiFi sharing.

## Features

- 🔍 **Scan Available Networks**: Discover nearby WiFi networks
- 💾 **View Saved WiFi**: Retrieve saved WiFi credentials from your system
- 📱 **QR Code Generator**: Create QR codes for WiFi credentials that can be scanned by phones
- ⬇️ **Download QR Codes**: Save QR codes as PNG images

## Installation

### 1. Clone or download this project

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Running Locally

```bash
streamlit run wifi_app.py
```

The app will open in your browser at `http://localhost:8501`


## Platform-Specific Notes

### Windows
- Requires **administrator privileges** to retrieve saved WiFi passwords
- Run Command Prompt or PowerShell as Administrator before running the app

### Linux
- Requires **NetworkManager**
- May need `sudo` permissions for some operations
- Install nmcli if not available: `sudo apt-get install network-manager`

### macOS
- May require **administrator password** for keychain access
- Ensure WiFi is enabled

## Important Security Notes

⚠️ **Privacy & Security Warnings**:

1. **Local Use Only**: This app is designed for **personal, local use**
2. **Never deploy publicly** with WiFi password retrieval features enabled
3. **Sensitive Data**: WiFi passwords are sensitive information
4. **Permissions**: The app requires system-level permissions to access saved networks
5. **Disable for Public Deployment**: If deploying publicly, comment out or remove the "View Saved WiFi" feature

## Usage

### Scan Available Networks
- Click "Scan Available Networks" from the sidebar
- Press "Scan Networks" to see nearby WiFi networks

### View Saved WiFi
- Click "View Saved WiFi" from the sidebar
- Press "Get Saved Networks" to retrieve saved credentials
- Generate QR codes for any saved network

### Manual QR Generator
- Click "Manual QR Generator" from the sidebar
- Enter WiFi SSID and password
- Select security type (WPA/WPA2/WEP/Open)
- Generate and download QR code

### Sharing WiFi via QR Code
1. Generate a QR code for your WiFi network
2. Download the QR code image
3. Share it with guests
4. They can scan it with their phone camera to connect automatically

## Troubleshooting

**"No networks found"**
- Ensure WiFi is enabled
- Check you have necessary permissions
- Try running with administrator/sudo privileges

**"Unable to retrieve password"**
- Run the application with elevated privileges
- Some networks may have restricted access
- Ensure NetworkManager is installed (Linux)

**App won't start**
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (requires Python 3.7+)
- Try: `streamlit cache clear`

## Technologies Used

- **Streamlit**: Web framework
- **qrcode**: QR code generation
- **PIL/Pillow**: Image processing
- **subprocess**: System command execution

## License

Free to use for personal projects. Please respect privacy and security best practices.

## Contributing

**Designed By SANDUN WIJESINGHA**
---

**Made with ❤️ using Streamlit**
