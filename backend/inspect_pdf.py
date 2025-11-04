"""Inspect PDF content streams to see color operators."""
import pikepdf
import sys

pdf_path = sys.argv[1] if len(sys.argv) > 1 else "test_darkblue_converted.pdf"

with pikepdf.open(pdf_path) as pdf:
    print(f"Inspecting: {pdf_path}")
    print(f"Pages: {len(pdf.pages)}\n")

    for i, page in enumerate(pdf.pages):
        print(f"=== Page {i+1} ===")

        if pikepdf.Name.Contents in page:
            contents = page.Contents

            if hasattr(contents, 'read_bytes'):
                content = contents.read_bytes().decode('latin-1', errors='ignore')
            else:
                content = ""
                for stream in contents:
                    content += stream.read_bytes().decode('latin-1', errors='ignore')

            # Find color operators
            import re

            # Find RGB operators
            rgb_ops = re.findall(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(rg|RG)', content)
            if rgb_ops:
                print("RGB Color Operators:")
                for r, g, b, op in rgb_ops[:10]:  # Show first 10
                    print(f"  {r} {g} {b} {op}")

            # Find grayscale
            gray_ops = re.findall(r'([\d.]+)\s+(g|G)\b', content)
            if gray_ops:
                print("Grayscale Operators:")
                for val, op in gray_ops[:10]:
                    print(f"  {val} {op}")

            print()
