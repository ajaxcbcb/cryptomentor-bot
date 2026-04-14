#!/bin/bash
# Script untuk menambahkan www subdomain ke SSL certificate

echo "========================================"
echo "🔒 Fix WWW SSL Certificate"
echo "========================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check DNS first
echo ""
echo "🔍 Checking DNS for www.cryptomentor.id..."
if host www.cryptomentor.id > /dev/null 2>&1; then
    echo "✅ DNS resolved successfully"
    host www.cryptomentor.id
else
    echo "❌ DNS not resolved yet"
    echo "⚠️  Please wait for DNS propagation (5-30 minutes)"
    echo "⚠️  Check with: host www.cryptomentor.id"
    exit 1
fi

# Backup current nginx config
echo ""
echo "📦 Backing up nginx config..."
cp /etc/nginx/sites-available/cryptomentor /etc/nginx/sites-available/cryptomentor.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"

# Run certbot to add www subdomain
echo ""
echo "🔒 Running certbot to add www subdomain..."
certbot --nginx -d cryptomentor.id -d www.cryptomentor.id --non-interactive --agree-tos --redirect

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL certificate updated successfully!"
    echo ""
    echo "🔄 Reloading nginx..."
    systemctl reload nginx
    
    echo ""
    echo "✅ Done! Testing URLs..."
    echo ""
    
    # Test URLs
    echo "Testing https://cryptomentor.id..."
    curl -I https://cryptomentor.id 2>&1 | head -n 1
    
    echo "Testing https://www.cryptomentor.id..."
    curl -I https://www.cryptomentor.id 2>&1 | head -n 1
    
    echo ""
    echo "========================================"
    echo "✅ WWW subdomain is now ready!"
    echo "========================================"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Verify in Google Search Console"
    echo "   2. Test: https://www.cryptomentor.id/googlee8915e6154b40498.html"
    
else
    echo ""
    echo "❌ Certbot failed!"
    echo "⚠️  Please check:"
    echo "   1. DNS is properly configured"
    echo "   2. Port 80 and 443 are open"
    echo "   3. Nginx is running"
fi
