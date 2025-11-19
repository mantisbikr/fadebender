#!/usr/bin/env python3
"""
Convert all markdown files in knowledge/ to HTML for Vertex AI Search
"""
import os
import sys
from pathlib import Path
import markdown

def convert_md_to_html(md_file: Path, output_dir: Path) -> Path:
    """Convert a single markdown file to HTML"""
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert to HTML with extensions for better formatting
    html_content = markdown.markdown(
        md_content,
        extensions=[
            'extra',      # Tables, fenced code blocks, etc.
            'codehilite', # Syntax highlighting
            'toc',        # Table of contents
            'nl2br',      # Newline to <br>
        ]
    )

    # Wrap in basic HTML structure
    html_full = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{md_file.stem}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 900px; margin: 0 auto; }}
        code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

    # Create output path (preserve directory structure, change extension)
    relative_path = md_file.relative_to(Path('../knowledge'))
    output_file = output_dir / relative_path.with_suffix('.html')

    # Create parent directories if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_full)

    return output_file


def main():
    knowledge_dir = Path('../knowledge')
    output_dir = Path('../knowledge-html')

    # Remove output dir if it exists and recreate
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all markdown files
    md_files = list(knowledge_dir.glob('**/*.md'))

    print(f"Found {len(md_files)} markdown files")
    print(f"Converting to HTML in: {output_dir}")
    print("-" * 60)

    converted = 0
    skipped = 0

    for md_file in md_files:
        # Skip .DS_Store and hidden files
        if md_file.name.startswith('.'):
            skipped += 1
            continue

        try:
            output_file = convert_md_to_html(md_file, output_dir)
            converted += 1
            if converted % 50 == 0:
                print(f"Converted {converted}/{len(md_files)} files...")
        except Exception as e:
            print(f"ERROR converting {md_file}: {e}", file=sys.stderr)
            skipped += 1

    print("-" * 60)
    print(f"✅ Converted: {converted} files")
    print(f"⏭  Skipped: {skipped} files")
    print(f"📁 Output directory: {output_dir.absolute()}")


if __name__ == '__main__':
    main()
