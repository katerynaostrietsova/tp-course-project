import argparse
import json
import sys

from .formal.grammar import GrammarError, language_up_to, load_grammar, parse_word
from .formal.trace import Trace
from .formal import transforms
from .formal.derivations import analyze
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
