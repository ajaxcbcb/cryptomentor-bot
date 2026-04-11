#!/usr/bin/env python3
"""
Script untuk mengecek apakah cryptomentor.id siap untuk Google Search Console verification
"""

import requests
import sys
from urllib.parse import urlparse

def check_url_accessibility(url):
    """Cek apakah URL bisa diakses"""
    print(f"\n🔍 Mengecek aksesibilitas: {url}")
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        print(f"   ✅ Status Code: {response.status_code}")
        print(f"   ✅ Final URL: {response.url}")
        print(f"   ✅ Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   ✅ Server: {response.headers.get('server', 'N/A')}")
        
        if response.status_code == 200:
            print(f"   ✅ Content Length: {len(response.text)} bytes")
            return True, response
        else:
            print(f"   ❌ Status code bukan 200")
            return False, response
    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error: {e}")
        return False, None
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: {e}")
        return False, None
    except requests.exceptions.Timeout as e:
        print(f"   ❌ Timeout: {e}")
        return False, None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None

def check_ssl_certificate(domain):
    """Cek SSL certificate"""
    print(f"\n🔒 Mengecek SSL Certificate untuk {domain}")
    try:
        import ssl
        import socket
        
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                print(f"   ✅ SSL Valid")
                print(f"   ✅ Issued to: {cert.get('subject', [[('commonName', 'N/A')]])[0][0][1]}")
                print(f"   ✅ Issued by: {cert.get('issuer', [[('organizationName', 'N/A')]])[0][0][1]}")
                print(f"   ✅ Valid until: {cert.get('notAfter', 'N/A')}")
                return True
    except Exception as e:
        print(f"   ❌ SSL Error: {e}")
        return False

def check_robots_txt(base_url):
    """Cek robots.txt"""
    print(f"\n🤖 Mengecek robots.txt")
    robots_url = f"{base_url}/robots.txt"
    try:
        response = requests.get(robots_url, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ robots.txt ditemukan")
            print(f"   📄 Content:\n{response.text[:500]}")
            return True
        else:
            print(f"   ⚠️  robots.txt tidak ditemukan (optional)")
            return False
    except Exception as e:
        print(f"   ⚠️  Error checking robots.txt: {e}")
        return False

def check_sitemap(base_url):
    """Cek sitemap.xml"""
    print(f"\n🗺️  Mengecek sitemap.xml")
    sitemap_url = f"{base_url}/sitemap.xml"
    try:
        response = requests.get(sitemap_url, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ sitemap.xml ditemukan")
            print(f"   📄 Content preview:\n{response.text[:300]}")
            return True
        else:
            print(f"   ⚠️  sitemap.xml tidak ditemukan (optional)")
            return False
    except Exception as e:
        print(f"   ⚠️  Error checking sitemap.xml: {e}")
        return False

def main():
    print("=" * 70)
    print("🔍 GOOGLE SEARCH CONSOLE VERIFICATION CHECKER")
    print("=" * 70)
    
    domain = "cryptomentor.id"
    urls_to_check = [
        f"https://{domain}",
        f"https://www.{domain}",
        f"http://{domain}",
        f"http://www.{domain}"
    ]
    
    results = {}
    
    # Check all URLs
    for url in urls_to_check:
        success, response = check_url_accessibility(url)
        results[url] = success
    
    # Check SSL
    ssl_ok = check_ssl_certificate(domain)
    
    # Check robots.txt and sitemap for main domain
    base_url = f"https://{domain}"
    robots_ok = check_robots_txt(base_url)
    sitemap_ok = check_sitemap(base_url)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY - READINESS FOR GOOGLE SEARCH CONSOLE")
    print("=" * 70)
    
    print("\n✅ URL Accessibility:")
    for url, status in results.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {url}")
    
    print(f"\n🔒 SSL Certificate: {'✅ Valid' if ssl_ok else '❌ Invalid'}")
    print(f"🤖 robots.txt: {'✅ Found' if robots_ok else '⚠️  Not found (optional)'}")
    print(f"🗺️  sitemap.xml: {'✅ Found' if sitemap_ok else '⚠️  Not found (optional)'}")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("💡 REKOMENDASI")
    print("=" * 70)
    
    if results.get(f"https://{domain}"):
        print(f"\n✅ SIAP untuk Google Search Console verification!")
        print(f"\n📝 Langkah selanjutnya:")
        print(f"   1. Buka Google Search Console: https://search.google.com/search-console")
        print(f"   2. Klik 'Add Property'")
        print(f"   3. Pilih 'URL prefix' dan masukkan: https://{domain}")
        print(f"   4. Pilih metode verifikasi:")
        print(f"      - HTML file upload (recommended)")
        print(f"      - HTML tag")
        print(f"      - Google Analytics")
        print(f"      - Google Tag Manager")
        print(f"      - Domain name provider (DNS)")
    else:
        print(f"\n❌ Belum siap untuk verification")
        print(f"\n🔧 Yang perlu diperbaiki:")
        if not results.get(f"https://{domain}"):
            print(f"   - HTTPS tidak bisa diakses")
        if not ssl_ok:
            print(f"   - SSL certificate bermasalah")
    
    # WWW redirect recommendation
    if results.get(f"https://{domain}") and not results.get(f"https://www.{domain}"):
        print(f"\n⚠️  www.{domain} tidak bisa diakses")
        print(f"   Rekomendasi: Setup redirect dari www ke non-www di nginx")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Dibatalkan oleh user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
