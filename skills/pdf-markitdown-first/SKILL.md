---
name: pdf-markitdown-first
description: Convert local PDF files to Markdown with Microsoft's MarkItDown before reading, extracting, summarizing, searching, or analyzing their contents. Use whenever a task requires inspecting a PDF; do not use for creating or editing PDFs.
---

# PDF via MarkItDown

For every local PDF that must be read:

1. Run `scripts/convert_pdf.sh <input.pdf> [output.md]` before inspecting the PDF's contents. If no output path is supplied, the script creates `<input-name>.md` beside the PDF.
2. Read, search, extract, summarize, or analyze the generated Markdown as the primary content source.
3. Keep the Markdown file unless the user asked for temporary output. Tell the user where it was written when it is a deliverable or useful for follow-up work.

Do not read the PDF directly first, including with PDF text extractors or page screenshots. It is fine to inspect filesystem metadata such as the filename and size in order to locate the input and choose an output path.

If `uvx` needs network access to obtain `markitdown[pdf]`, request the required approval. Never install packages globally as part of this workflow.

If conversion fails or the Markdown is empty or clearly incomplete, report the problem. Ask before using another PDF extraction or OCR method, because that would depart from the user's requested MarkItDown-first workflow. Visual inspection is allowed afterward only when the task specifically requires checking layout, images, or rendering that Markdown cannot represent.

The converter follows the official Microsoft MarkItDown CLI syntax: `markitdown input.pdf -o output.md`.
