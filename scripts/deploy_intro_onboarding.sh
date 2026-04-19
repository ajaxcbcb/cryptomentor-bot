#!/usr/bin/env bash
set -euo pipefail

# One-shot deploy helper for intro.cryptomentor.id onboarding deck
# Usage:
#   VPS_HOST=147.93.156.165 VPS_USER=root ./scripts/deploy_intro_onboarding.sh
# Optional SSL (recommended after DNS is live):
#   DOMAIN=intro.cryptomentor.id EMAIL=admin@cryptomentor.id ISSUE_SSL=1 ./scripts/deploy_intro_onboarding.sh

VPS_HOST="${VPS_HOST:-147.93.156.165}"
VPS_USER="${VPS_USER:-root}"
VPS_PORT="${VPS_PORT:-22}"
DOMAIN="${DOMAIN:-intro.cryptomentor.id}"
EMAIL="${EMAIL:-admin@cryptomentor.id}"
ISSUE_SSL="${ISSUE_SSL:-0}"
# Backward-compatible: ROOT_DIR still works as override, but default is nginx-safe.
SITE_ROOT="${SITE_ROOT:-${ROOT_DIR:-/var/www/intro-cryptomentor}}"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_CONF="/etc/nginx/sites-available/intro-cryptomentor.conf"
TARGET_ENABLED="/etc/nginx/sites-enabled/intro-cryptomentor.conf"

if [[ "$SITE_ROOT" == /root/* ]]; then
  echo "WARNING: SITE_ROOT is under /root (${SITE_ROOT}). nginx may not read it unless permissions are explicitly fixed."
fi

cd "$REPO_ROOT/website-frontend"
echo "[1/9] Building frontend..."
npm run build

if [[ ! -f "$REPO_ROOT/website-frontend/dist/cryptomentor-onboarding-deck.html" ]]; then
  echo "ERROR: dist/cryptomentor-onboarding-deck.html not found after build."
  exit 1
fi

if [[ ! -f "$REPO_ROOT/website-frontend/dist/intro.html" ]]; then
  echo "ERROR: dist/intro.html not found after build."
  exit 1
fi

cd "$REPO_ROOT"
echo "[2/9] Creating VPS site root + uploading dist files to ${VPS_USER}@${VPS_HOST}:${SITE_ROOT} ..."
tar -C "$REPO_ROOT/website-frontend/dist" -cf - . | ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" \
  "mkdir -p '${SITE_ROOT}' && tar -xf - -C '${SITE_ROOT}' && chmod -R a+rX '${SITE_ROOT}'"

echo "[3/9] Writing HTTP nginx config for ${DOMAIN} (safe first deploy) ..."
ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" "cat >'${TARGET_CONF}' <<'NGINX'
server {
    listen 80;
    server_name ${DOMAIN};

    root ${SITE_ROOT};
    index index.html;

    location = / {
        return 302 /intro.html;
    }

    location / {
        try_files \$uri \$uri/ =404;
    }
}
NGINX"

echo "[4/9] Disabling conflicting nginx sites that also claim ${DOMAIN} ..."
ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" "set -euo pipefail
for enabled_path in /etc/nginx/sites-enabled/*; do
  [[ -e \"\$enabled_path\" ]] || continue
  resolved_path=\$(readlink -f \"\$enabled_path\" || true)
  [[ \"\$resolved_path\" == \"${TARGET_CONF}\" ]] && continue
  [[ -f \"\$resolved_path\" ]] || continue
  if grep -q 'server_name' \"\$resolved_path\" && grep -Fq '${DOMAIN}' \"\$resolved_path\"; then
    echo \"Disabled conflicting site: \$enabled_path -> \$resolved_path\"
    rm -f \"\$enabled_path\"
  fi
done"

echo "[5/9] Enabling site + nginx reload ..."
ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" "ln -sfn '${TARGET_CONF}' '${TARGET_ENABLED}' && nginx -t && systemctl reload nginx"

echo "[6/9] Verifying files exist on VPS ..."
ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" "ls -la '${SITE_ROOT}/intro.html' '${SITE_ROOT}/cryptomentor-onboarding-deck.html'"

echo "[7/9] Verifying nginx routing locally on VPS ..."
ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" "set -euo pipefail
status_root=\$(curl -sS -o /dev/null -I -H 'Host: ${DOMAIN}' -w '%{http_code}' http://127.0.0.1/)
status_intro=\$(curl -sS -o /dev/null -I -H 'Host: ${DOMAIN}' -w '%{http_code}' http://127.0.0.1/intro.html)
status_deck=\$(curl -sS -o /dev/null -I -H 'Host: ${DOMAIN}' -w '%{http_code}' http://127.0.0.1/cryptomentor-onboarding-deck.html)
echo \"HTTP / status=\${status_root}\"
echo \"HTTP /intro.html status=\${status_intro}\"
echo \"HTTP /cryptomentor-onboarding-deck.html status=\${status_deck}\"
if [[ \"\${status_root}\" != \"302\" ]]; then
  echo \"ERROR: expected 302 on / but got \${status_root}\"
  exit 1
fi
if [[ \"\${status_intro}\" != \"200\" ]]; then
  echo \"ERROR: expected 200 on intro.html but got \${status_intro}\"
  exit 1
fi
if [[ \"\${status_deck}\" != \"200\" ]]; then
  echo \"ERROR: expected 200 on onboarding deck but got \${status_deck}\"
  exit 1
fi"

has_existing_cert="$(ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" "if [[ -f '${CERT_DIR}/fullchain.pem' && -f '${CERT_DIR}/privkey.pem' ]]; then echo 1; else echo 0; fi")"

if [[ "$ISSUE_SSL" == "1" ]]; then
  echo "[8/10] Requesting Let's Encrypt certificate for ${DOMAIN} ..."
  ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" \
    "certbot certonly --webroot -w '${SITE_ROOT}' -d '${DOMAIN}' --non-interactive --agree-tos -m '${EMAIL}'"
  has_existing_cert="1"
fi

if [[ "$has_existing_cert" == "1" ]]; then
  if [[ "$ISSUE_SSL" == "1" ]]; then
    echo "[9/10] Rewriting config to force HTTPS + reloading nginx ..."
  else
    echo "[8/10] Existing certificate found. Enabling HTTPS + reloading nginx ..."
  fi
  ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" "cat >'${TARGET_CONF}' <<'NGINX'
server {
    listen 80;
    server_name ${DOMAIN};
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};

    root ${SITE_ROOT};
    index index.html;

    location = / {
        return 302 /intro.html;
    }

    location / {
        try_files \$uri \$uri/ =404;
    }

    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
}
NGINX
nginx -t && systemctl reload nginx"

  if [[ "$ISSUE_SSL" == "1" ]]; then
    echo "[10/10] Verifying HTTPS routing + SNI mapping ..."
  else
    echo "[9/10] Verifying HTTPS routing + SNI mapping ..."
  fi
  ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" "set -euo pipefail
status_https_root=\$(curl -ksS -o /dev/null -I --resolve '${DOMAIN}:443:127.0.0.1' -w '%{http_code}' https://${DOMAIN}/)
status_https_intro=\$(curl -ksS -o /dev/null -I --resolve '${DOMAIN}:443:127.0.0.1' -w '%{http_code}' https://${DOMAIN}/intro.html)
status_https_deck=\$(curl -ksS -o /dev/null -I --resolve '${DOMAIN}:443:127.0.0.1' -w '%{http_code}' https://${DOMAIN}/cryptomentor-onboarding-deck.html)
deck_body=\$(curl -ksS --resolve '${DOMAIN}:443:127.0.0.1' https://${DOMAIN}/cryptomentor-onboarding-deck.html || true)
echo \"HTTPS / status=\${status_https_root}\"
echo \"HTTPS /intro.html status=\${status_https_intro}\"
echo \"HTTPS /cryptomentor-onboarding-deck.html status=\${status_https_deck}\"
if [[ \"\${status_https_root}\" != \"302\" ]]; then
  echo \"ERROR: expected 302 on HTTPS / but got \${status_https_root}\"
  exit 1
fi
if [[ \"\${status_https_intro}\" != \"200\" ]]; then
  echo \"ERROR: expected 200 on HTTPS intro.html but got \${status_https_intro}\"
  exit 1
fi
if [[ \"\${status_https_deck}\" != \"200\" ]]; then
  echo \"ERROR: expected 200 on HTTPS onboarding deck but got \${status_https_deck}\"
  exit 1
fi
if grep -Fq 'Invalid or missing token' <<< \"\${deck_body}\"; then
  echo \"ERROR: HTTPS intro domain is still routed to token-protected backend (invalid token response detected).\"
  exit 1
fi"
else
  echo "[8/9] SSL skipped (ISSUE_SSL=${ISSUE_SSL}) and no existing cert found."
  echo "[9/9] Verifying HTTPS is not misrouted to token-protected backend ..."
  ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" "set -euo pipefail
status_https_root=\$(curl -ksS -o /dev/null -I --resolve '${DOMAIN}:443:127.0.0.1' -w '%{http_code}' https://${DOMAIN}/ || true)
https_body=\$(curl -ksS --resolve '${DOMAIN}:443:127.0.0.1' https://${DOMAIN}/ || true)
echo \"HTTPS / status=\${status_https_root}\"
if grep -Fq 'Invalid or missing token' <<< \"\${https_body}\"; then
  echo \"ERROR: HTTPS currently resolves to token-protected backend for ${DOMAIN}.\"
  echo \"Fix: rerun with ISSUE_SSL=1 (after DNS is live) or install a dedicated ${DOMAIN} TLS vhost.\"
  exit 1
fi"
  echo "      Keep using HTTP for now: http://${DOMAIN}/"
  echo "      When DNS is stable, rerun with ISSUE_SSL=1 to enable HTTPS redirect."
fi

echo
echo "Done. Verify:"
echo "  http://${DOMAIN}/              → redirects to /intro.html"
echo "  http://${DOMAIN}/intro.html"
echo "  http://${DOMAIN}/cryptomentor-onboarding-deck.html"
if [[ "$ISSUE_SSL" == "1" || "$has_existing_cert" == "1" ]]; then
  echo "  https://${DOMAIN}/             → redirects to /intro.html"
  echo "  https://${DOMAIN}/intro.html"
  echo "  https://${DOMAIN}/cryptomentor-onboarding-deck.html"
fi
