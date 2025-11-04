#!/usr/bin/env python3
"""
Command-line interface for PDF dark mode converter.
Usage: python cli.py input.pdf output.pdf [theme]
"""

import sys
from pdf_processor_pikepdf import PDFVectorProcessorPikePDF

def main():
    if len(sys.argv) < 3:
        print("Usage: python cli.py input.pdf output.pdf [theme]")
        print("Available themes: classic, claude, chatgpt, sepia, midnight, forest")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    theme = sys.argv[3] if len(sys.argv) > 3 else "classic"

    print(f"Converting {input_path} to dark mode...")
    print(f"Theme: {theme}")
    print(f"Output: {output_path}")

    try:
        # Read input PDF
        with open(input_path, 'rb') as f:
            input_bytes = f.read()

        # Process
        processor = PDFVectorProcessorPikePDF(theme=theme)
        output_bytes = processor.process_pdf(input_bytes)

        # Write output PDF
        with open(output_path, 'wb') as f:
            f.write(output_bytes)

        print(f"SUCCESS: Successfully converted! Saved to {output_path}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
