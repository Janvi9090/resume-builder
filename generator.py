"""
generator.py
Reads data/resume_data.json, fills templates/resume_template.tex using Jinja2,
and compiles the result into output/resume.pdf using pdflatex.
"""

import json
import os
import subprocess
import sys
from jinja2 import Environment, FileSystemLoader

# --- Jinja2 environment configured for LaTeX ---
# LaTeX uses { } heavily, which clashes with Jinja2's default {{ }} / {% %}
# syntax. These custom delimiters (\VAR{...}, \BLOCK{...}) avoid that clash.
latex_jinja_env = Environment(
    block_start_string='\\BLOCK{',
    block_end_string='}',
    variable_start_string='\\VAR{',
    variable_end_string='}',
    comment_start_string='\\#{',
    comment_end_string='}',
    line_statement_prefix='%%',
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    loader=FileSystemLoader('templates'),
)


def escape_latex(text):
    """
    Escape characters that have special meaning in LaTeX so user input
    (which may contain %, &, #, etc.) doesn't break compilation or,
    worse, inject LaTeX commands.
    """
    if not isinstance(text, str):
        return text

    replacements = {
        '\\': r'\textbackslash{}',
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    # Replace backslash first so we don't double-escape the backslashes
    # introduced by the other replacements.
    result = []
    for ch in text:
        result.append(replacements.get(ch, ch))
    return ''.join(result)


def sanitize(data):
    """Recursively escape every string value in the data structure."""
    if isinstance(data, dict):
        return {key: sanitize(value) for key, value in data.items()}
    if isinstance(data, list):
        return [sanitize(item) for item in data]
    if isinstance(data, str):
        return escape_latex(data)
    return data


def load_data(json_path):
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found. Run gui.py first to generate it.")
        sys.exit(1)

    with open(json_path, "r") as f:
        return json.load(f)


def render_template(data):
    template = latex_jinja_env.get_template("resume_template.tex")
    return template.render(**data)


def compile_pdf(tex_path, output_dir):
    """
    Run pdflatex on the .tex file. -interaction=nonstopmode prevents pdflatex
    from pausing to ask questions on errors (which would hang the script);
    instead it logs errors and continues where possible.
    """
    result = subprocess.run(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={output_dir}",
            tex_path,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("LaTeX compilation failed. Last part of the log:\n")
        print(result.stdout[-2000:])  # pdflatex errors show up in stdout, not stderr
        sys.exit(1)


def main():
    json_path = os.path.join("data", "resume_data.json")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    raw_data = load_data(json_path)
    raw_data.setdefault("heading_color", "2454A6")
    raw_data.setdefault("profiles", [])
    data = sanitize(raw_data)

    rendered_tex = render_template(data)

    tex_path = os.path.join(output_dir, "resume.tex")
    with open(tex_path, "w") as f:
        f.write(rendered_tex)

    compile_pdf(tex_path, output_dir)

    pdf_path = os.path.join(output_dir, "resume.pdf")
    if os.path.exists(pdf_path):
        print(f"Resume generated successfully: {pdf_path}")
    else:
        print("pdflatex ran but no PDF was produced. Check output/resume.log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()