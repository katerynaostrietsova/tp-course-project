"""Лівосторонні / правосторонні виводи слова і дерева виводу (FORM-04)."""

from dataclasses import dataclass

from .grammar import EPS, nullable, rhs_str, rule_str
from ..visualization.tree import TreeNode


@dataclass
class Derivation:
    start: str
    steps: list  # (форма до кроку, позиція нетермінала, правило)
    final: tuple

    def forms(self):
        return [st[0] for st in self.steps] + [self.final]

    def short(self):
        return " ⇒ ".join(rhs_str(f) for f in self.forms())

    def detailed(self):
        lines = [rhs_str(self.steps[0][0]) if self.steps else rhs_str(self.final)]
        for i, (form, pos, rule) in enumerate(self.steps):
            nxt = self.steps[i + 1][0] if i + 1 < len(self.steps) else self.final
            lines.append(f"⇒ {rhs_str(nxt)}    ({rule_str(rule)})")
        return "\n".join(lines)

    def tree(self):
        root = TreeNode(self.start)
        frontier = [root]
        for form, pos, (a, rhs) in self.steps:
            node = frontier[pos]
            node.rule = rule_str((a, rhs))
            if rhs:
                node.children = [TreeNode(s) for s in rhs]
                frontier = frontier[:pos] + node.children + frontier[pos + 1:]
            else:
                node.children = [TreeNode(EPS)]
                frontier = frontier[:pos] + frontier[pos + 1:]
        return root

    def to_dict(self):
        return {
            "steps": [{"form": rhs_str(f), "position": p, "rule": rule_str(r)}
                      for f, p, r in self.steps],
            "result": rhs_str(self.final),
        }


def find_derivations(g, word, mode="left", max_steps=20, limit=10):
    """Шукає до limit різних виводів слова word (кортеж терміналів)
    довжиною не більше max_steps кроків. mode = 'left' або 'right'."""
    if mode not in ("left", "right"):
        raise ValueError("mode має бути 'left' або 'right'")
    word = tuple(word)
    n = len(word)
    nul = nullable(g)
    nts = g.nonterminals
    results = []

    def possible(form):
        # кожен символ, з якого не виводиться ε, дає хоча б один термінал
        if sum(1 for s in form if s not in nul) > n:
            return False
        if mode == "left":
            k = 0
            while k < len(form) and form[k] not in nts:
                k += 1
            if form[:k] != word[:k]:
                return False
            if k == len(form):
                return form == word
        else:
            k = len(form)
            while k > 0 and form[k - 1] not in nts:
                k -= 1
            tail = form[k:]
            if tail and word[len(word) - len(tail):] != tail:
                return False
            if len(tail) > n:
                return False
            if k == 0:
                return form == word
        return True

    def pick(form):
        idx = [i for i, s in enumerate(form) if s in nts]
        if not idx:
            return None
        return idx[0] if mode == "left" else idx[-1]

    def dfs(form, steps):
        if len(results) >= limit:
            return
        pos = pick(form)
        if pos is None:
            if form == word:
                results.append(Derivation(g.start, steps, form))
            return
        if len(steps) >= max_steps:
            return
        a = form[pos]
        for rhs in g.rules_for(a):
            new = form[:pos] + rhs + form[pos + 1:]
            if possible(new):
                dfs(new, steps + [(form, pos, (a, rhs))])

    dfs((g.start,), [])
    return results


def distinct_trees(derivations):
    seen = {}
    for d in derivations:
        t = d.tree()
        seen.setdefault(t.bracket(), t)
    return list(seen.values())


def analyze(g, word, mode="left", max_steps=20, limit=10):
    ders = find_derivations(g, word, mode, max_steps, limit)
    trees = distinct_trees(ders)
    return {
        "word": rhs_str(tuple(word)),
        "mode": mode,
        "derivations": ders,
        "trees": trees,
        "ambiguous": len(trees) > 1,
        "found": bool(ders),
    }
