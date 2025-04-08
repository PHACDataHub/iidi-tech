#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

if [[ -n "${CODESPACE_NAME}" ]]; then
  export IIDI_NGINX_HOST="https://${CODESPACE_NAME}-8080.app.github.dev"
else
  export IIDI_NGINX_HOST="http://localhost:8080"
fi

# add to .bashrc and .zshrc for codespaces session, to persist in new shells
echo "export IIDI_NGINX_HOST=\"${IIDI_NGINX_HOST}\"" >> ~/.bashrc
echo "export IIDI_NGINX_HOST=\"${IIDI_NGINX_HOST}\"" >> ~/.zshrc

npm run ci:all