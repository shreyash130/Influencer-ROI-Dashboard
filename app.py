from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import threading
import time
import sys
import os

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'''
        <html>
        <head><title>Influencer Dashboard</title></head>
        <body>
            <h1>Influencer Campaign ROI Dashboard</h1>
            <p>The Streamlit app should be starting now. If it doesn't load automatically:</p>
            <p><a href="http://localhost:8501">Click here to access the dashboard</a></p>
            <p><strong>Note:</strong> This deployment method has limitations. For best results, 
            run locally with: <code>streamlit run influencer_dashboard.py</code></p>
        </body>
        </html>
        ''')

def start_streamlit():
    # Set environment variables for Streamlit
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "localhost"
    
    # Run the Streamlit app
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "influencer_dashboard.py",
        "--server.port", "8501",
        "--server.address", "localhost"
    ])

if __name__ == "__main__":
    # Start Streamlit in a background thread
    streamlit_thread = threading.Thread(target=start_streamlit)
    streamlit_thread.daemon = True
    streamlit_thread.start()
    
    # Give Streamlit time to start
    time.sleep(3)
    
    # Start the HTTP server
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f"Server running on port {port}")
    server.serve_forever()