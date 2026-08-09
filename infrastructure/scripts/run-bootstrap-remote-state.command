#!/bin/bash
cd /Users/satish_byndr/Documents/workspace-ai/codestrata-platform || exit 1
export AWS_PROFILE=codestrata_infra
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy NO_PROXY no_proxy
./infrastructure/scripts/bootstrap-remote-state.sh
echo "EXIT:$?"
echo "Press enter to close..."
read -r _
