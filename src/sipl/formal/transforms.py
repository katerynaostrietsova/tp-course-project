"""Еквівалентні перетворення КВ-граматик (Нікітченко, §4.9)."""

from .grammar import Grammar, nullable, rule_str, set_str
from .trace import Trace


def _rules_str(rules):
    return ", ".join(rule_str(r) for r in rules) if rules else "-"


# ---------- 4.9.1 Видалення несуттєвих символів ----------

def reachable(g, trace=None):
    r = {g.start}
    i = 0
    if trace is not None:
        trace.add(f"R0 = {set_str(r)}")
    while True:
        new = r | {s for a, rhs in g.rules if a in r for s in rhs if s in g.nonterminals}
        if new == r:
            break
        i += 1
        r = new
        if trace is not None:
            trace.add(f"R{i} = {set_str(r)}")
    if trace is not None:
        trace.add(f"R{i + 1} = R{i}, послідовність стабілізувалась: R = {set_str(r)}")
    return r


def productive(g, trace=None):
    pr = {a for a, rhs in g.rules if all(s in g.terminals for s in rhs)}
    i = 0
    if trace is not None:
        trace.add(f"Pr0 = {set_str(pr)}  (є правило A → t, t ∈ T*)")
    while True:
        new = pr | {a for a, rhs in g.rules
                    if all(s in g.terminals or s in pr for s in rhs)}
        if new == pr:
            break
        i += 1
        pr = new
        if trace is not None:
            trace.add(f"Pr{i} = {set_str(pr)}")
    if trace is not None:
        trace.add(f"Pr{i + 1} = Pr{i}, послідовність стабілізувалась: Pr = {set_str(pr)}")
    return pr


def remove_unreachable(g, trace=None):
    if trace is not None:
        trace.add("Пошук досяжних нетерміналів:")
    r = reachable(g, trace)
    ur = g.nonterminals - r
    rules = [(a, rhs) for a, rhs in g.rules if a in r]
    if trace is not None:
        if ur:
            removed = [x for x in g.rules if x not in rules]
            trace.add(f"UR = N \\ R = {set_str(ur)}",
                      f"видаляємо правила: {_rules_str(removed)}")
        else:
            trace.add("UR = ∅, недосяжних нетерміналів немає")
    return Grammar(g.nonterminals & r, g.terminals, rules, g.start)


def remove_unproductive(g, trace=None):
    if trace is not None:
        trace.add("Пошук продуктивних нетерміналів:")
    pr = productive(g, trace)
    upr = g.nonterminals - pr
    rules = [(a, rhs) for a, rhs in g.rules
             if a in pr and all(s in g.terminals or s in pr for s in rhs)]
    if trace is not None:
        if upr:
            removed = [x for x in g.rules if x not in rules]
            trace.add(f"UPr = N \\ Pr = {set_str(upr)}",
                      f"видаляємо правила: {_rules_str(removed)}")
            if g.start in upr:
                trace.add("аксіома непродуктивна, отже мова L(G) порожня")
        else:
            trace.add("UPr = ∅, непродуктивних нетерміналів немає")
    return Grammar((g.nonterminals & pr) | {g.start}, g.terminals, rules, g.start)


def reduce_grammar(g, trace=None):
    """Зведена граматика: спочатку недосяжні, потім непродуктивні,
    і так поки граматика змінюється (див. приклад 4.19), потім несуттєві термінали."""
    if trace is not None:
        trace.add("== Побудова зведеної граматики (§4.9.1) ==")
    cur = g
    k = 1
    while True:
        if trace is not None:
            trace.add(f"-- прохід {k} --")
        nxt = remove_unproductive(remove_unreachable(cur, trace), trace)
        if nxt.same_as(cur):
            break
        cur = nxt
        k += 1
    used = {s for _, rhs in cur.rules for s in rhs if s in cur.terminals}
    if trace is not None:
        extra = cur.terminals - used
        if extra:
            trace.add(f"несуттєві термінали {set_str(extra)} видаляємо з T")
        trace.add("Зведена граматика:", str(cur) or "(правил немає)")
    return Grammar(cur.nonterminals, used, cur.rules, cur.start)


# ---------- 4.9.2 Видалення ε-правил ----------

def remove_eps(g, trace=None):
    """Лема 4.6. Результат породжує L(G) \\ {ε}."""
    if trace is not None:
        trace.add("== Видалення ε-правил (§4.9.2) ==")
    p = list(g.rules)
    i = 0
    if trace is not None:
        eps = [r for r in p if not r[1]]
        trace.add("P0 = P", f"ε-правила: {_rules_str(eps)}")
    while True:
        pset = set(p)
        eps_lhs = {a for a, rhs in p if not rhs}
        added = []
        for b, rhs in p:
            for j, s in enumerate(rhs):
                if s in eps_lhs:
                    new = (b, rhs[:j] + rhs[j + 1:])
                    if new not in pset and new not in added:
                        added.append(new)
        if not added:
            break
        i += 1
        p += added
        if trace is not None:
            trace.add(f"P{i} = P{i - 1} ∪ {{{_rules_str(added)}}}",
                      "для B → αAβ і A → ε додаємо B → αβ")
    rest = [r for r in p if r[1]]
    if trace is not None:
        trace.add(f"P{i + 1} = P{i}, множина правил стабілізувалась")
        removed = [r for r in p if not r[1]]
        trace.add(f"видаляємо ε-правила: {_rules_str(removed)}",
                  "отримана граматика породжує L(G) \\ {ε}")
    return Grammar(g.nonterminals, g.terminals, rest, g.start)


# ---------- 4.9.3 Нормальна форма Хомського ----------

def _fresh(name, used):
    while name in used:
        name += "'"
    return name


def _short(sym, term_nt):
    # N(a) -> a, щоб імена нових нетерміналів були як у посібнику: N(bSc)
    for a, nt in term_nt.items():
        if nt == sym:
            return a
    return sym


def to_cnf(g, trace=None):
    """Лема 4.7. Кроки в тому ж порядку, що й у доведенні."""
    has_eps = g.start in nullable(g)
    if trace is not None:
        trace.add("==== Побудова нормальної форми Хомського (§4.9.3, лема 4.7) ====")
        trace.add("Крок 1. Будуємо еквівалентну граматику без ε-правил")
    g1 = remove_eps(g, trace)
    used = set(g1.nonterminals) | set(g1.terminals)

    # крок 2: термінали в правилах довжини >= 2 замінюємо на N(a)
    term_nt = {}
    rules = []
    for a, rhs in g1.rules:
        if len(rhs) >= 2:
            new_rhs = []
            for s in rhs:
                if s in g1.terminals:
                    if s not in term_nt:
                        term_nt[s] = _fresh(f"N({s})", used)
                        used.add(term_nt[s])
                    s = term_nt[s]
                new_rhs.append(s)
            rhs = tuple(new_rhs)
        rules.append((a, rhs))
    for a, nt in term_nt.items():
        rules.append((nt, (a,)))
    if trace is not None:
        if term_nt:
            trace.add("Крок 2. Замінюємо термінали a на нові нетермінали N(a)",
                      "додано: " + _rules_str([(nt, (a,)) for a, nt in term_nt.items()])
                      + "\n" + "\n".join(rule_str(r) for r in rules))
        else:
            trace.add("Крок 2. Терміналів у правилах довжини ≥ 2 немає")

    # крок 3: A -> A1 A2 ... An (n > 2)
    rules3 = []
    split_log = []
    for a, rhs in rules:
        if len(rhs) <= 2:
            rules3.append((a, rhs))
            continue
        cur = a
        part = list(rhs)
        new_rules = []
        while len(part) > 2:
            tail = part[1:]
            name = "N(" + "".join(_short(s, term_nt) for s in tail) + ")"
            if name not in used:
                used.add(name)
            new_rules.append((cur, (part[0], name)))
            cur = name
            part = tail
        new_rules.append((cur, tuple(part)))
        rules3 += new_rules
        split_log.append(f"{rule_str((a, rhs))}  замінюємо на  {_rules_str(new_rules)}")
    if trace is not None:
        trace.add("Крок 3. Розбиваємо правила A → A1A2…An (n > 2)",
                  "\n".join(split_log) if split_log else "таких правил немає")

    nts = {a for a, _ in rules3} | {s for _, rhs in rules3 for s in rhs if s not in g1.terminals}

    # крок 4: ланцюгові правила A -> B
    def is_chain(r):
        return len(r[1]) == 1 and r[1][0] in nts

    pset = set(rules3)
    order = list(rules3)
    added = []
    changed = True
    while changed:
        changed = False
        for a, rhs in list(order):
            if not is_chain((a, rhs)):
                continue
            b = rhs[0]
            for b2, alpha in list(order):
                if b2 == b and (a, alpha) not in pset and alpha != (a,):
                    pset.add((a, alpha))
                    order.append((a, alpha))
                    added.append((a, alpha))
                    changed = True
    chains = [r for r in order if is_chain(r)]
    rules4 = [r for r in order if not is_chain(r)]
    if trace is not None:
        if chains:
            trace.add("Крок 4. Ланцюгові правила: для A → B і B → α додаємо A → α",
                      f"додано: {_rules_str(added)}\nвидаляємо: {_rules_str(chains)}")
        else:
            trace.add("Крок 4. Ланцюгових правил немає")

    start = g.start
    # крок 5: якщо ε ∈ L(G) - нова аксіома S'
    if has_eps:
        new_start = _fresh(g.start + "'", used)
        used.add(new_start)
        extra = [(new_start, ())] + [(new_start, rhs) for a, rhs in rules4 if a == g.start]
        rules4 = extra + rules4
        start = new_start
        if trace is not None:
            trace.add(f"Крок 5. ε ∈ L(G): нова аксіома {new_start}",
                      f"додаємо {new_start} → ε, {new_start} → {g.start}; ланцюгове правило "
                      f"{new_start} → {g.start} одразу замінюємо правилами {new_start} → α")
    elif trace is not None:
        trace.add("Крок 5. ε ∉ L(G), нова аксіома не потрібна")

    nts = {start} | {a for a, _ in rules4} | {s for _, rhs in rules4 for s in rhs if s not in g1.terminals}
    res = Grammar(nts, g1.terminals, rules4, start)
    if trace is not None:
        trace.add("Крок 6. Прибираємо несуттєві символи, що могли з'явитись")
    res = reduce_grammar(res, trace)
    if trace is not None:
        trace.add("Граматика в НФХ:", str(res))
    return res


def is_cnf(g):
    for a, rhs in g.rules:
        if len(rhs) == 1 and rhs[0] in g.terminals:
            continue
        if len(rhs) == 2 and all(s in g.nonterminals for s in rhs):
            continue
        if not rhs and a == g.start:
            continue
        return False
    return True


def explain(func, g):
    """Виконати перетворення і повернути (граматика, trace)."""
    tr = Trace()
    res = func(g, tr)
    return res, tr
