#!/bin/sh
set -eu
prefix=${PREFIX:-"$HOME/.local"}
if [ -f "$prefix/bin/skyfetch" ]; then
    rm -- "$prefix/bin/skyfetch"
    printf 'Removed %s/bin/skyfetch\n' "$prefix"
else
    printf 'No skyfetch executable found at %s/bin/skyfetch\n' "$prefix"
fi
printf 'Saved settings and cache were kept. See README.md to remove them.\n'
