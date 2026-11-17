#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
SDK_SETUP="${HOME}/lynx_ws/src/sdk_deploy/install/setup.bash"
if [[ ! -f "$SDK_SETUP" ]]; then
  echo "Missing SDK overlay: $SDK_SETUP" >&2
  exit 2
fi
source "$SDK_SETUP"

cd "$(dirname "$0")"
count=0
for test_file in test_*.py; do
  echo
  echo "===== $test_file ====="
  python3 "$test_file"
  count=$((count + 1))
done

echo
echo "ALL $count SOFTWARE TEST SCRIPTS PASSED"
