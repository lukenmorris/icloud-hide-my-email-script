#!/usr/bin/env python3
"""
iCloud Hide My Email Manager
This script provides an easy way to run the Hide My Email Manager.
"""

import sys
import os
import platform
import subprocess
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        print(f"   Your version: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print("\n📥 Download the latest Python from: https://www.python.org/downloads/")
        sys.exit(1)

def check_and_install_requirements():
    """Check if required packages are installed, install if missing"""
    required_packages = {
        'selenium': 'selenium>=4.15.0',
        'webdriver_manager': 'webdriver-manager>=4.0.1'
    }
    
    missing_packages = []
    
    for package, install_name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(install_name)
    
    if missing_packages:
        print("📦 Installing required packages...")
        print(f"   Packages to install: {', '.join(missing_packages)}")
        
        try:
            # Try to install missing packages
            for package in missing_packages:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print("✅ All requirements installed successfully!\n")
        except subprocess.CalledProcessError:
            print("\n❌ Failed to install requirements automatically.")
            print("Please install manually with:")
            print(f"   pip install {' '.join(missing_packages)}")
            sys.exit(1)

def check_chrome_installed():
    """Check if Google Chrome is installed"""
    system = platform.system()
    
    chrome_paths = {
        'Windows': [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ],
        'Darwin': [  # macOS
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ],
        'Linux': [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]
    }
    
    paths = chrome_paths.get(system, [])
    chrome_found = any(os.path.exists(path) for path in paths)
    
    if not chrome_found:
        # Try to find Chrome in PATH
        try:
            if system == 'Windows':
                subprocess.run(['where', 'chrome'], capture_output=True, check=True)
                chrome_found = True
        except:
            try:
                subprocess.run(['which', 'google-chrome'], capture_output=True, check=True)
                chrome_found = True
            except:
                pass
    
    if not chrome_found:
        print("⚠️  Warning: Google Chrome may not be installed.")
        print("   Chrome is required for this script to work.")
        print("   Download from: https://www.google.com/chrome/")
        response = input("\nContinue anyway? (yes/no): ").lower()
        if response not in ['yes', 'y']:
            sys.exit(1)

def print_banner():
    """Print a nice banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🔐 iCloud Hide My Email Manager                          ║
║                                                              ║
║     Automate your iCloud Hide My Email addresses            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Main entry point"""
    try:
        # Clear screen based on OS
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print_banner()
        
        # Run checks
        print("🔍 Running system checks...\n")
        
        print("Checking Python version...")
        check_python_version()
        print("✅ Python version OK\n")
        
        print("Checking Chrome installation...")
        check_chrome_installed()
        print("✅ Chrome check complete\n")
        
        print("Checking required packages...")
        check_and_install_requirements()
        print("✅ All requirements satisfied\n")
        
        print("="*60)
        print("🚀 Starting Hide My Email Manager...")
        print("="*60 + "\n")
        
        # Import and run the main script
        try:
            from hide_my_email_manager import main as run_manager
            run_manager()
        except ModuleNotFoundError:
            # Try alternative import for direct script name
            from deactivate_icloudemails import main as run_manager
            run_manager()
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Script interrupted by user (Ctrl+C)")
        print("Goodbye! 👋")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        print("\nPlease report this issue at:")
        print("https://github.com/lukenmorris/icloud-hide-my-email-manager/issues")
        sys.exit(1)

if __name__ == "__main__":
    main()