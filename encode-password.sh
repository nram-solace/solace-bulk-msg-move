#!/bin/bash

# Check arg
if [ $# -eq 0 ]; then
    echo "Usage: $0 <password>"
    echo "Example: $0 mypassword"
    exit 1
fi

PASSWORD="$1"
ENCODED="ENC:$(echo -n "$PASSWORD" | base64)"

echo "Original password: $PASSWORD"
echo "Encoded  password: $ENCODED" 