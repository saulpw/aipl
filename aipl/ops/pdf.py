from aipl import defop


@defop('pdf-extract', 0, 0)
def op_pdf_extract(aipl, pdfdata:bytes) -> str:
    'Extract contents of pdf to value.'
    from pdfminer.high_level import extract_text
    from io import BytesIO
    s = BytesIO(pdfdata)
    return extract_text(s)
