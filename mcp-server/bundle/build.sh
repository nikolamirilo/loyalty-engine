#!/usr/bin/env bash
# Builds loyalty-engine-mcp.mcpb, the double-click installer for Claude Desktop.
#
#   ./bundle/build.sh
#
# --omit=dev because everything in the archive ships to the user's machine, and
# mcp-remote's dev tree is a few megabytes of it.
set -euo pipefail

cd "$(dirname "$0")"

npm install --omit=dev
npx --yes @anthropic-ai/mcpb pack . loyalty-engine-mcp.mcpb

echo
echo "Built $(pwd)/loyalty-engine-mcp.mcpb - drag it onto Claude Desktop to install."
