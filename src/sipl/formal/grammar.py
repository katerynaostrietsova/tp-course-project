"""КВ-граматика G = (N, T, P, S) і читання її з тексту."""

import re
from dataclasses import dataclass

EPS = "ε"

# нетермінали: велика літера (можна з цифрами або штрихами), <ім'я>, N(...)
# термінали: будь-який інший символ або рядок у лапках 'begin'
_TOKEN = re.compile(r"N\([^()]*\)|<[^<>]+>|[A-Z][0-9'′]*|'[^']+'|\S")


class GrammarError(Exception):
    pass


def is_nonterminal_name(s):
    return s.startswith("<") or s.startswith("N(") or s[0].isupper()


def sym_str(s):
    if len(s) > 1 and not is_nonterminal_name(s):
        return f"'{s}'"
    return s


def rhs_str(rhs):
    if not rhs:
        return EPS
    if all(len(s) == 1 for s in rhs):
        return "".join(rhs)
    return " ".join(sym_str(s) for s in rhs)


def rule_str(rule):
    lhs, rhs = rule
    return f"{lhs} → {rhs_str(rhs)}"


def set_str(items):
    return "{" + ", ".join(sorted(items)) + "}"


@dataclass
class Grammar:
    nonterminals: set
    terminals: set
    rules: list  # список пар (A, (X1, ..., Xk)), порожній кортеж = ε
    start: str

    def __post_init__(self):
        seen = set()
        uniq = []
        for r in self.rules:
            r = (r[0], tuple(r[1]))
            if r not in seen:
                seen.add(r)
                uniq.append(r)
        self.rules = uniq
        self.nonterminals = set(self.nonterminals) | {self.start}
        self.terminals = set(self.terminals)

    def rules_for(self, a):
        return [rhs for lhs, rhs in self.rules if lhs == a]

    def same_as(self, other):
        return (set(self.rules) == set(other.rules)
                and self.nonterminals == other.nonterminals
                and self.terminals == other.terminals
                and self.start == other.start)

    def lhs_order(self):
        order = [self.start]
        for lhs, _ in self.rules:
            if lhs not in order:
                order.append(lhs)
        return order

    def __str__(self):
        lines = []
        for a in self.lhs_order():
            alts = self.rules_for(a)
            if alts:
                lines.append(f"{a} → " + " | ".join(rhs_str(r) for r in alts))
        return "\n".join(lines)

    def describe(self):
        return (f"N = {set_str(self.nonterminals)}\n"
                f"T = {set_str(self.terminals)}\n"
                f"S = {self.start}\n"
                f"P:\n{self}")

    def to_dict(self):
        return {
            "nonterminals": sorted(self.nonterminals),
            "terminals": sorted(self.terminals),
            "start": self.start,
            "rules": [{"lhs": a, "rhs": list(rhs)} for a, rhs in self.rules],
        }


def tokenize(alt):
    alt = alt.strip()
    if alt in ("", EPS, "eps"):
        return ()
    result = []
    for tok in _TOKEN.findall(alt):
        if tok == EPS:
            continue
        if tok.startswith("'") and tok.endswith("'") and len(tok) > 2:
            tok = tok[1:-1]
        result.append(tok)
    return tuple(result)


def parse_grammar(text):
    """Читає граматику з рядків вигляду  S -> aSb | ε  (можна → замість ->).
    Аксіома - ліва частина першого правила."""
    rules = []
    start = None
    for no, line in enumerate(text.splitlines(), 1):
        line = line.split("#")[0].strip()
        if not line:
            continue
        m = re.match(r"^(\S+?)\s*(->|→)\s*(.*)$", line)
        if not m:
            raise GrammarError(f"рядок {no}: очікувалось правило вигляду A -> α")
        lhs = m.group(1)
        if not is_nonterminal_name(lhs):
            raise GrammarError(f"рядок {no}: ліва частина '{lhs}' не є нетерміналом")
        if start is None:
            start = lhs
        for alt in m.group(3).split("|"):
            rules.append((lhs, tokenize(alt)))
    if not rules:
        raise GrammarError("граматика не містить жодного правила")

    nonterms = {a for a, _ in rules}
    nonterms |= {s for _, rhs in rules for s in rhs if is_nonterminal_name(s)}
    terms = {s for _, rhs in rules for s in rhs if s not in nonterms}
    return Grammar(nonterms, terms, rules, start)


def load_grammar(path):
    with open(path, encoding="utf-8") as f:
        return parse_grammar(f.read())


def parse_word(word):
    """'aabb' -> ('a','a','b','b');  'begin x end' -> по пробілах;  ε -> ()"""
    word = word.strip()
    if word in ("", EPS, "eps"):
        return ()
    if " " in word:
        return tuple(word.split())
    return tuple(word)


# --- слова мови довжини <= n ---

def concat(langs, n):
    """Добуток мов з відкиданням слів, довших за n."""
    result = {""}
    for lang in langs:
        result = {u + v for u in result for v in lang if len(u) + len(v) <= n}
        if not result:
            break
    return result


def words_by_nonterminal(g, n):
    """Для кожного нетермінала A - множина слів довжини <= n, що виводяться з A.
    Рахується як найменша нерухома точка системи рівнянь (обрізаної до довжини n)."""
    lang = {a: set() for a in g.nonterminals}
    changed = True
    while changed:
        changed = False
        for a, rhs in g.rules:
            parts = [lang[s] if s in g.nonterminals else {s} for s in rhs]
            new = concat(parts, n) - lang[a]
            if new:
                lang[a] |= new
                changed = True
    return lang


def language_up_to(g, n):
    return words_by_nonterminal(g, n)[g.start]


def nullable(g):
    """Нетермінали A, для яких A ⇒* ε."""
    result = set()
    changed = True
    while changed:
        changed = False
        for a, rhs in g.rules:
            if a not in result and all(s in result for s in rhs):
                result.add(a)
                changed = True
    return result
