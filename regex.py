

import re

#Римские цифры
numbers = {
    "M": 1000,
    "CM": 900,
    "D": 500,
    "CD": 400,
    "C": 100,
    "XC": 90,
    "L": 50,
    "XL": 40,
    "X": 10,
    "IX": 9,
    "V": 5,
    "IV": 4,
    "I": 1,
}

#Функция парсинга римских цифр
def parse_numbers(match) -> str:
    group = match.group()
    res = 0
    for roman, arabic in numbers.items():
        res += len(re.findall(roman, group)) * arabic
        group = re.sub(roman, "", group)
    return str(res)

string = 'Например, в первой главе — фрагменты от I до LX, а во второй — от I до XL. ' \
         'Прочитаем, например, такое число MMIII: MMIII — это 1000 + 1000 + 3 = 2003.'
print(string)
roman_pattern = re.compile(r'\b(?=[IVXLMCD])M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})\b')
print(roman_pattern.sub(parse_numbers, string))

