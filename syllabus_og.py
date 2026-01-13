import pdfplumber
import re

def subjects_extract(pdf_path):
    subjects = []

    pdf_path = r"C:\Users\ACER SAI\Documents\great\ttgen\syllabus.pdf.pdf"

    pattern_subject = r'([A-Z]{3}-\d{3}-\s*[A-Z]{3})\s*:?\s*,?\s*(.+)'
    pattern_hours = r'(Theory|Practical|Tutorials?|Lab)\s*:\s*(\d+)\s*Hour[s]?/Week'

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            subject_matches = re.findall(pattern_subject, text)
            hour_matches = re.findall(pattern_hours, text)

            # Convert hours into dictionary
            hours_dict = {
                "theory_hours": 0,
                "practical_hours": 0,
                "tutorial_hours": 0,
                
            }

            for hour_type, value in hour_matches:
                hour_type = hour_type.lower()
                value = int(value)

                if hour_type == "theory":
                    hours_dict["theory_hours"] = value
                elif hour_type == "practical":
                    hours_dict["practical_hours"] = value
                elif hour_type.startswith("tutorial"):
                    hours_dict["tutorial_hours"] = value
                

            for code, name in subject_matches:
                subjects.append({
                    "code": code.strip(),
                    "name": name.replace(",", "").strip(),
                    **hours_dict
                })

    return subjects
# subjects=subjects_extract( r"C:\Users\ACER SAI\Documents\great\ttgen\syllabus.pdf.pdf")
# for subject in subjects:
#     print(subject)