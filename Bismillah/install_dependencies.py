
#!/usr/bin/env python3
"""
Installer script for CryptoMentor AI dependencies
"""
import subprocess
import sys
import os

def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    print("🚀 Installing CryptoMentor AI Dependencies...")
    
    required_packages = [
        "httpx==0.27.2",
        "pandas==2.2.2", 
        "numpy==1.26.4"
    ]
    
    success_count = 0
    for package in required_packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 Installation Summary: {success_count}/{len(required_packages)} packages installed")
    
    if success_count == len(required_packages):
        print("✅ All dependencies installed successfully!")
        print("🎯 You can now use the new CoinAPI commands:")
        print("   • /analyze_new <symbol>")
        print("   • /futures_new <symbol>")
        print("   • /futures_signals_new")
        print("   • /market_new")
    else:
        print("⚠️ Some dependencies failed to install. Please check manually.")

if __name__ == "__main__":
    main()
