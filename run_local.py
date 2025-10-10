"""
Local Deployment Script for Movie Recommendation System
=====================================================

This script starts the FastAPI backend and serves the frontend locally
for development and testing purposes.
"""

import subprocess
import webbrowser
import time
import os
import signal
import sys
import threading
from pathlib import Path

class LocalServer:
    """Local server manager for the movie recommendation system."""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.backend_port = 3000  # Single port for both
        self.frontend_port = 3000
        
    def start_backend(self):
        """Start the FastAPI backend server."""
        print("🚀 Starting FastAPI backend server...")
        try:
            # Start the API server
            self.backend_process = subprocess.Popen(
                [sys.executable, "api.py"],
                cwd=os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"✅ Backend server starting on http://localhost:{self.backend_port}")
            return True
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start a simple HTTP server for the frontend."""
        print("🌐 Starting frontend server...")
        try:
            frontend_dir = Path("frontend")
            if not frontend_dir.exists():
                print("❌ Frontend directory not found")
                return False
                
            # Start simple HTTP server for frontend with explicit IPv4 binding
            self.frontend_process = subprocess.Popen(
                [sys.executable, "-m", "http.server", str(self.frontend_port), "--bind", "127.0.0.1"],
                cwd=frontend_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Give it a moment to start
            time.sleep(2)
            
            # Verify the server started
            if self.frontend_process.poll() is None:
                print(f"✅ Frontend server started on http://127.0.0.1:{self.frontend_port}")
                return True
            else:
                print(f"❌ Frontend server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            return False
    
    def wait_for_backend(self, timeout=30):
        """Wait for backend to be ready."""
        import requests
        
        print("⏳ Waiting for backend to be ready...")
        for i in range(timeout):
            try:
                response = requests.get(f"http://localhost:{self.backend_port}/health", timeout=1)
                if response.status_code == 200:
                    print("✅ Backend is ready!")
                    return True
            except:
                pass
            time.sleep(1)
            print(f"   Waiting... ({i+1}/{timeout})")
        
        print("❌ Backend failed to start within timeout")
        return False
    
    def open_browser(self):
        """Open the application in the default browser."""
        print("🌐 Opening application in browser...")
        time.sleep(2)  # Give servers time to fully start
        webbrowser.open(f"http://localhost:{self.frontend_port}")
        
    def stop_servers(self):
        """Stop both servers."""
        print("\n🛑 Stopping servers...")
        
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            print("✅ Backend server stopped")
            
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
            print("✅ Frontend server stopped")
    
    def run(self):
        """Run the complete local deployment."""
        print("🎬 MOVIE RECOMMENDATION SYSTEM - LOCAL DEPLOYMENT")
        print("=" * 60)
        
        try:
            # Start backend
            if not self.start_backend():
                return False
            
            # Wait for backend to be ready
            if not self.wait_for_backend():
                self.stop_servers()
                return False
            
            # Start frontend
            if not self.start_frontend():
                self.stop_servers()
                return False
            
            # Open browser in a separate thread
            browser_thread = threading.Thread(target=self.open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            print("\n" + "=" * 60)
            print("🎉 MOVIE RECOMMENDATION SYSTEM IS RUNNING!")
            print("=" * 60)
            print(f"🔗 Frontend: http://localhost:{self.frontend_port}")
            print(f"🔗 Backend API: http://localhost:{self.backend_port}")
            print(f"📚 API Docs: http://localhost:{self.backend_port}/docs")
            print(f"📊 Health Check: http://localhost:{self.backend_port}/health")
            print(f"📈 Metrics: http://localhost:{self.backend_port}/metrics")
            print("\n💡 Features Available:")
            print("   • Netflix-style movie browsing interface")
            print("   • Real-time movie recommendations")
            print("   • Performance metrics dashboard")
            print("   • Fuzzy logic + Neural network hybrid system")
            print("   • Advanced collaborative filtering")
            print("   • User clustering and personalization")
            print("   • Intelligent recommendation explanations")
            print("\n⌨️  Press Ctrl+C to stop the servers")
            print("=" * 60)
            
            # Keep running until interrupted
            try:
                while True:
                    # Check if processes are still running
                    if self.backend_process.poll() is not None:
                        print("❌ Backend process stopped unexpectedly")
                        break
                    if self.frontend_process.poll() is not None:
                        print("❌ Frontend process stopped unexpectedly")
                        break
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n📝 Shutdown requested by user")
                
        except Exception as e:
            print(f"❌ Error during deployment: {e}")
            return False
        finally:
            self.stop_servers()
            
        return True


def main():
    """Main function to run local deployment."""
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    server = LocalServer()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n🛑 Stopping servers...")
        server.stop_servers()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    success = server.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()