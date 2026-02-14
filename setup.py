#!/usr/bin/env python3
"""
Quick Start Script for Legal Assistant
This script helps you set up and run the legal assistant quickly.
"""

import os
import sys
import subprocess

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def check_python_version():
    """Check if Python version is adequate"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✓ Python version: {sys.version.split()[0]}")
    return True

def check_venv():
    """Check if running in virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if in_venv:
        print("✓ Running in virtual environment")
    else:
        print("⚠️  Warning: Not running in virtual environment")
        print("   Consider creating one: python -m venv venv")
    return True

import subprocess

def install_dependencies():
    """Install required dependencies"""
    # print("\n📦 Installing dependencies...")
    # try:
    #     subprocess.check_call(
    #         ["uv", "add", "-r", "requirements.txt", "--quiet"]
    #     )
    #     print("✓ Dependencies installed successfully")
    #     return True
    # except subprocess.CalledProcessError:
    #     print("❌ Error installing dependencies")
    return


def check_api_key():
    """Check if API key is set"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        print(f"✓ API key found: {api_key[:8]}...{api_key[-4:]}")
        return True
    else:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("\n   Please set your API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print("\n   Or create a .env file (see .env.example)")
        return False

def create_directories():
    """Create necessary directories"""
    dirs = [
        "legal-docs",
        "legal-docs/contracts",
        "legal-docs/deeds",
        "legal-docs/leases",
        "legal-docs/regulations",
        "templates"
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    print("✓ Directory structure created")
    return True

def main():
    print_header("🏛️  Legal Property Assistant - Quick Start")
    
    # Check system requirements
    if not check_python_version():
        sys.exit(1)
    
    check_venv()
    
    # Install dependencies
    print_header("Step 1: Installing Dependencies")
    if not install_dependencies():
        sys.exit(1)
    
    # Check API key
    print_header("Step 2: Checking Configuration")
    create_directories()
    
    has_api_key = check_api_key()
    
    # Final instructions
    print_header("Setup Complete!")
    
    if has_api_key:
        print("✓ All checks passed! You're ready to start.")
        print("\n🚀 To start the Legal Assistant:")
        print("   python app.py")
        print("\n   Then open: http://localhost:5252")
    else:
        print("⚠️  Please set your OPENAI_API_KEY before starting:")
        print("\n   export OPENAI_API_KEY='your-api-key-here'")
        print("   python app.py")
    
    print("\n📚 For more information, see README.md")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()