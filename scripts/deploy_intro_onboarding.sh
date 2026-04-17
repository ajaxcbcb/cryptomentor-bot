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
        return 302 /cryptomentor-onboarding-deck.html;
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

echo "[6/9] Verifying file exists on VPS ..."
ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" "ls -la '${SITE_ROOT}/cryptomentor-onboarding-deck.html'"

echo "[7/9] Verifying nginx routing locally on VPS ..."
ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" "set -euo pipefail
status_root=\$(curl -sS -o /dev/null -I -H 'Host: ${DOMAIN}' -w '%{http_code}' http://127.0.0.1/)
status_file=\$(curl -sS -o /dev/null -I -H 'Host: ${DOMAIN}' -w '%{http_code}' http://127.0.0.1/cryptomentor-onboarding-deck.html)
echo \"HTTP / status=\${status_root}\"
echo \"HTTP /cryptomentor-onboarding-deck.html status=\${status_file}\"
if [[ \"\${status_root}\" != \"302\" ]]; then
  echo \"ERROR: expected 302 on / but got \${status_root}\"
  exit 1
fi
if [[ \"\${status_file}\" != \"200\" ]]; then
  echo \"ERROR: expected 200 on onboarding file but got \${status_file}\"
  exit 1
fi"

if [[ "$ISSUE_SSL" == "1" ]]; then
  echo "[8/9] Requesting Let's Encrypt certificate for ${DOMAIN} ..."
  ssh -p "$VPS_PORT" "${VPS_USER}@${VPS_HOST}" \
    "certbot certonly --webroot -w '${SITE_ROOT}' -d '${DOMAIN}' --non-interactive --agree-tos -m '${EMAIL}'"

  echo "[9/9] Rewriting config to force HTTPS + reloading nginx ..."
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
        return 302 /cryptomentor-onboarding-deck.html;
    }

    location / {
        try_files \$uri \$uri/ =404;
    }

    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
}
NGINX
nginx -t && systemctl reload nginx"
else
  echo "[8/9] SSL skipped (ISSUE_SSL=${ISSUE_SSL})."
  echo "[9/9] Keep using HTTP for now: http://${DOMAIN}/"
  echo "      When DNS is stable, rerun with ISSUE_SSL=1 to enable HTTPS redirect."
fi

echo
echo "Done. Verify:"
echo "  http://${DOMAIN}/"
echo "  http://${DOMAIN}/cryptomentor-onboarding-deck.html"
if [[ "$ISSUE_SSL" == "1" ]]; then
  echo "  https://${DOMAIN}/"
  echo "  https://${DOMAIN}/cryptomentor-onboarding-deck.html"
fi
