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

## Deployment Options

### Option 1: Streamlit Community Cloud (Recommended - Free)

1. **Create a GitHub account** (if you don't have one)

2. **Create a new repository** on GitHub and push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

3. **Go to [share.streamlit.io](https://share.streamlit.io)**

4. **Sign in with GitHub**

5. **Click "New app"**

6. **Fill in the deployment settings**:
   - Repository: `YOUR_USERNAME/YOUR_REPO`
   - Branch: `main`
   - Main file path: `wifi_app.py`

7. **Click "Deploy"**

Your app will be live at: `https://YOUR_APP_NAME.streamlit.app`

### Option 2: Deploy on Heroku

1. **Install Heroku CLI**

2. **Create a `setup.sh` file**:
   ```bash
   mkdir -p ~/.streamlit/
   echo "\
   [server]\n\
   headless = true\n\
   port = $PORT\n\
   enableCORS = false\n\
   \n\
   " > ~/.streamlit/config.toml
   ```

3. **Create a `Procfile`**:
   ```
   web: sh setup.sh && streamlit run wifi_app.py
   ```

4. **Deploy**:
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```

### Option 3: Deploy on Railway

1. **Go to [railway.app](https://railway.app)**
2. **Sign up/Login**
3. **Click "New Project" → "Deploy from GitHub repo"**
4. **Select your repository**
5. **Railway will auto-detect and deploy**

### Option 4: Deploy on Render

1. **Go to [render.com](https://render.com)**
2. **Sign up/Login**
3. **Click "New" → "Web Service"**
4. **Connect your GitHub repository**
5. **Configure**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run wifi_app.py --server.port $PORT --server.address 0.0.0.0`

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

Feel free to submit issues and enhancement requests!

---

**Made with ❤️ using Streamlit**
