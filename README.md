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

## Рівняння в алгебрі мов (FORM-02)

Файл може містити систему рівнянь (`S = {ε} ∪ {a}S{b}`) або граматику, тоді система будується з неї.
Об'єднання: `∪`, `|` або `+`; константи-мови: `{a, ab, ε}`; `∅` - порожня мова.

    sipl eq solve   examples/equations/ex4_30.txt               # наближення R(0) = ∅, R(i+1) = ϕ(R(i))
    sipl eq compare examples/equations/system.txt --max-len 5   # порівняння з мовою граматики
    sipl eq grammar examples/equations/system.txt               # граматика за системою рівнянь
    sipl eq lang examples/grammars/anbn.txt --lang "w.count('a') == w.count('b')" --max-len 6

Для `lang` мова задається умовою на слово `w`; виводяться зайві та пропущені слова.

## Лема про накачку (FORM-03)

Лема 4.11: t = u·t1·x·t2·v, |t1 t2| >= 1, |t1 x t2| <= k, u·t1^i·x·t2^i·v ∈ L.
Мова задається умовою на слово (`--lang`) або граматикою (`--grammar`), слово - шаблоном з k.

    sipl pump --lang "w == 'a'*(len(w)//3) + 'b'*(len(w)//3) + 'c'*(len(w)//3)" --k 3 --word "a^k b^k c^k"
    sipl pump --grammar examples/grammars/anbn.txt --k 3 --word "a^k b^k"
    sipl pump --grammar examples/grammars/anbn.txt --k 3 --word "a^k b^k" --split "aa|a||b|bb"
    sipl pump --lang "..." --k 3 --word "a^k b^k c^k" --html pump.html

Перебираються всі розклади t і для кожного шукається i, при якому слово виходить з мови.
`--split` перевіряє один розклад, `--html` зберігає кольорову таблицю (u, v - сірі, t1, t2 - червоні, x - синій).

## Дерево виводу SIPL-програми (VIS-01)

    sipl tree examples/sipl/gcd.sipl
    sipl tree examples/sipl/gcd.sipl --format dot --out gcd.dot

Граматика SIPL: `grammar/sipl_bnf.txt` (БНФ з посібника) і `src/sipl/sipl.lark`.

## Обмеження

- виводи шукаються перебором з обмеженням глибини (`--max-steps`), тому для дуже довгих слів
  пошук може нічого не знайти, хоча слово належить мові;
- перевірка еквівалентності граматик робиться лише на словах обмеженої довжини;
- наближення рахуються лише для слів довжини <= `--max-len`, тому вони завжди стабілізуються
  за скінченну кількість кроків; це наближення розв'язку, а не вся (можливо нескінченна) мова;
- лема про накачку перевіряється лише для заданих k, t та скінченної кількості i, тому
  інструмент є асистентом, а не доведенням того, що мова не є КВ;
- у SIPL немає від'ємних констант, замість -1 треба писати 0 - 1.
