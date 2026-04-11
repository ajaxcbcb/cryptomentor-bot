#!/bin/bash
# Script untuk upload file verification Google yang baru

echo "========================================"
echo "📤 Upload Google Verification File"
echo "========================================"

# File details
FILENAME="google25bce93832cdac80.html"
CONTENT="google-site-verification: google25bce93832cdac80.html"
VPS_USER="root"
VPS_IP="147.93.156.165"
VPS_PATH="/var/www/cryptomentor"

echo ""
echo "📝 Creating verification file locally..."
echo "$CONTENT" > "$FILENAME"
echo "✅ File created: $FILENAME"

echo ""
echo "📤 Uploading to VPS..."
scp "$FILENAME" "$VPS_USER@$VPS_IP:$VPS_PATH/"

if [ $? -eq 0 ]; then
    echo "✅ File uploaded successfully!"
    
    echo ""
    echo "🔧 Setting permissions on VPS..."
    ssh "$VPS_USER@$VPS_IP" "chmod 644 $VPS_PATH/$FILENAME && chown www-data:www-data $VPS_PATH/$FILENAME"
    
    echo ""
    echo "✅ Done! Testing URL..."
    echo ""
    
    # Test URL
    sleep 2
    curl -s "https://cryptomentor.id/$FILENAME"
    
    echo ""
    echo ""
    echo "========================================"
    echo "✅ Verification file ready!"
    echo "========================================"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Kembali ke Google Search Console"
    echo "   2. Klik tombol 'VERIFIKASI'"
    echo "   3. Selesai!"
    echo ""
    echo "🔗 Test URL: https://cryptomentor.id/$FILENAME"
    
else
    echo "❌ Upload failed!"
    echo "Please check your SSH connection"
fi

# Cleanup local file
rm -f "$FILENAME"
