"""Create a test PDF with dark blue lines."""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Create test PDF
c = canvas.Canvas("test_darkblue.pdf", pagesize=letter)

# White background (default)
# Draw black text
c.setFillColorRGB(0, 0, 0)
c.drawString(100, 700, "This is black text that should become white")

# Draw dark blue line - RGB(0, 0, 128) = (0, 0, 0.5019)
c.setStrokeColorRGB(0, 0, 0.5019)
c.setLineWidth(5)
c.line(100, 650, 500, 650)

# Draw dark blue rectangle
c.setFillColorRGB(0, 0, 0.5019)
c.rect(100, 500, 200, 100, fill=True, stroke=False)

# Draw another dark blue text
c.setFillColorRGB(0, 0, 0.5019)
c.drawString(100, 400, "This is dark blue text")

c.save()
print("Created test_darkblue.pdf with dark blue RGB(0, 0, 128)")
