# scripts/deploy.py
#!/usr/bin/env python3
"""
Deployment script for SWORMS Lite
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {description}")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {description}")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Deploying SWORMS Lite...")
    
    # Check if Docker is available
    if not run_command("docker --version", "Checking Docker installation"):
        print("Docker is required for deployment. Please install Docker first.")
        return False
    
    # Create Docker image
    if not run_command("docker build -t sworms-lite .", "Building Docker image"):
        return False
    
    # Start the system
    if not run_command("docker run -d --name sworms-lite-container sworms-lite", "Starting container"):
        return False
    
    print("🎉 SWORMS Lite deployed successfully!")
    print("📊 Access system status at: http://localhost:8000/status")
    print("🔧 Monitor logs with: docker logs -f sworms-lite-container")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)