"""Дерево виводу і його експорт у text / JSON / DOT / SVG."""

import json
import shutil
import subprocess
from dataclasses import dataclass, field


@dataclass
class TreeNode:
    label: str
    children: list = field(default_factory=list)
    rule: str = None   # назва або текст застосованого правила
    span: dict = None  # line, column, end_line, end_column, text

    def is_leaf(self):
        return not self.children

    def leaves(self):
        if self.is_leaf():
            return [self.label]
        res = []
        for c in self.children:
            res += c.leaves()
        return res

    def bracket(self):
        """Запис дерева в один рядок, напр. S(a S(ε) b). Зручно для порівняння дерев."""
        if self.is_leaf():
            return self.label
        return self.label + "(" + " ".join(c.bracket() for c in self.children) + ")"


def _span_str(span):
    if not span:
        return ""
    return f"  @{span['line']}:{span['column']}-{span['end_line']}:{span['end_column']}"


def to_text(node, show_spans=True):
    lines = []

    def walk(n, prefix, last, root):
        rule = f"  [{n.rule}]" if n.rule else ""
        sp = _span_str(n.span) if show_spans else ""
        if root:
            lines.append(f"{n.label}{rule}{sp}")
            child_prefix = ""
        else:
            lines.append(f"{prefix}{'└── ' if last else '├── '}{n.label}{rule}{sp}")
            child_prefix = prefix + ("    " if last else "│   ")
        for i, c in enumerate(n.children):
            walk(c, child_prefix, i == len(n.children) - 1, False)

    walk(node, "", True, True)
    return "\n".join(lines)


def to_dict(node):
    d = {"label": node.label}
    if node.rule:
        d["rule"] = node.rule
    if node.span:
        d["span"] = node.span
    if node.children:
        d["children"] = [to_dict(c) for c in node.children]
    return d


def to_json(node):
    return json.dumps(to_dict(node), ensure_ascii=False, indent=2)


def _esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _dot_body(node, prefix, lines):
    counter = [0]

    def walk(n):
        my = f"{prefix}{counter[0]}"
        counter[0] += 1
        attrs = f'label="{_esc(n.label)}' + (f'\\n[{_esc(n.rule)}]' if n.rule else "") + '"'
        if n.is_leaf():
            attrs += ", shape=plaintext, fontcolor=blue"
        if n.span and n.span.get("text"):
            attrs += f', tooltip="{_esc(n.span["text"])}"'
        lines.append(f"  {my} [{attrs}];")
        for c in n.children:
            cid = walk(c)
            lines.append(f"  {my} -> {cid};")
        return my

    walk(node)


def to_dot(node, name="tree"):
    lines = [f"digraph {name} {{", '  node [fontname="Arial"];']
    _dot_body(node, "n", lines)
    lines.append("}")
    return "\n".join(lines)


def to_dot_many(nodes, titles=None, name="trees"):
    """Кілька дерев в одному DOT-файлі (кожне у своєму кластері)."""
    lines = [f"digraph {name} {{", '  node [fontname="Arial"];']
    for i, n in enumerate(nodes):
        title = titles[i] if titles else f"дерево {i + 1}"
        lines.append(f"  subgraph cluster_{i} {{")
        lines.append(f'  label="{_esc(title)}";')
        _dot_body(n, f"t{i}_", lines)
        lines.append("  }")
    lines.append("}")
    return "\n".join(lines)


def dot_to_svg(dot_text):
    exe = shutil.which("dot")
    if exe is None:
        raise RuntimeError("не знайдено Graphviz (програма dot), збережіть результат у форматі dot")
    res = subprocess.run([exe, "-Tsvg"], input=dot_text.encode("utf-8"),
                         capture_output=True, check=True)
    return res.stdout.decode("utf-8")
