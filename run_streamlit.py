#!/usr/bin/env python3
"""
Streamlit launcher script for the Stock Index Dashboard.

This script launches the Streamlit UI with proper configuration.
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit application."""
    print("🚀 Launching Stock Index Dashboard...")
    print("📊 Streamlit UI will open in your browser")
    print("🔗 Make sure the FastAPI service is running on localhost:8001")
    print("=" * 50)
    
    # Set Streamlit configuration
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "localhost"
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped by user")
    except Exception as e:
        print(f"❌ Error launching Streamlit: {e}")
        print("💡 Make sure you have installed the requirements: pip install -r requirements.txt")

if __name__ == "__main__":
    main() 