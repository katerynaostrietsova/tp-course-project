from dataclasses import dataclass


@dataclass
class Step:
    title: str
    text: str = ""


class Trace(list):
    """Список кроків перетворення з поясненнями."""

    def add(self, title, text=""):
        self.append(Step(title, text))

    def __str__(self):
        out = []
        for st in self:
            out.append(st.title)
            if st.text:
                out.extend("    " + line for line in st.text.splitlines())
        return "\n".join(out)

    def to_list(self):
        return [{"title": s.title, "text": s.text} for s in self]
