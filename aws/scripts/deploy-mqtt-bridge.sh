#!/bin/bash
# Deploy MQTT Bridge to EC2

set -e

echo "============================================"
echo "Deploying MQTT Bridge to EC2"
echo "============================================"
echo ""

# EC2 Configuration
EC2_IP="172.31.6.172"
EC2_USER="ubuntu"
EC2_KEY="~/.ssh/server.pem"  # Update this with your key path

echo "Step 1: Installing dependencies on EC2..."
ssh -i $EC2_KEY $EC2_USER@$EC2_IP << 'EOF'
    sudo apt update
    sudo apt install -y python3 python3-pip
    pip3 install paho-mqtt requests
EOF

echo ""
echo "Step 2: Copying MQTT bridge script..."
scp -i $EC2_KEY mqtt_bridge.py $EC2_USER@$EC2_IP:/home/ubuntu/

echo ""
echo "Step 3: Making script executable..."
ssh -i $EC2_KEY $EC2_USER@$EC2_IP << 'EOF'
    chmod +x /home/ubuntu/mqtt_bridge.py
EOF

echo ""
echo "Step 4: Installing systemd service..."
scp -i $EC2_KEY mqtt-bridge.service $EC2_USER@$EC2_IP:/tmp/
ssh -i $EC2_KEY $EC2_USER@$EC2_IP << 'EOF'
    sudo mv /tmp/mqtt-bridge.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable mqtt-bridge
    sudo systemctl restart mqtt-bridge
EOF

echo ""
echo "Step 5: Checking service status..."
ssh -i $EC2_KEY $EC2_USER@$EC2_IP << 'EOF'
    sudo systemctl status mqtt-bridge --no-pager
EOF

echo ""
echo "============================================"
echo "✓ MQTT Bridge deployed successfully!"
echo "============================================"
echo ""
echo "View logs:"
echo "  ssh -i $EC2_KEY $EC2_USER@$EC2_IP 'sudo tail -f /var/log/mqtt-bridge.log'"
echo ""
echo "Check status:"
echo "  ssh -i $EC2_KEY $EC2_USER@$EC2_IP 'sudo systemctl status mqtt-bridge'"
echo ""
