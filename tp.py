from PyPDF2 import PdfReader

def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text()

    return text


pdf_text = read_pdf("syllabus.pdf")
print(pdf_text)



 