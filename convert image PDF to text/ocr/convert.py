import re
import pytesseract
from PIL import Image

def ocr_to_text(file_path, output_path):
    img = Image.open(file_path)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(img, lang='spa', config=custom_config)
    
    with open(output_path, 'w') as file:
        file.write(text)

    return output_path

ocr_files = []
for i in range(1, 4):
    file_path = f'diciembre-2023/informes contables Diciembre 2023 Cardales_page-000{i}.jpg'
    output_path = f'diciembre-2023/informes_contables_Diciembre_2023_Cardales_page_000{i}.txt'
    ocr_files.append(ocr_to_text(file_path, output_path))

for i in range(1, 4):
    file = open(f'diciembre-2023/informes_contables_Diciembre_2023_Cardales_page_000{i}.txt', 'r')
    for line in file:
        match = re.search(r'^(.+?)\s+\$?([0-9,]{4,})', line)
        if match:
            thing = match.group(1)
            value = match.group(2)
            value = value.replace('$', '')
            value = value.replace(',', '')
            print(f'{thing},{value}')
        else:
            print(line)


ocr_files
