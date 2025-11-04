from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pdf_processor_pikepdf import PDFVectorProcessorPikePDF
import os
from typing import Optional

app = FastAPI(
    title="PDF Dark Mode Converter API",
    description="Vector-based PDF dark mode conversion API that preserves text quality",
    version="2.0.0"
)

# Configure CORS to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "PDF Dark Mode Converter API is running",
        "version": "2.0.0",
        "features": ["vector-preservation", "text-searchability", "multiple-themes"]
    }


@app.post("/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    theme: str = Form("classic")
):
    """
    Convert a PDF to dark mode while preserving vector data.

    Args:
        file: PDF file to convert
        theme: Dark mode theme (classic, claude, chatgpt, sepia, midnight, forest)

    Returns:
        Converted PDF file
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF"
        )

    # Validate theme
    valid_themes = ["classic", "claude", "chatgpt", "sepia", "midnight", "forest"]
    if theme not in valid_themes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid theme. Must be one of: {', '.join(valid_themes)}"
        )

    try:
        # Read the uploaded file
        input_bytes = await file.read()

        # Process the PDF - using high-res rasterization for reliability
        processor = PDFVectorProcessorPikePDF(theme=theme)
        output_bytes = processor.process_pdf(input_bytes)

        # Generate output filename
        original_name = file.filename.replace('.pdf', '')
        output_filename = f"{original_name}_{theme}_dark.pdf"

        # Return the processed PDF
        return Response(
            content=output_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{output_filename}"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )


@app.get("/themes")
async def get_themes():
    """Get available dark mode themes"""
    return {
        "themes": [
            {
                "id": "classic",
                "name": "True Black (Classic Inversion)",
                "background": {"r": 0, "g": 0, "b": 0}
            },
            {
                "id": "claude",
                "name": "Claude Warm",
                "background": {"r": 42, "g": 37, "b": 34}
            },
            {
                "id": "chatgpt",
                "name": "ChatGPT Cool",
                "background": {"r": 52, "g": 53, "b": 65}
            },
            {
                "id": "sepia",
                "name": "Sepia Dark",
                "background": {"r": 40, "g": 35, "b": 25}
            },
            {
                "id": "midnight",
                "name": "Midnight Blue",
                "background": {"r": 25, "g": 30, "b": 45}
            },
            {
                "id": "forest",
                "name": "Forest Green",
                "background": {"r": 25, "g": 35, "b": 30}
            }
        ]
    }


if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))

    print(f"""
    ========================================================
    PDF Dark Mode Converter API - Vector Edition
    Running on: http://localhost:{port}
    Docs: http://localhost:{port}/docs
    ========================================================
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
