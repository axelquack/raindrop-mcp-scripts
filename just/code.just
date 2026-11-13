# Code repository. Lives at just/code.just.
# The root justfile loads it with: import 'just/code.just'
#
# Live-infra rule (Axel, 2026-11-13): do not run raindrop_cleanup.py,
# raindrop_importer.py, or anything that calls the Raindrop API.
# Those scripts change bookmarks. python -m py_compile does not run them.
# There is no formatter and no package build.

# Syntax-check the three scripts. Does not execute them and does not call the API.
test:
    #!/usr/bin/env bash
    set -euo pipefail
    python3 -m py_compile raindrop_cleanup.py raindrop_importer.py raindrop_utils.py

# No package build. The syntax check is `just test`.
build:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "code: no package build; run just test for py_compile"

# No formatter is configured.
fmt:
    @echo "code: no formatter is configured"
