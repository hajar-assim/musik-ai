#!/bin/bash
# file: start_vault.sh

VAULT_LOG="/tmp/vault.log"

# make sure the required env vars exist
: "${YOUTUBE_API_KEY:?need to set YOUTUBE_API_KEY}"
: "${SPOTIFY_CLIENT_ID:?need to set SPOTIFY_CLIENT_ID}"
: "${SPOTIFY_CLIENT_SECRET:?need to set SPOTIFY_CLIENT_SECRET}"

# start Vault in dev mode in background
vault server -dev > $VAULT_LOG 2>&1 &

# wait until Vault writes the root token
echo "Waiting for Vault to start..."
while ! grep -q 'Root Token:' $VAULT_LOG; do
    sleep 1
done

# extract the root token
VAULT_TOKEN=$(grep 'Root Token:' $VAULT_LOG | awk '{print $3}')

# export environment variables for this shell
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN
echo "Vault dev server started."
echo "VAULT_ADDR=$VAULT_ADDR"
echo "VAULT_TOKEN=$VAULT_TOKEN"

# populate secrets using the existing env vars
vault kv put secret/api-keys/youtube YOUTUBE_API_KEY="$YOUTUBE_API_KEY"
vault kv put secret/api-keys/spotify SPOTIFY_CLIENT_ID="$SPOTIFY_CLIENT_ID" SPOTIFY_CLIENT_SECRET="$SPOTIFY_CLIENT_SECRET"

echo "Secrets have been added."

