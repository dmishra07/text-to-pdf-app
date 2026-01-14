from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io
import textwrap
from datetime import datetime


# Initialize a Flask application
app = Flask(__name__)


def build_pdf(title: str, body: str) -> io.BytesIO:
    """Create a PDF from a title and body text using reportlab.

    This helper function sets up a PDF canvas with sensible margins and
    wraps paragraph text so that lines do not exceed the page width.

    Args:
        title: The document title displayed at the top of the first page.
        body: The main content of the document.

    Returns:
        A BytesIO object containing the generated PDF file.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    # Define margins in inches
    left = 1 * inch
    right = 1 * inch
    top = 1 * inch
    bottom = 1 * inch

    # Start drawing near the top of the page
    y = height - top

    # Title
    c.setFont("Helvetica-Bold", 16)
    title_text = title.strip() or "Document"
    c.drawString(left, y, title_text)
    y -= 0.35 * inch

    # Meta line (timestamp)
    c.setFont("Helvetica", 9)
    c.drawString(left, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 0.25 * inch

    # Body text settings
    c.setFont("Helvetica", 11)

    # Calculate maximum characters per line based on available width.
    # Reportlab does not handle automatic wrapping, so we use textwrap.
    usable_width = width - left - right
    # Estimate characters per inch for 11pt font; adjust factor as needed.
    max_chars = int((usable_width / inch) * 6.1)

    lines = []
    # Split paragraphs into lines with wrapping
    for paragraph in (body or "").splitlines():
        if paragraph.strip() == "":
            # Represent a blank line between paragraphs
            lines.append("")
            continue
        wrapped = textwrap.wrap(paragraph, width=max_chars)
        lines.extend(wrapped if wrapped else [""])

    # Line height in points
    line_height = 14
    for line in lines:
        # If we've reached the bottom margin, start a new page
        if y < bottom:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - top
        c.drawString(left, y, line)
        y -= line_height

    # Finish the page and save the PDF into the buffer
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer


@app.get("/")
def index():
    """Render the index page with a form for users to input title and body."""
    return render_template("index.html")


@app.post("/generate")
def generate():
    """Handle form submission, generate a PDF and return it for download."""
    title = request.form.get("title", "")
    body = request.form.get("body", "")

    pdf_bytes = build_pdf(title=title, body=body)

    filename = (title.strip() or "document").replace(" ", "_")
    return send_file(
        pdf_bytes,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{filename}.pdf",
    )


if __name__ == "__main__":
    # Run in development mode when executed directly
    app.run(host="0.0.0.0", port=8080, debug=True)
