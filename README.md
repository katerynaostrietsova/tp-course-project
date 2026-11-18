# sipl-formal-toolkit

Проєктна робота з теорії програмування, трек "Формальні мови".

Завдання: FORM-01 (2.0), FORM-02 (2.5), FORM-03 (2.0), FORM-04 (1.5), VIS-01 (1.5), REL-02 (0.5). Разом 10 балів.

## Встановлення

    python -m venv .venv
    .venv\Scripts\activate
    pip install -e .[test]

Тести: `pytest`. Швидко подивитись усе разом: `python examples/demo.py`.

## Перетворення граматик (FORM-01)

Формат файлу з граматикою описано в `docs/grammar-format.md`.

    sipl cfg reduce examples/grammars/ex4_19.txt --explain    # зведена граматика
    sipl cfg noeps  examples/grammars/ex4_20.txt --explain    # без ε-правил
    sipl cfg cnf    examples/grammars/ex4_21.txt --explain    # нормальна форма Хомського
    sipl cfg words  examples/grammars/anbn.txt --max-len 6    # слова мови довжини <= 6

`--format json` - результат і кроки у JSON, `--out файл` - зберегти у файл.

## Виводи і дерева виводу (FORM-04)

    sipl derive examples/grammars/minus.txt a-a-a
    sipl derive examples/grammars/anbn.txt aabb --mode right
    sipl derive examples/grammars/minus.txt a-a-a --format dot --out trees.dot

Параметри: `--mode left|right`, `--max-steps` (глибина пошуку), `--limit` (скільки виводів шукати),
`--format text|json|dot|svg`. Для svg потрібен встановлений Graphviz.

## Дерево виводу SIPL-програми (VIS-01)

    sipl tree examples/sipl/gcd.sipl
    sipl tree examples/sipl/gcd.sipl --format dot --out gcd.dot

Граматика SIPL: `grammar/sipl_bnf.txt` (БНФ з посібника) і `src/sipl/sipl.lark`.

## Обмеження

- виводи шукаються перебором з обмеженням глибини (`--max-steps`), тому для дуже довгих слів
  пошук може нічого не знайти, хоча слово належить мові;
- перевірка еквівалентності граматик робиться лише на словах обмеженої довжини;
- у SIPL немає від'ємних констант, замість -1 треба писати 0 - 1.
