import subprocess
import sys
import os

if __name__ == "__main__":
    # Install dependencies
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Run Streamlit app with Vercel settings
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "influencer_dashboard.py",
        "--server.port", os.environ.get("PORT", "8080"),
        "--server.address", "0.0.0.0",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ])