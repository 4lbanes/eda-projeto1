from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from textwrap import wrap

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas


def find_repo_root(start: Path) -> Path:
    start = start.resolve()
    for parent in [start, *start.parents]:
        if (parent / "data").exists() and (parent / "docs").exists():
            return parent
    return start


def draw_wrapped(
    canvas: Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_name: str = "Helvetica",
    font_size: int = 10,
    leading: int = 13,
) -> float:
    canvas.setFont(font_name, font_size)

    # Wrapping simples por caracteres, com ajuste fino pela largura medida.
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for w in words:
        candidate = " ".join([*current, w])
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))

    if not lines:
        lines = wrap(text, width=110) or [text]

    for line in lines:
        canvas.drawString(x, y, line)
        y -= leading
    return y


def main() -> None:
    root = find_repo_root(Path.cwd())
    links_path = root / "docs" / "entregaveis_links.json"
    out_path = root / "docs" / "Entregaveis_Projeto1_ReclameAqui.pdf"

    data = json.loads(links_path.read_text(encoding="utf-8"))
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    canvas = Canvas(str(out_path), pagesize=A4)
    width, height = A4

    margin_x = 2.0 * cm
    y = height - 2.0 * cm

    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(margin_x, y, "Projeto 1 — Entregáveis (ReclameAqui)")
    y -= 18

    canvas.setFont("Helvetica", 11)
    canvas.drawString(margin_x, y, f"Gerado em: {now}")
    y -= 18

    equipe = data.get("equipe", "")
    empresa = data.get("empresa", "")
    if equipe:
        canvas.drawString(margin_x, y, f"Equipe: {equipe}")
        y -= 16
    if empresa:
        canvas.drawString(margin_x, y, f"Empresa: {empresa}")
        y -= 16

    y -= 8
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(margin_x, y, "Links obrigatórios")
    y -= 18

    items = [
        ("A) Código fonte (limpeza + EDA)", data.get("repositorio_notebooks", "")),
        ("A) Código fonte (dashboard)", data.get("repositorio_dashboard", "")),
        ("B) Dashboard publicado (deploy)", data.get("dashboard_publicado", "")),
        ("C) Vídeo explicativo (até 10 min)", data.get("video", "")),
    ]

    max_width = width - (2 * margin_x)
    for title, url in items:
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(margin_x, y, title)
        y -= 14
        canvas.setFont("Helvetica", 10)
        y = draw_wrapped(canvas, url or "TODO", margin_x, y, max_width=max_width, font_size=10, leading=13)
        y -= 10

        if y < 3.0 * cm:
            canvas.showPage()
            y = height - 2.0 * cm

    obs = data.get("observacoes", "")
    if obs:
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(margin_x, y, "Observações")
        y -= 14
        y = draw_wrapped(canvas, str(obs), margin_x, y, max_width=max_width, font_size=10, leading=13)

    canvas.save()
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()

