#!/usr/bin/env python3
"""
Convert fadebender catalog markdown files to HTML for Vertex AI Search
"""
import markdown
from pathlib import Path

def convert_md_to_html(md_file: Path) -> Path:
    """Convert a single markdown file to HTML"""
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert to HTML with extensions
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
        h1, h2, h3, h4 {{ color: #333; margin-top: 1.5em; }}
        ul, ol {{ margin: 1em 0; padding-left: 2em; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

    # Create output path (same location, .html extension)
    html_file = md_file.with_suffix('.html')

    # Write HTML file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_full)

    return html_file


def main():
    fadebender_dir = Path('knowledge/fadebender')

    files_to_convert = [
        fadebender_dir / 'user-guide.md',
        fadebender_dir / 'device-catalog.md',
        fadebender_dir / 'preset-catalog.md',
    ]

    print("=" * 70)
    print("CONVERTING FADEBENDER CATALOGS TO HTML")
    print("=" * 70)
    print()

    for md_file in files_to_convert:
        if not md_file.exists():
            print(f"⚠️  {md_file.name} not found, skipping")
            continue

        try:
            html_file = convert_md_to_html(md_file)
            file_size = html_file.stat().st_size / 1024
            print(f"✓ {md_file.name} → {html_file.name} ({file_size:.1f} KB)")
        except Exception as e:
            print(f"❌ Error converting {md_file.name}: {e}")

    print()
    print("=" * 70)
    print("✅ CONVERSION COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Upload HTML files to GCS")
    print("2. Trigger Vertex AI Search import with HTML files")


if __name__ == '__main__':
    main()
