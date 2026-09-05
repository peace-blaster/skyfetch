#!/bin/sh
set -eu
# Set PREFIX to install elsewhere (e.g. PREFIX=/usr/local).
prefix=${PREFIX:-"$HOME/.local"}
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
command -v python3 >/dev/null 2>&1 || { echo 'Python 3.8+ is required.' >&2; exit 1; }
python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))' || { echo 'Python 3.8+ is required.' >&2; exit 1; }
mkdir -p "$prefix/bin"
cp "$script_dir/skyfetch" "$prefix/bin/skyfetch"
chmod 755 "$prefix/bin/skyfetch"
printf 'Installed %s/bin/skyfetch\n' "$prefix"
case ":$PATH:" in
  *":$prefix/bin:"*) ;;
  *) printf 'Add %s/bin to your PATH. For the default install, add this to your shell profile:\n  export PATH="$HOME/.local/bin:$PATH"\n' "$prefix" ;;
esac
