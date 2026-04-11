#!/bin/bash
# Single command untuk create verification file di VPS
# Copy paste semua command ini ke PuTTY setelah login

echo "Creating Google verification file..."
echo "google-site-verification: google25bce93832cdac80.html" > /var/www/cryptomentor/google25bce93832cdac80.html && \
chmod 644 /var/www/cryptomentor/google25bce93832cdac80.html && \
chown www-data:www-data /var/www/cryptomentor/google25bce93832cdac80.html && \
echo "✅ File created!" && \
echo "" && \
echo "📄 File content:" && \
cat /var/www/cryptomentor/google25bce93832cdac80.html && \
echo "" && \
echo "🔗 Testing URL..." && \
curl -s https://cryptomentor.id/google25bce93832cdac80.html && \
echo "" && \
echo "" && \
echo "========================================" && \
echo "✅ SUCCESS! File is ready" && \
echo "========================================" && \
echo "" && \
echo "Next: Go to Google Search Console and click VERIFIKASI"
