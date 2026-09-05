#!/bin/sh
set -eu

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 <input.pdf> [output.md]" >&2
  exit 2
fi

input=$1
case "$input" in
  *.pdf|*.PDF) ;;
  *) echo "Input must be a PDF file: $input" >&2; exit 2 ;;
esac

if [ ! -f "$input" ]; then
  echo "PDF file not found: $input" >&2
  exit 1
fi

if [ "$#" -eq 2 ]; then
  output=$2
else
  output=${input%.*}.md
fi

if command -v markitdown >/dev/null 2>&1; then
  markitdown "$input" -o "$output"
elif command -v uvx >/dev/null 2>&1; then
  uvx --from 'markitdown[pdf]' markitdown "$input" -o "$output"
else
  echo "Neither markitdown nor uvx is available. Install markitdown[pdf] or uv first." >&2
  exit 1
fi

if [ ! -s "$output" ]; then
  echo "Conversion produced an empty Markdown file: $output" >&2
  exit 1
fi

printf '%s\n' "$output"
