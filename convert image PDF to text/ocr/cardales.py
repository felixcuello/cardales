import re
from pdfminer.high_level import extract_text

for i in range(1, 3):
    file_path = f'cardales/enero_2024_{i}.pdf'
    output_path = f'cardales/enero_2024_{i}.txt'

    text = extract_text(file_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

column = 3
for i in range(1, 3):
    file = open(f'cardales/enero_2024_{i}.txt', 'r')
    lines = file.readlines()

    rubro = []
    empresa = []
    fact = []
    total = []
    col = 3
    for line in lines:
        if re.match(r'^(rubro|empresa|fact|total)', line, re.I):
            col += 1

        if col % 4 == 0:
            rubro.append(line.strip())
        elif col % 4 == 1:
            empresa.append(line.strip())
        elif col % 4 == 2:
            fact.append(line.strip())
        elif col % 4 == 3:
            total.append(line.strip())


    min_len = min(len(rubro), len(empresa), len(fact), len(total))

    for row in range(min_len):
        print(rubro[row], empresa[row], fact[row], total[row])
