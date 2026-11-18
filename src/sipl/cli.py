import argparse
import json
import sys

from .formal.grammar import GrammarError, language_up_to, load_grammar, parse_word
from .formal.trace import Trace
from .formal import transforms
from .formal.derivations import analyze
from .formal import equations as eq
from .formal import pumping
from .sipl_tree import SiplSyntaxError, load_tree
from .visualization import tree as tv


def _write(text, out):
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"збережено у {out}")
    else:
        print(text)


def _export_tree(node, fmt):
    if fmt == "text":
        return tv.to_text(node)
    if fmt == "json":
        return tv.to_json(node)
    dot = tv.to_dot(node)
    return dot if fmt == "dot" else tv.dot_to_svg(dot)


def cmd_cfg(args):
    g = load_grammar(args.file)
    if args.action == "words":
        words = sorted(language_up_to(g, args.max_len), key=lambda w: (len(w), w))
        print(", ".join(w if w else "ε" for w in words))
        return 0
    func = {"reduce": transforms.reduce_grammar,
            "noeps": transforms.remove_eps,
            "cnf": transforms.to_cnf}[args.action]
    tr = Trace()
    res = func(g, tr)
    if args.format == "json":
        data = {"result": res.to_dict(), "steps": tr.to_list()}
        _write(json.dumps(data, ensure_ascii=False, indent=2), args.out)
        return 0
    text = ""
    if args.explain:
        text += str(tr) + "\n\n"
    text += "Результат:\n" + res.describe()
    _write(text, args.out)
    return 0


def cmd_derive(args):
    g = load_grammar(args.file)
    r = analyze(g, parse_word(args.word), args.mode, args.max_steps, args.limit)
    if args.format == "json":
        data = {"word": r["word"], "mode": r["mode"], "ambiguous": r["ambiguous"],
                "derivations": [d.to_dict() for d in r["derivations"]],
                "trees": [tv.to_dict(t) for t in r["trees"]]}
        _write(json.dumps(data, ensure_ascii=False, indent=2), args.out)
        return 0 if r["found"] else 2
    if args.format in ("dot", "svg"):
        if not r["found"]:
            print("виводів не знайдено", file=sys.stderr)
            return 2
        dot = tv.to_dot_many(r["trees"])
        _write(dot if args.format == "dot" else tv.dot_to_svg(dot), args.out)
        return 0

    kind = "лівосторонніх" if args.mode == "left" else "правосторонніх"
    if not r["found"]:
        print(f"Слово {r['word']} не виводиться (у межах {args.max_steps} кроків)")
        return 2
    lines = [f"Знайдено {kind} виводів: {len(r['derivations'])}"]
    for i, d in enumerate(r["derivations"], 1):
        lines.append(f"\nВивід {i}:\n{d.detailed()}")
    lines.append("")
    for i, t in enumerate(r["trees"], 1):
        lines.append(f"Дерево {i}:\n{tv.to_text(t)}\n")
    if r["ambiguous"]:
        lines.append(f"Слово має {len(r['trees'])} різних дерева виводу, граматика неоднозначна.")
    else:
        lines.append("Знайдено одне дерево виводу.")
    _write("\n".join(lines), args.out)
    return 0


def cmd_eq(args):
    system = eq.load_system(args.file)
    if args.action == "grammar":
        _write(str(eq.to_grammar(system)), args.out)
        return 0
    if args.action == "lang":
        g = eq.to_grammar(system)
        pred = eq.make_predicate(args.lang)
        alphabet = set(args.alphabet) if args.alphabet else None
        r = eq.compare_with_language(g, pred, args.max_len, alphabet)
        lines = [f"Граматика:\n{g}", ""]
        if r["ok"]:
            lines.append(f"На словах довжини <= {args.max_len} граматика породжує саме задану мову")
        else:
            lines.append(f"Зайві слова (є в граматиці, але не задовольняють умову): {eq.lang_str(r['extra'])}")
            lines.append(f"Пропущені слова (задовольняють умову, але не породжуються): {eq.lang_str(r['missing'])}")
        _write("\n".join(lines), args.out)
        return 0 if r["ok"] else 2

    approx = eq.approximations(system, args.max_len, args.iterations)
    last = approx[-1]
    if args.format == "json":
        data = {"system": str(system).splitlines(),
                "approximations": [{x: sorted(r[x], key=lambda w: (len(w), w)) for x in system.order}
                                   for r in approx]}
        _write(json.dumps(data, ensure_ascii=False, indent=2), args.out)
        return 0
    lines = ["Система рівнянь:", str(system), "",
             f"Послідовні наближення (слова довжини <= {args.max_len}):",
             eq.approx_table(system, approx, args.show)]
    if len(approx) <= args.iterations:
        lines.append(f"R({len(approx)}) = R({len(approx) - 1}), наближення стабілізувались")
    lines.append(f"Перевірка R = ϕ(R): {'так' if eq.is_solution(system, last, args.max_len) else 'ні'}")
    if args.action == "compare":
        c = eq.compare_with_grammar(system, args.max_len)
        lines.append("")
        lines.append(f"Слова граматики (перевірка CYK): {eq.lang_str(c['grammar'], args.show)}")
        if c["equal"]:
            lines.append(f"Розв'язок збігається з мовою граматики на словах довжини <= {args.max_len}")
        else:
            lines.append(f"Не збігаються! лише в наближенні: {eq.lang_str(c['only_approx'])}, "
                         f"лише в граматиці: {eq.lang_str(c['only_grammar'])}")
    _write("\n".join(lines), args.out)
    return 0


def cmd_pump(args):
    if bool(args.lang) == bool(args.grammar):
        print("помилка: задайте мову через --lang або --grammar", file=sys.stderr)
        return 1
    if args.grammar:
        in_lang = pumping.grammar_membership(load_grammar(args.grammar))
    else:
        in_lang = eq.make_predicate(args.lang)
    t = pumping.expand_word(args.word, args.k)

    if args.split:
        sp = pumping.parse_split(t, args.split)
        r = pumping.check_split(sp, in_lang, args.max_i)
        _write(pumping.single_text(r, args.k), args.out)
        return 0

    res = pumping.explore(t, args.k, in_lang, args.max_i)
    if args.html:
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(pumping.report_html(res))
        print(f"таблицю збережено у {args.html}")
    _write(pumping.report_text(res, None if args.all else 20), args.out)
    return 0


def cmd_tree(args):
    node = load_tree(args.file)
    _write(_export_tree(node, args.format), args.out)
    return 0


def build_arg_parser():
    p = argparse.ArgumentParser(prog="sipl", description="Інструменти для КВ-граматик і мови SIPL")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("cfg", help="перетворення КВ-граматики (FORM-01)")
    c.add_argument("action", choices=["reduce", "noeps", "cnf", "words"])
    c.add_argument("file", help="файл з граматикою")
    c.add_argument("--explain", action="store_true", help="показати всі кроки")
    c.add_argument("--format", choices=["text", "json"], default="text")
    c.add_argument("--max-len", type=int, default=6, help="для words: макс. довжина слова")
    c.add_argument("--out", help="зберегти у файл")
    c.set_defaults(func=cmd_cfg)

    d = sub.add_parser("derive", help="виводи та дерева виводу слова (FORM-04)")
    d.add_argument("file", help="файл з граматикою")
    d.add_argument("word", help="слово, напр. aabb; ε - порожнє слово")
    d.add_argument("--mode", choices=["left", "right"], default="left")
    d.add_argument("--max-steps", type=int, default=20)
    d.add_argument("--limit", type=int, default=10, help="скільки виводів шукати максимум")
    d.add_argument("--format", choices=["text", "json", "dot", "svg"], default="text")
    d.add_argument("--out")
    d.set_defaults(func=cmd_derive)

    e = sub.add_parser("eq", help="рівняння в алгебрі мов (FORM-02)")
    e.add_argument("action", choices=["solve", "compare", "grammar", "lang"])
    e.add_argument("file", help="файл з рівняннями або з граматикою")
    e.add_argument("--max-len", type=int, default=6, help="макс. довжина слів")
    e.add_argument("--iterations", type=int, default=30, help="макс. кількість наближень")
    e.add_argument("--show", type=int, default=10, help="скільки слів показувати")
    e.add_argument("--lang", help="для lang: умова на слово w, напр. \"w.count('a') == w.count('b')\"")
    e.add_argument("--alphabet", help="для lang: алфавіт, напр. ab")
    e.add_argument("--format", choices=["text", "json"], default="text")
    e.add_argument("--out")
    e.set_defaults(func=cmd_eq)

    pm = sub.add_parser("pump", help="лема про накачку (FORM-03)")
    pm.add_argument("--lang", help="умова на слово w, напр. \"w.count('a') == w.count('b')\"")
    pm.add_argument("--grammar", help="або файл з граматикою мови")
    pm.add_argument("--k", type=int, required=True, help="стала k з леми")
    pm.add_argument("--word", required=True, help="слово t, можна шаблоном: a^k b^k c^k")
    pm.add_argument("--max-i", type=int, default=3, help="перевіряти i = 0..max_i")
    pm.add_argument("--split", help="перевірити один розклад u|t1|x|t2|v, напр. aa|a||b|bcc")
    pm.add_argument("--all", action="store_true", help="показати всі розклади")
    pm.add_argument("--html", help="зберегти кольорову таблицю у html-файл")
    pm.add_argument("--out")
    pm.set_defaults(func=cmd_pump)

    t = sub.add_parser("tree", help="дерево виводу SIPL-програми (VIS-01)")
    t.add_argument("file", help="файл .sipl")
    t.add_argument("--format", choices=["text", "json", "dot", "svg"], default="text")
    t.add_argument("--out")
    t.set_defaults(func=cmd_tree)
    return p


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    args = build_arg_parser().parse_args(argv)
    try:
        return args.func(args)
    except (GrammarError, SiplSyntaxError, RuntimeError, OSError) as e:
        print(f"помилка: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
