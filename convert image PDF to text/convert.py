import re
import sys
import fitz                    # PyMuPDF => Extraer imágenes de un PDF
import pytesseract             # OCR
from PIL import Image          # Python Imaging Library

def extract_text_from_image(image_path):
    # Load and convert image to grayscale
    img = Image.open(image_path)
    img = img.convert('L')

    # Use automatic page segmentation with OSD
    custom_config = r'--oem 3 --psm 6'
    #text_data = pytesseract.image_to_string(img, config=custom_config, output_type=pytesseract.Output.DICT)
    text_data = pytesseract.image_to_string(image_path)

    # Prepare to write to file
    text_path = image_path.replace(".png", ".txt")
    last_bottom = 0

    with open(text_path, "w") as file:
        file.write(text_data)

    print(f"Saved OCR file => {text_path}")

def extract_from_pdf(pdf_path, dpi=300):
    doc = fitz.open(pdf_path)
    zoom = dpi / 72                 # Default PDF rendering is 72 DPI
    mat = fitz.Matrix(zoom, zoom)  # Create a transformation matrix for the zoom
    
    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat)
        output_path = f"page_{i + 1}.png"
        pix.save(output_path)
        print(f"Saved {output_path}")

        # Process the image
        extract_text_from_image(output_path)

if __name__ == "__main__":
    extract_from_pdf("info_detallada.pdf", dpi=800)
