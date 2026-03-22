from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def draw_architecture(output_path: Path, variant: str = "standard") -> None:
    fig, ax = plt.subplots(figsize=(14, 9), dpi=180)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    if variant == "report":
        background = "#ffffff"
        edge_color = "#172b4d"
        arrow_color = "#1f4b99"
        feedback_color = "#1e7d4d"
        title_color = "#102a43"
        box_colors = {
            "io": "#e8f0ff",
            "process": "#ffffff",
            "core": "#fff1cc",
            "feedback": "#e8f6ee",
            "output": "#fde7e7",
        }
        title = "CV Creation Using Dual-LLM System - Report/Slide Architecture"
    else:
        background = "#f7f9fc"
        edge_color = "#1f2a44"
        arrow_color = "#2b4c7e"
        feedback_color = "#1f7a3a"
        title_color = "#102a43"
        box_colors = {
            "io": "#d9e8ff",
            "process": "#ffffff",
            "core": "#fff4d9",
            "feedback": "#e6f8ea",
            "output": "#ffe3e3",
        }
        title = "CV Creation Using Dual-LLM System - Architecture Diagram"

    fig.patch.set_facecolor(background)
    ax.set_facecolor(background)

    nodes = {
        "resume": (8, 84, 24, 10, "Resume\n(PDF/DOCX/TXT)"),
        "job": (68, 84, 24, 10, "Job Description\n(TXT)"),
        "extractor": (10, 67, 20, 8, "extractor.py"),
        "parser": (70, 67, 20, 8, "parser.py"),
        "main": (38, 55, 24, 10, "main.py\n(workflow)"),
        "matcher": (40, 42, 20, 8, "matcher.py"),
        "generator": (38, 30, 24, 10, "generator.py"),
        "ats": (18, 16, 22, 9, "ats_checker.py"),
        "reviser": (60, 16, 22, 9, "reviser.py\n(iterative loop)"),
        "formatters": (38, 4, 24, 8, "formatters.py"),
        "output": (30, -8, 40, 10, "Tailored Resume Output\n(JSON / PDF / DOCX)"),
    }

    style_map = {
        "resume": "io",
        "job": "io",
        "extractor": "process",
        "parser": "process",
        "main": "core",
        "matcher": "core",
        "generator": "core",
        "ats": "feedback",
        "reviser": "feedback",
        "formatters": "process",
        "output": "output",
    }

    for key, (x, y, w, h, label) in nodes.items():
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.35,rounding_size=0.9",
            linewidth=1.2,
            edgecolor=edge_color,
            facecolor=box_colors[style_map[key]],
        )
        ax.add_patch(patch)
        ax.text(
            x + w / 2,
            y + h / 2,
            label,
            ha="center",
            va="center",
            fontsize=9,
            color=edge_color,
            fontweight="bold" if key in ["main", "generator"] else "normal",
        )

    def mid_bottom(node: str):
        x, y, w, h, _ = nodes[node]
        return (x + w / 2, y)

    def mid_top(node: str):
        x, y, w, h, _ = nodes[node]
        return (x + w / 2, y + h)

    def mid_left(node: str):
        x, y, w, h, _ = nodes[node]
        return (x, y + h / 2)

    def mid_right(node: str):
        x, y, w, h, _ = nodes[node]
        return (x + w, y + h / 2)

    def arrow(p1, p2, rad=0.0, style="-|>", color=None, lw=1.4, linestyle="solid"):
        if color is None:
            color = arrow_color
        arr = FancyArrowPatch(
            p1,
            p2,
            connectionstyle=f"arc3,rad={rad}",
            arrowstyle=style,
            mutation_scale=11,
            linewidth=lw,
            linestyle=linestyle,
            color=color,
        )
        ax.add_patch(arr)

    arrow(mid_bottom("resume"), mid_top("extractor"))
    arrow(mid_bottom("job"), mid_top("parser"))
    arrow(mid_bottom("extractor"), mid_left("main"))
    arrow(mid_bottom("parser"), mid_right("main"))
    arrow(mid_bottom("main"), mid_top("matcher"))
    arrow(mid_bottom("matcher"), mid_top("generator"))
    arrow(mid_bottom("generator"), mid_top("formatters"))
    arrow(mid_bottom("formatters"), mid_top("output"))

    arrow(mid_left("reviser"), mid_right("ats"), color=feedback_color)
    arrow(mid_top("ats"), (50, 30), rad=-0.25, color=feedback_color, linestyle="dashed")
    arrow(mid_top("reviser"), (50, 30), rad=0.25, color=feedback_color, linestyle="dashed")
    arrow(mid_bottom("generator"), mid_top("reviser"), rad=0.25, color=feedback_color)

    ax.text(
        50,
        98,
        title,
        ha="center",
        va="top",
        fontsize=14,
        fontweight="bold",
        color=title_color,
    )

    legend_y = 94 if variant == "standard" else 93.5
    legend_items = [
        ("Input", box_colors["io"]),
        ("Core Orchestration", box_colors["core"]),
        ("Processing", box_colors["process"]),
        ("Feedback Loop", box_colors["feedback"]),
        ("Final Output", box_colors["output"]),
    ]
    start_x = 8
    for name, col in legend_items:
        ax.add_patch(
            FancyBboxPatch(
                (start_x, legend_y - 2.4),
                10,
                2.2,
                boxstyle="round,pad=0.1,rounding_size=0.4",
                edgecolor=edge_color,
                facecolor=col,
                linewidth=0.8,
            )
        )
        ax.text(start_x + 11.2, legend_y - 1.3, name, va="center", fontsize=8, color=edge_color)
        start_x += 19

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    standard_out = base_dir / "system_architecture_diagram.png"
    report_out = base_dir / "system_architecture_diagram_report.png"
    draw_architecture(standard_out, variant="standard")
    draw_architecture(report_out, variant="report")
    print(f"Created: {standard_out}")
    print(f"Created: {report_out}")
