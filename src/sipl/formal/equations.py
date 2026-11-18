"""Рівняння в алгебрі формальних мов AL = (2^T*, ∪, ·), Нікітченко §4.15."""

import itertools
import re
from dataclasses import dataclass

from .grammar import EPS, Grammar, GrammarError, is_nonterminal_name
from .transforms import to_cnf


# ---------- вирази LExp ----------

@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Const:
    words: frozenset


@dataclass(frozen=True)
class Union:
    left: object
    right: object


@dataclass(frozen=True)
class Concat:
    left: object
    right: object


def word_str(w):
    return w if w else EPS


def lang_str(words, limit=None):
    items = sorted(words, key=lambda w: (len(w), w))
    if limit is not None and len(items) > limit:
        return "{" + ", ".join(word_str(w) for w in items[:limit]) + f", ... (ще {len(items) - limit})}}"
    return "{" + ", ".join(word_str(w) for w in items) + "}" if items else "∅"


def expr_str(e):
    if isinstance(e, Var):
        return e.name
    if isinstance(e, Const):
        return lang_str(e.words)
    if isinstance(e, Union):
        return f"{expr_str(e.left)} ∪ {expr_str(e.right)}"
    left = expr_str(e.left)
    right = expr_str(e.right)
    if isinstance(e.left, Union):
        left = f"({left})"
    if isinstance(e.right, Union):
        right = f"({right})"
    return left + right


def interpret(e, nu, n=None):
    """µν(e). Якщо задано n, слова довші за n відкидаються."""
    if isinstance(e, Var):
        return set(nu[e.name])
    if isinstance(e, Const):
        return {w for w in e.words if n is None or len(w) <= n}
    if isinstance(e, Union):
        return interpret(e.left, nu, n) | interpret(e.right, nu, n)
    a = interpret(e.left, nu, n)
    b = interpret(e.right, nu, n)
    return {u + v for u in a for v in b if n is None or len(u) + len(v) <= n}


def variables(e):
    if isinstance(e, Var):
        return {e.name}
    if isinstance(e, Const):
        return set()
    return variables(e.left) | variables(e.right)


# ---------- система рівнянь ----------

@dataclass
class System:
    order: list    # змінні в порядку рівнянь, перша - "головна"
    rhs: dict      # змінна -> вираз

    @property
    def start(self):
        return self.order[0]

    def __str__(self):
        return "\n".join(f"{x} = {expr_str(self.rhs[x])}" for x in self.order)


def _union_all(terms):
    res = terms[0]
    for t in terms[1:]:
        res = Union(res, t)
    return res


def _concat_all(items):
    res = items[0]
    for t in items[1:]:
        res = Concat(res, t)
    return res


def from_grammar(g):
    """Кожному нетерміналу A - рівняння A = ∪ праві частини правил A → α."""
    order = g.lhs_order()
    rhs = {}
    for a in order:
        terms = []
        for alpha in g.rules_for(a):
            if not alpha:
                terms.append(Const(frozenset({""})))
            else:
                terms.append(_concat_all([Var(s) if s in g.nonterminals else Const(frozenset({s}))
                                          for s in alpha]))
        rhs[a] = _union_all(terms) if terms else Const(frozenset())
    return System(order, rhs)


def _products(e):
    """Розкриття дужок: вираз -> список добутків (кожен - список Var/Const)."""
    if isinstance(e, (Var, Const)):
        return [[e]]
    if isinstance(e, Union):
        return _products(e.left) + _products(e.right)
    return [p + q for p in _products(e.left) for q in _products(e.right)]


def to_grammar(system):
    """Обернена побудова: система рівнянь -> КВ-граматика."""
    rules = []
    terms = set()
    for x in system.order:
        for prod in _products(system.rhs[x]):
            choices = []
            for item in prod:
                if isinstance(item, Var):
                    choices.append([(item.name,)])
                else:
                    choices.append([tuple(w) for w in sorted(item.words)])
            for combo in itertools.product(*choices):
                rhs = tuple(s for part in combo for s in part)
                rules.append((x, rhs))
                terms |= {s for s in rhs if s not in system.rhs}
    return Grammar(set(system.order), terms, rules, system.start)


# ---------- читання системи з тексту ----------

_TOK = re.compile(r"\s*(\{[^}]*\}|∪|\||\+|\(|\)|<[^<>]+>|[A-Z][0-9'′]*|∅)")


def _parse_const(tok):
    inner = tok[1:-1].strip()
    if not inner:
        return Const(frozenset())
    words = set()
    for w in inner.split(","):
        w = w.strip()
        words.add("" if w in (EPS, "eps") else w)
    return Const(frozenset(words))


def parse_expr(text):
    pos = 0
    toks = []
    text = text.strip()
    while pos < len(text):
        m = _TOK.match(text, pos)
        if not m:
            raise GrammarError(f"незрозумілий символ у виразі: '{text[pos:].strip()[:10]}'")
        toks.append(m.group(1))
        pos = m.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
    i = 0

    def union():
        nonlocal i
        res = concat()
        while i < len(toks) and toks[i] in ("∪", "|", "+"):
            i += 1
            res = Union(res, concat())
        return res

    def concat():
        nonlocal i
        items = []
        while i < len(toks) and toks[i] not in ("∪", "|", "+", ")"):
            items.append(atom())
        if not items:
            raise GrammarError("порожній доданок у виразі")
        return _concat_all(items)

    def atom():
        nonlocal i
        t = toks[i]
        i += 1
        if t == "(":
            e = union()
            if i >= len(toks) or toks[i] != ")":
                raise GrammarError("не закрита дужка")
            i += 1
            return e
        if t == "∅":
            return Const(frozenset())
        if t.startswith("{"):
            return _parse_const(t)
        if is_nonterminal_name(t):
            return Var(t)
        raise GrammarError(f"неочікуване '{t}'")

    e = union()
    if i != len(toks):
        raise GrammarError(f"неочікуване '{toks[i]}'")
    return e


def parse_system(text):
    """Рядки вигляду  S = {ε} ∪ {a}S{b}"""
    order = []
    rhs = {}
    for no, line in enumerate(text.splitlines(), 1):
        line = line.split("#")[0].strip()
        if not line:
            continue
        if "=" not in line:
            raise GrammarError(f"рядок {no}: очікувалось рівняння X = вираз")
        left, right = line.split("=", 1)
        x = left.strip()
        if not is_nonterminal_name(x):
            raise GrammarError(f"рядок {no}: '{x}' не може бути змінною")
        try:
            rhs[x] = parse_expr(right)
        except GrammarError as e:
            raise GrammarError(f"рядок {no}: {e}") from None
        if x not in order:
            order.append(x)
    if not order:
        raise GrammarError("система не містить рівнянь")
    for x in order:
        for v in variables(rhs[x]):
            if v not in rhs:
                raise GrammarError(f"для змінної {v} немає рівняння")
    return System(order, rhs)


def load_system(path):
    """Файл з рівняннями або з граматикою (якщо є '->')."""
    from .grammar import parse_grammar
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if "->" in text or "→" in text:
        return from_grammar(parse_grammar(text))
    return parse_system(text)


# ---------- метод послідовних наближень ----------

def phi(system, nu, n):
    return {x: interpret(system.rhs[x], nu, n) for x in system.order}


def approximations(system, n, max_iter=30):
    """R(0) = ∅, R(i+1) = ϕ(R(i)); слова обрізаються до довжини n.
    Зупиняємось, коли наближення перестали змінюватись."""
    cur = {x: set() for x in system.order}
    res = [cur]
    for _ in range(max_iter):
        nxt = phi(system, cur, n)
        if nxt == cur:
            break
        res.append(nxt)
        cur = nxt
    return res


def is_solution(system, nu, n):
    """Чи перетворює ν усі рівняння на рівності (для слів довжини <= n)."""
    cut = {x: {w for w in nu[x] if len(w) <= n} for x in system.order}
    return phi(system, cut, n) == cut


def approx_table(system, approx, limit=8):
    lines = []
    for i, r in enumerate(approx):
        parts = [f"{x}: {lang_str(r[x], limit)}" for x in system.order]
        lines.append(f"R({i}) = " + ";  ".join(parts) if len(system.order) > 1
                     else f"R({i}) = {lang_str(r[system.start], limit)}")
    return "\n".join(lines)


# ---------- порівняння з граматикою ----------

def cyk(g, word):
    """Чи належить слово мові граматики g у НФХ (алгоритм Кока-Янгера-Касамі)."""
    if not word:
        return (g.start, ()) in g.rules
    n = len(word)
    table = [[set() for _ in range(n + 1)] for _ in range(n)]
    for i, ch in enumerate(word):
        table[i][1] = {a for a, rhs in g.rules if rhs == (ch,)}
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            for k in range(1, length):
                left = table[i][k]
                right = table[i + k][length - k]
                if not left or not right:
                    continue
                for a, rhs in g.rules:
                    if len(rhs) == 2 and rhs[0] in left and rhs[1] in right:
                        table[i][length].add(a)
    return g.start in table[0][n]


def all_words(alphabet, n):
    alphabet = sorted(alphabet)
    res = [""]
    for k in range(1, n + 1):
        res += ["".join(p) for p in itertools.product(alphabet, repeat=k)]
    return res


def grammar_words(g, n):
    """Слова довжини <= n, що породжує граматика (перевірка кожного слова алгоритмом CYK)."""
    cnf = to_cnf(g)
    return {w for w in all_words(g.terminals, n) if cyk(cnf, w)}


def compare_with_grammar(system, n):
    g = to_grammar(system)
    approx = approximations(system, n)
    r = approx[-1][system.start]
    gw = grammar_words(g, n)
    return {"approx": r, "grammar": gw, "equal": r == gw,
            "only_approx": r - gw, "only_grammar": gw - r}


def compare_with_language(g, predicate, n, alphabet=None):
    """Конструктор: чи породжує граматика саме ту мову, що задана умовою predicate(w)."""
    alphabet = alphabet or g.terminals
    expected = {w for w in all_words(alphabet, n) if predicate(w)}
    generated = approximations(from_grammar(g), n)[-1][g.start]
    return {"extra": generated - expected, "missing": expected - generated,
            "ok": generated == expected}


def make_predicate(text):
    """Умова на слово, напр. "w.count('a') == w.count('b')" або "lambda w: ..."."""
    text = text.strip()
    if not text.startswith("lambda"):
        text = "lambda w: " + text
    allowed = {"len": len, "all": all, "any": any, "set": set, "sorted": sorted,
               "range": range, "int": int, "str": str}
    try:
        return eval(text, {"__builtins__": allowed})
    except SyntaxError as e:
        raise GrammarError(f"помилка в умові: {e.msg}") from None
