#!/bin/bash

# Multi-backend OCR Deployment Script
# This script deploys the updated code to the server for all components
# Usage: ./deploy.sh [-m "commit message"] [-s server_address] [-p ssh_port] [-d project_directory]

COMMIT_MESSAGE=""
SERVER_ADDRESS=""
SSH_PORT="22"
PROJECT_DIR="/home/zakir/ocr-project"
LOCAL_PORTS="8080:localhost:8080 5000:localhost:5000 5001:localhost:5001"

# Parse command line arguments
while getopts "m:s:p:d:" opt; do
  case $opt in
    m)
      COMMIT_MESSAGE="$OPTARG"
      ;;
    s)
      SERVER_ADDRESS="$OPTARG"
      ;;
    p)
      SSH_PORT="$OPTARG"
      ;;
    d)
      PROJECT_DIR="$OPTARG"
      ;;
    \?)
      echo "Usage: $0 [-m \"commit message\"] [-s server_address] [-p ssh_port] [-d project_directory]"
      echo ""
      echo "Examples:"
      echo "  ./deploy.sh -m \"Update OCR system\" -s zakir@223.166.245.194 -p 40032"
      echo "  ./deploy.sh -s root@192.168.1.100 -d /home/root/ocr-project"
      echo ""
      echo "Default values:"
      echo "  SSH Port: $SSH_PORT"
      echo "  Project Directory: $PROJECT_DIR"
      exit 1
      ;;
  esac
done

# Validate required arguments
if [ -z "$SERVER_ADDRESS" ]; then
    echo "❌ Error: Server address (-s) is required"
    echo ""
    echo "Usage: $0 [-m \"commit message\"] [-s server_address] [-p ssh_port] [-d project_directory]"
    exit 1
fi

echo "🚀 Starting Multi-backend OCR deployment..."

# Step 1: Add, commit and push changes (only if there are changes)
echo "📝 Checking for changes to commit..."
git status

if [[ -n "$COMMIT_MESSAGE" ]]; then
    echo "📦 Committing changes with message: $COMMIT_MESSAGE"
    git add .
    git commit -m "$COMMIT_MESSAGE"
    git push origin master
    echo "✅ Changes committed and pushed"
elif [[ -z "$COMMIT_MESSAGE" ]]; then
    read -p "Do you want to commit and push changes? (y/n): " commit_choice

    if [[ $commit_choice == "y" || $commit_choice == "Y" ]]; then
        echo "📦 Committing changes..."
        git add .
        git commit -m "Update: Multi-backend OCR system improvements"
        git push origin master
        echo "✅ Changes committed and pushed"
    else
        echo "⏭️ Skipping commit step"
    fi
fi

echo ""
echo "🔗 Deploying to server..."
echo "============================="
echo "Server: $SERVER_ADDRESS"
echo "SSH Port: $SSH_PORT"
echo "Project Directory: $PROJECT_DIR"
echo "Local Port Forwarding: $LOCAL_PORTS"
echo ""

# SSH into server and deploy with port forwarding
ssh -p "$SSH_PORT" "$SERVER_ADDRESS" -L "$LOCAL_PORTS" << 'EOF'
    echo "🛑 Stopping current servers..."
    pkill -9 python3 || true

    echo "📁 Navigating to project..."
    cd "$PROJECT_DIR"

    echo "⬇️ Pulling latest changes..."
    git fetch origin
    git reset --hard origin/master

    echo "🔧 Running setup scripts..."
    cd deployment
    ./setup.sh

    echo "🚀 Starting all servers..."
    cd ..

    # Start orchestrator
    cd orchestrator
    source venv/bin/activate
    python3 server.py &
    ORCHESTRATOR_PID=$!
    echo "   ✅ Orchestrator started (PID: $ORCHESTRATOR_PID)"

    # Start DeepSeek backend
    cd ../backends/deepseek-ocr
    source venv/bin/activate
    python3 server.py &
    DEEPSEEK_PID=$!
    echo "   ✅ DeepSeek backend started (PID: $DEEPSEEK_PID)"

    # Start Mineru backend
    cd ../mineru
    source venv/bin/activate
    python3 server.py &
    MINERU_PID=$!
    echo "   ✅ Mineru backend started (PID: $MINERU_PID)"

    echo ""
    echo "✅ Multi-backend deployment complete!"
    echo "🌐 Access points:"
    echo "   - Orchestrator: http://localhost:8080"
    echo "   - DeepSeek: http://localhost:5000"
    echo "   - Mineru: http://localhost:5001"
    echo ""
    echo "📊 Server PIDs:"
    echo "   - Orchestrator: $ORCHESTRATOR_PID"
    echo "   - DeepSeek: $DEEPSEEK_PID"
    echo "   - Mineru: $MINERU_PID"
EOF

echo ""
echo "✅ Multi-backend deployment completed!"
echo "🌐 Access points:"
echo "   - Orchestrator: http://localhost:8080"
echo "   - DeepSeek: http://localhost:5000"
echo "   - Mineru: http://localhost:5001"