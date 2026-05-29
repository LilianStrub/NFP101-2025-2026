#!/usr/bin/env bash
# Génère docs/documentation.pdf à partir de docs/documentation.md.
#
# Prérequis : pandoc + un moteur LaTeX Unicode (xelatex, fourni par MacTeX /
# TeX Live). Installation macOS : `brew install pandoc` puis MacTeX.
#
# Usage : bash docs/build_pdf.sh
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

pandoc "$DIR/documentation.md" -o "$DIR/documentation.pdf" \
  --pdf-engine=xelatex \
  --toc --toc-depth=2 \
  -V geometry:margin=2.4cm \
  -V mainfont="Helvetica Neue" \
  -V monofont="Menlo" \
  -V lang=fr \
  -V colorlinks=true -V linkcolor=teal -V urlcolor=teal

echo "✓ docs/documentation.pdf généré."
