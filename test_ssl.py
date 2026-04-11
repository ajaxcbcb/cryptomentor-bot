#!/usr/bin/env python3
"""Test SSL certificate for cryptomentor.id"""

import ssl
import socket
import datetime

def test_ssl(hostname):
    print(f"Testing SSL for: {hostname}")
    print("=" * 60)
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        # Connect
        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                
                print("✅ SSL Connection Successful!")
                print()
                
                # Subject
                subject = dict(x[0] for x in cert['subject'])
                print(f"📋 Issued to: {subject.get('commonName', 'N/A')}")
                
                # Issuer
                issuer = dict(x[0] for x in cert['issuer'])
                print(f"🏢 Issued by: {issuer.get('organizationName', 'N/A')}")
                
                # Validity
                not_before = cert['notBefore']
                not_after = cert['notAfter']
                print(f"📅 Valid from: {not_before}")
                print(f"📅 Valid until: {not_after}")
                
                # Check expiry
                expiry = datetime.datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                days_left = (expiry - datetime.datetime.now()).days
                print(f"⏰ Days until expiry: {days_left}")
                
                # Subject Alternative Names (SANs)
                sans = cert.get('subjectAltName', [])
                print(f"\n🌐 Domains covered by this certificate:")
                for san_type, san_value in sans:
                    if san_type == 'DNS':
                        print(f"   - {san_value}")
                
                # Check if www is covered
                san_domains = [san[1] for san in sans if san[0] == 'DNS']
                print()
                print("=" * 60)
                print("📊 ANALYSIS:")
                print("=" * 60)
                
                if hostname in san_domains:
                    print(f"✅ {hostname} is covered")
                else:
                    print(f"❌ {hostname} is NOT covered")
                
                www_hostname = f"www.{hostname}"
                if www_hostname in san_domains:
                    print(f"✅ {www_hostname} is covered")
                else:
                    print(f"❌ {www_hostname} is NOT covered")
                    print(f"\n⚠️  This is why Google Search Console fails for www!")
                    print(f"   You need to add www to the SSL certificate.")
                
                return True
                
    except ssl.SSLError as e:
        print(f"❌ SSL Error: {e}")
        return False
    except socket.timeout:
        print(f"❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_ssl("cryptomentor.id")
