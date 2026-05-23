# parser.py — Extract text from a PDF resume using pdfplumber

import pdfplumber


def extract_text_from_pdf(pdf_path):
    """
    Read a PDF file and return all text content as a single string.

    Args:
        pdf_path (str): Absolute path to the PDF file.

    Returns:
        str: Extracted text, or an error message if extraction fails.
    """
    try:
        text_pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)

        full_text = "\n\n".join(text_pages).strip()

        if not full_text:
            return "[No readable text found in the PDF.]"

        return full_text

    except Exception as e:
        return f"[Error extracting text: {e}]"
