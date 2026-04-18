from fpdf import FPDF
import os

os.makedirs('papers', exist_ok=True)

pdf = FPDF()
pdf.add_page()
pdf.set_font("helvetica", size=12)

text = """
CBSE Class 10 Science Board Paper 2022

Section A - Multiple Choice Questions

1. Which of the following is an exothermic reaction?
(A) Photosynthesis
(B) Respiration
(C) Melting of ice
(D) Boiling of water

2. A ray of light passes from glass to air. The angle of refraction will be:
(A) Equal to the angle of incidence
(B) Less than the angle of incidence
(C) Greater than the angle of incidence
(D) Zero
"""

pdf.multi_cell(0, 10, text)
pdf.output('papers/sample_paper_2022.pdf')
print("Created dummy PDF at papers/sample_paper_2022.pdf")
