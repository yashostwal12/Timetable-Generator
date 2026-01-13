import pdfplumber
import re

pdf_path = "syllabus.pdf"
all_text = ""


with pdfplumber.open(r"C:\\Users\\ACER SAI\\Documents\\great\\ttgen\\syllabus.pdf.pdf") as pdf:
    pages = pdf.pages
    for page in pages:
        text = page.extract_text()

        pattern_all = r'([A-Z]{3}-\d{3}-\s*[A-Z]{3})\s*:?\s*,?\s*(.+)'


        pattern_hours = r'(Theory|Practical|Tutorials?|Lab)\s*:\s*(\d+)\s*Hour[s]?/Week'


        code_matches = re.findall(pattern_all, text)
        theory_matches = re.findall(pattern_hours, text)
        

       
        for code, name in code_matches:
            name = name.replace(",", "").strip()
            
            print("Code:", code, "Name:", name)

        
        for theory in theory_matches:
            print("Theory Hours:", theory)

from PyPDF2 import PdfReader

def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text()

    return text


pdf_text = read_pdf("syllabus.pdf.pdf")
print(pdf_text)



 