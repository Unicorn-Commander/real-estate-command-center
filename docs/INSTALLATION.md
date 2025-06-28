# 🚀 Installation Guide
## Real Estate Command Center Setup Instructions

### Table of Contents
1. [System Requirements](#system-requirements)
2. [Quick Installation](#quick-installation)
3. [Detailed Installation Steps](#detailed-installation-steps)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Configuration](#advanced-configuration)

---

## System Requirements

### Supported Operating Systems
- **Primary**: Ubuntu 20.04+ or Debian-based Linux distributions
- **Tested**: Ubuntu 25.04 with KDE Plasma Desktop
- **Architecture**: x86_64 (64-bit)

### Hardware Requirements

#### Minimum Requirements
- **CPU**: Dual-core processor (2.0 GHz+)
- **RAM**: 4GB system memory
- **Storage**: 2GB free disk space
- **Display**: 1024x768 resolution
- **Network**: Internet connection for map tiles

#### Recommended Requirements
- **CPU**: Quad-core processor (3.0 GHz+)
- **RAM**: 8GB+ system memory
- **Storage**: SSD with 10GB+ free space
- **Display**: 1920x1080 or higher resolution
- **Network**: Broadband internet connection

### Software Prerequisites
- **Python**: 3.11 or later (system Python recommended)
- **Desktop Environment**: KDE Plasma (recommended) or GNOME
- **Package Manager**: apt (Ubuntu/Debian)

---

## Quick Installation

For experienced users who want to get started immediately:

```bash
# 1. Clone repository
git clone <repository-url>
cd real-estate-command-center

# 2. Install system dependencies
sudo apt update
sudo apt install -y \
  python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtwidgets \
  python3-pyside6.qtuitools python3-pyside6.qtwebenginewidgets \
  python3-qt-material python3-qtawesome python3-matplotlib \
  python3-reportlab python3-folium python3-pillow

# 3. Launch application
cd desktop
/usr/bin/python3 src/main.py
```

---

## Detailed Installation Steps

### Step 1: System Preparation

#### Update Package Lists
```bash
sudo apt update
sudo apt upgrade -y
```

#### Verify Python Installation
```bash
python3 --version
# Should show Python 3.11 or later
```

If Python 3.11+ is not available:
```bash
# Add deadsnakes PPA for newer Python versions
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-dev
```

### Step 2: Install System Dependencies

#### Core PySide6 Packages
```bash
sudo apt install -y \
  python3-pyside6.qtcore \
  python3-pyside6.qtgui \
  python3-pyside6.qtwidgets \
  python3-pyside6.qtuitools \
  python3-pyside6.qtwebenginewidgets \
  python3-pyside6.qtnetwork \
  python3-pyside6.qtprintsupport \
  python3-pyside6.qtwebchannel \
  python3-pyside6.qtwebenginecore
```

#### UI and Theming Packages
```bash
sudo apt install -y \
  python3-qt-material \
  python3-qtawesome
```

#### Data Visualization and Reporting
```bash
sudo apt install -y \
  python3-matplotlib \
  python3-reportlab \
  python3-pillow
```

#### Mapping and Geospatial
```bash
sudo apt install -y \
  python3-folium \
  python3-branca \
  python3-xyzservices
```

#### Additional Dependencies
```bash
sudo apt install -y \
  python3-jinja2 \
  python3-scipy \
  python3-fonttools
```

### Step 3: Obtain Source Code

#### Option A: Git Clone (Recommended)
```bash
git clone <repository-url>
cd real-estate-command-center
```

#### Option B: Download Archive
```bash
# Download and extract source archive
wget <archive-url> -O real-estate-command-center.zip
unzip real-estate-command-center.zip
cd real-estate-command-center
```

### Step 4: Directory Setup

#### Create Required Directories
```bash
# Navigate to project directory
cd real-estate-command-center

# Create photo storage directory
mkdir -p desktop/cma_photos

# Set appropriate permissions
chmod 755 desktop/cma_photos
```

#### Verify Directory Structure
```bash
ls -la desktop/src/
# Should show: main.py, core/, ui/ directories
```

### Step 5: Configuration

#### Create Settings File (Optional)
```bash
# Navigate to desktop directory
cd desktop

# Create default settings
cat > settings.json << EOF
{
  "api_url": "http://localhost:8000",
  "theme": "dark_amber.xml"
}
EOF
```

### Step 6: Initial Launch

#### Test Launch
```bash
# Ensure you're in the desktop directory
cd desktop

# Launch with system Python
/usr/bin/python3 src/main.py
```

#### Expected Behavior
- Application window should open
- Five tabs should be visible: Dashboard, Leads, Marketing, CMA, Database
- No error messages in terminal
- Theme should apply correctly

---

## Verification

### Basic Functionality Tests

#### 1. Application Launch
```bash
cd desktop
/usr/bin/python3 src/main.py
```
**Expected**: Application opens without errors

#### 2. CMA Module Test
1. Click the "CMA" tab
2. Navigate through all 5 sub-tabs
3. Try entering a property address
4. Upload a test photo

**Expected**: All tabs load, forms are responsive

#### 3. Map Functionality
1. Go to CMA → Location Map tab
2. Enter "New York" in address field
3. Click "Locate" button

**Expected**: Map displays with New York location

#### 4. Chart Generation
1. Go to CMA → Analysis tab
2. Charts should be visible

**Expected**: Price trend and comparable charts display

#### 5. PDF Export Test
1. Complete property details in CMA
2. Go to Report tab
3. Click "Export PDF"

**Expected**: PDF export dialog appears

### Diagnostic Commands

#### Check Python Modules
```bash
/usr/bin/python3 -c "import PySide6.QtWidgets; print('PySide6 OK')"
/usr/bin/python3 -c "import matplotlib; print('Matplotlib OK')"
/usr/bin/python3 -c "import folium; print('Folium OK')"
/usr/bin/python3 -c "import reportlab; print('ReportLab OK')"
```

#### System Information
```bash
# Check Qt version
/usr/bin/python3 -c "from PySide6.QtCore import qVersion; print(f'Qt version: {qVersion()}')"

# Check Python version
/usr/bin/python3 --version

# Check available memory
free -h
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: "ModuleNotFoundError: No module named 'PySide6'"
**Cause**: PySide6 not installed or using wrong Python interpreter

**Solutions**:
```bash
# Verify installation
dpkg -l | grep pyside6

# Reinstall if needed
sudo apt install --reinstall python3-pyside6.qtcore python3-pyside6.qtwidgets

# Use system Python explicitly
/usr/bin/python3 src/main.py
```

#### Issue 2: "ImportError: cannot import name 'pyqtSignal'"
**Cause**: Mixed PyQt/PySide imports

**Solution**: This should not occur with current codebase, but if it does:
```bash
# Check for PyQt installations
dpkg -l | grep pyqt

# Remove PyQt if present
sudo apt remove python3-pyqt5 python3-pyqt6
```

#### Issue 3: Application crashes on startup
**Cause**: Various possible causes

**Debugging steps**:
```bash
# Run with verbose output
/usr/bin/python3 -v src/main.py

# Check error logs
journalctl --user -f

# Try minimal test
/usr/bin/python3 -c "
import sys
from PySide6.QtWidgets import QApplication, QLabel
app = QApplication(sys.argv)
label = QLabel('Test')
label.show()
print('Qt test successful')
"
```

#### Issue 4: Map not loading
**Cause**: WebEngine issues or network problems

**Solutions**:
```bash
# Check WebEngine installation
dpkg -l | grep qtwebengine

# Install if missing
sudo apt install python3-pyside6.qtwebenginewidgets

# Test network connectivity
ping -c 3 tile.openstreetmap.org
```

#### Issue 5: Charts not displaying
**Cause**: Matplotlib backend issues

**Solutions**:
```bash
# Test matplotlib
/usr/bin/python3 -c "
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for testing
import matplotlib.pyplot as plt
print('Matplotlib test successful')
"

# Install additional backends if needed
sudo apt install python3-matplotlib-qt
```

### Performance Issues

#### Slow Startup
**Possible causes and solutions**:
1. **Large photo directory**: Clean up old photos in `desktop/cma_photos/`
2. **Low memory**: Close other applications, consider RAM upgrade
3. **Slow storage**: Move to SSD if using traditional HDD

#### Map loading slowly
**Solutions**:
1. **Check internet speed**: Maps require good connectivity
2. **Clear cache**: Remove temporary files in `/tmp/`
3. **Use wired connection**: WiFi may be unstable for large map tiles

---

## Advanced Configuration

### Custom Python Installation

If you need to use a custom Python installation:

#### Using Python Virtual Environment (Not Recommended)
```bash
# Create virtual environment
python3 -m venv ~/.local/share/real-estate-venv

# Activate environment
source ~/.local/share/real-estate-venv/bin/activate

# Install packages with pip (may have compatibility issues)
pip install PySide6 matplotlib reportlab folium pillow

# Launch application
python src/main.py
```

**Note**: System packages are strongly recommended over pip packages for stability.

### Desktop Integration

#### Create Desktop Entry
```bash
# Create desktop file
cat > ~/.local/share/applications/real-estate-command-center.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Real Estate Command Center
Comment=Professional CMA and Property Management Platform
Exec=/usr/bin/python3 $(pwd)/desktop/src/main.py
Icon=applications-office
Terminal=false
Categories=Office;Finance;
EOF

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

#### Create System-wide Installation
```bash
# Copy application to system location
sudo cp -r real-estate-command-center /opt/

# Create system-wide desktop entry
sudo tee /usr/share/applications/real-estate-command-center.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Real Estate Command Center
Comment=Professional CMA and Property Management Platform
Exec=/usr/bin/python3 /opt/real-estate-command-center/desktop/src/main.py
Icon=applications-office
Terminal=false
Categories=Office;Finance;
EOF
```

### Environment Variables

#### Custom Configuration
```bash
# Add to ~/.bashrc or ~/.profile
export REAL_ESTATE_DATA_DIR="$HOME/.local/share/real-estate-command-center"
export REAL_ESTATE_CONFIG_FILE="$HOME/.config/real-estate-command-center/settings.json"

# Create directories
mkdir -p "$REAL_ESTATE_DATA_DIR"
mkdir -p "$(dirname "$REAL_ESTATE_CONFIG_FILE")"
```

### Firewall Configuration

If using network features in the future:
```bash
# Allow outbound connections for map tiles
sudo ufw allow out 80/tcp
sudo ufw allow out 443/tcp

# For future API integration
sudo ufw allow out 8000/tcp
```

---

## Uninstallation

### Remove Application
```bash
# Remove source code
rm -rf real-estate-command-center

# Remove user data (optional)
rm -rf ~/.local/share/real-estate-command-center
rm -f ~/.config/real-estate-command-center/settings.json

# Remove desktop entries
rm -f ~/.local/share/applications/real-estate-command-center.desktop
```

### Remove System Packages
```bash
# Remove PySide6 packages (if not needed by other applications)
sudo apt remove python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtwidgets

# Remove other packages (carefully - check dependencies)
sudo apt autoremove
```

---

## Support

### Getting Help
- **Documentation**: Check `docs/` directory for additional guides
- **Issues**: Report installation problems via GitHub Issues
- **Community**: Join discussions for installation tips and tricks

### Providing Feedback
When reporting installation issues, please include:
1. Operating system version (`lsb_release -a`)
2. Python version (`python3 --version`)
3. Complete error messages
4. Steps to reproduce the problem

---

*Installation Guide - Last updated: 2025-06-26*