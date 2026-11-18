"""Лема про накачку для КВ-мов (Нікітченко, лема 4.11).

Якщо L - КВ-мова, то існує k таке, що для кожного t ∈ L, |t| >= k, знайдуться
u, t1, x, t2, v: t = u t1 x t2 v, |t1 t2| >= 1, |t1 x t2| <= k
і u t1^i x t2^i v ∈ L для всіх i = 0, 1, ...

Інструмент лише допомагає дослідити лему для конкретних k, t і скінченної
кількості значень i. Довести, що мова не є КВ, він не може.
"""

import html
import re
from dataclasses import dataclass

from .grammar import EPS, GrammarError
from .equations import cyk
from .transforms import to_cnf

NOTE = ("Увага: перевіряються лише задані k, t та i = 0..max_i. Це асистент для дослідження леми, "
        "а не загальний алгоритм: у загальному випадку перевірити, чи є мова контекстно-вільною, неможливо.")


@dataclass
class Split:
    u: str
    t1: str
    x: str
    t2: str
    v: str

    def pumped(self, i):
        return self.u + self.t1 * i + self.x + self.t2 * i + self.v

    def parts(self):
        return [self.u, self.t1, self.x, self.t2, self.v]

    def __str__(self):
        return " · ".join(p if p else EPS for p in self.parts())


@dataclass
class SplitResult:
    split: Split
    checks: list       # (i, слово, чи належить L)
    failed_i: int      # перше i, для якого слово ∉ L, або None

    @property
    def refuted(self):
        return self.failed_i is not None


def splits(t, k):
    """Усі розклади t = u t1 x t2 v з |t1 t2| >= 1 та |t1 x t2| <= k."""
    n = len(t)
    res = []
    for start in range(n):
        for length in range(1, min(k, n - start) + 1):     # |t1 x t2| = length
            mid = t[start:start + length]
            for a in range(length + 1):                     # |t1| = a
                for b in range(length - a + 1):             # |t2| = b
                    if a + b == 0:
                        continue
                    t1 = mid[:a]
                    x = mid[a:length - b]
                    t2 = mid[length - b:]
                    res.append(Split(t[:start], t1, x, t2, t[start + length:]))
    return res


def check_split(sp, in_lang, max_i=3):
    checks = []
    failed = None
    for i in range(max_i + 1):
        w = sp.pumped(i)
        ok = in_lang(w)
        checks.append((i, w, ok))
        if not ok and failed is None:
            failed = i
    return SplitResult(sp, checks, failed)


def explore(t, k, in_lang, max_i=3):
    if not in_lang(t):
        raise GrammarError(f"слово {t} не належить мові, лему для нього перевіряти не можна")
    if len(t) < k:
        raise GrammarError(f"|t| = {len(t)} < k = {k}, лема вимагає слово довжини не менше k")
    results = [check_split(sp, in_lang, max_i) for sp in splits(t, k)]
    survived = [r for r in results if not r.refuted]
    return {"t": t, "k": k, "max_i": max_i, "results": results,
            "survived": survived, "all_refuted": not survived}


def parse_split(t, text):
    """Розклад, заданий вручну: 'aa|a||b|bcc' (5 частин через |)."""
    parts = text.split("|")
    if len(parts) != 5:
        raise GrammarError("розклад має складатися з 5 частин u|t1|x|t2|v")
    parts = ["" if p in (EPS, "eps") else p for p in parts]
    sp = Split(*parts)
    if "".join(parts) != t:
        raise GrammarError(f"частини розкладу не складаються в слово {t}")
    return sp


def split_conditions(sp, k):
    a = len(sp.t1) + len(sp.t2)
    b = len(sp.t1) + len(sp.x) + len(sp.t2)
    return [(f"|t1 t2| = {a} >= 1", a >= 1), (f"|t1 x t2| = {b} <= {k}", b <= k)]


def expand_word(template, k):
    """'a^k b^k c^k' -> aaabbbccc для k = 3. Показник може бути виразом: a^{k+1}, b^{2k}."""
    def repl(m):
        exp = m.group(2).strip("{}")
        exp = re.sub(r"(\d)k", r"\1*k", exp)
        try:
            count = eval(exp, {"__builtins__": {}}, {"k": k})
        except Exception:
            raise GrammarError(f"незрозумілий показник '{m.group(2)}'") from None
        return m.group(1) * int(count)

    word = re.sub(r"(\w)\^(\{[^}]*\}|\w+)", repl, template)
    return word.replace(" ", "")


def grammar_membership(g):
    cnf = to_cnf(g)
    return lambda w: cyk(cnf, w)


# ---------- вивід ----------

def report_text(res, limit=20):
    lines = [f"t = {res['t']},  |t| = {len(res['t'])},  k = {res['k']}",
             f"розкладів t = u·t1·x·t2·v з |t1 t2| >= 1 і |t1 x t2| <= k: {len(res['results'])}", ""]
    ordered = res["survived"] + [r for r in res["results"] if r.refuted]
    shown = ordered if limit is None else ordered[:limit]
    for r in shown:
        if r.refuted:
            i, w, _ = r.checks[r.failed_i]
            lines.append(f"  {r.split}   ->  i = {i}: {w if w else EPS} ∉ L")
        else:
            lines.append(f"  {r.split}   ->  для i = 0..{res['max_i']} всі слова ∈ L")
    if limit is not None and len(res["results"]) > limit:
        lines.append(f"  ... ще {len(res['results']) - limit} розкладів")
    lines.append("")
    if res["all_refuted"]:
        lines.append("Кожен розклад спростовано: для цього t умова леми не виконується.")
        lines.append("Якщо так буде для будь-якого k (слово треба будувати залежно від k), мова не є КВ.")
    else:
        lines.append(f"Розкладів, для яких лема виконується: {len(res['survived'])}. "
                     "Таке t нічого не доводить, спробуйте інше слово.")
    lines.append("")
    lines.append(NOTE)
    return "\n".join(lines)


def single_text(r, k):
    lines = [f"розклад: u = {r.split.u or EPS}, t1 = {r.split.t1 or EPS}, x = {r.split.x or EPS}, "
             f"t2 = {r.split.t2 or EPS}, v = {r.split.v or EPS}"]
    for cond, ok in split_conditions(r.split, k):
        lines.append(f"  {cond}  {'так' if ok else 'НІ'}")
    for i, w, ok in r.checks:
        lines.append(f"  i = {i}: {w if w else EPS}  {'∈ L' if ok else '∉ L'}")
    lines.append("розклад спростовано" if r.refuted else "для перевірених i лема виконується")
    return "\n".join(lines)


_COLORS = ["#dddddd", "#ffb3b3", "#b3d9ff", "#ffb3b3", "#dddddd"]
_NAMES = ["u", "t1", "x", "t2", "v"]


def report_html(res, title="Лема про накачку"):
    def colored(sp):
        out = []
        for name, part, color in zip(_NAMES, sp.parts(), _COLORS):
            text = html.escape(part) if part else EPS
            out.append(f'<span title="{name}" style="background:{color};padding:1px 3px;'
                       f'margin-right:2px;font-family:monospace">{text}</span>')
        return "".join(out)

    rows = []
    for r in res["results"]:
        cells = "".join(
            f'<td style="color:{"green" if ok else "red"};font-family:monospace">'
            f'{html.escape(w) if w else EPS}</td>' for _, w, ok in r.checks)
        status = "спростовано" if r.refuted else "виконується"
        rows.append(f"<tr><td>{colored(r.split)}</td>{cells}<td>{status}</td></tr>")
    head = "".join(f"<th>i = {i}</th>" for i in range(res["max_i"] + 1))
    verdict = ("Кожен розклад спростовано: для цього t умова леми не виконується."
               if res["all_refuted"] else
               f"Є розклади, для яких лема виконується ({len(res['survived'])}): це слово нічого не доводить.")
    return f"""<!DOCTYPE html>
<html lang="uk"><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:Arial;margin:20px}} td,th{{border:1px solid #ccc;padding:4px 8px}}
table{{border-collapse:collapse}}</style></head><body>
<h2>{title}</h2>
<p>t = <b>{html.escape(res['t'])}</b>, |t| = {len(res['t'])}, k = {res['k']}.
Умови: t = u·t1·x·t2·v, |t1 t2| &ge; 1, |t1 x t2| &le; k, u·t1<sup>i</sup>·x·t2<sup>i</sup>·v &isin; L.</p>
<p>Кольори: <span style="background:#dddddd">u, v</span>
<span style="background:#ffb3b3">t1, t2</span> <span style="background:#b3d9ff">x</span>.
Зелене слово належить L, червоне - ні.</p>
<table><tr><th>розклад</th>{head}<th></th></tr>
{''.join(rows)}
</table>
<p><b>{verdict}</b></p>
<p><i>{html.escape(NOTE)}</i></p>
</body></html>
"""
