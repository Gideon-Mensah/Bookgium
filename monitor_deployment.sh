#!/bin/bash
# Script to monitor Render deployment and test login endpoints

echo "=== Monitoring Render Deployment ===\n"

# Function to test an endpoint
test_endpoint() {
    local url=$1
    local description=$2
    echo "Testing $description at $url..."
    
    # Get HTTP status code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$status_code" = "200" ]; then
        echo "✓ $description: OK (200)"
        return 0
    else
        echo "✗ $description: HTTP $status_code"
        return 1
    fi
}

echo "Waiting for deployment to complete (this usually takes 2-5 minutes)..."
echo "You can monitor the deployment at: https://dashboard.render.com/\n"

# Wait a bit for deployment to start
sleep 30

# Test endpoints periodically
max_attempts=20
attempt=1

while [ $attempt -le $max_attempts ]; do
    echo "\n--- Attempt $attempt/$max_attempts ---"
    
    # Test main site
    if test_endpoint "https://bookgium.onrender.com/" "Main site"; then
        echo "✓ Main site is responding"
        
        # Test admin login page
        if test_endpoint "https://bookgium.onrender.com/admin/login/" "Admin login page"; then
            echo "✓ Admin login page is accessible"
            
            # Test users login page
            if test_endpoint "https://bookgium.onrender.com/users/login/" "Users login page"; then
                echo "\n🎉 SUCCESS! Both login pages are working!"
                echo "\nYou can now test authentication with:"
                echo "  Username: geolumia67"
                echo "  Password: Metrotv111l2@"
                echo "\nLogin URLs:"
                echo "  Admin: https://bookgium.onrender.com/admin/login/"
                echo "  Users: https://bookgium.onrender.com/users/login/"
                exit 0
            fi
        fi
    fi
    
    echo "Deployment still in progress... waiting 30 seconds"
    sleep 30
    attempt=$((attempt + 1))
done

echo "\n⚠️  Deployment is taking longer than expected."
echo "Please check the Render dashboard for deployment logs:"
echo "https://dashboard.render.com/"
