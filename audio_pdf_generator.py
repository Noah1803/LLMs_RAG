from fpdf import FPDF
import os

def generate_pdf(markdown_text: str, output_path: str) -> str:
    """
    Gera um arquivo PDF a partir de texto em Markdown.

    Args:
        markdown_text (str): Texto em Markdown a ser convertido em PDF.
        output_path (str): Caminho para salvar o arquivo PDF.

    Returns:
        str: Caminho do arquivo PDF gerado.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in markdown_text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf_path = os.path.join(output_path, "output_document.pdf")
    pdf.output(pdf_path)
    return pdf_path