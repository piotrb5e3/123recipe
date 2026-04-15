#!/usr/bin/env python3
"""
generate_recipe.py — Generate a PDF recipe card from a JSON file.

Usage:
    python generate_recipe.py recipe.json
    python generate_recipe.py recipe.json -o output.pdf
    python generate_recipe.py recipe.json -t custom_template.tex
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional
from urllib.error import URLError

import jinja2


# ── LaTeX escaping ────────────────────────────────────────────────────────────

def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in a plain-text string."""
    if not isinstance(text, str):
        text = str(text)
    mapping = {
        "\\": r"\textbackslash{}",
        "&":  r"\&",
        "%":  r"\%",
        "$":  r"\$",
        "#":  r"\#",
        "_":  r"\_",
        "{":  r"\{",
        "}":  r"\}",
        "~":  r"\textasciitilde{}",
        "^":  r"\textasciicircum{}",
    }
    # Character-by-character substitution so replacements don't re-trigger
    return "".join(mapping.get(c, c) for c in text)


# ── Template rendering ────────────────────────────────────────────────────────

def render_template(template_path: str, recipe: dict, output_tex: str) -> None:
    """Render the Jinja2 LaTeX template to *output_tex*."""
    template_dir = os.path.dirname(os.path.abspath(template_path))
    template_name = os.path.basename(template_path)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        # Custom delimiters to avoid clashing with LaTeX braces
        variable_start_string="<<",
        variable_end_string=">>",
        block_start_string="<%",
        block_end_string="%>",
        comment_start_string="<#",
        comment_end_string="#>",
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["latex"] = escape_latex

    template = env.get_template(template_name)
    rendered = template.render(recipe=recipe)

    with open(output_tex, "w", encoding="utf-8") as fh:
        fh.write(rendered)


# ── PDF compilation ───────────────────────────────────────────────────────────

def find_pdflatex() -> str:
    """Return the path to pdflatex or abort with a helpful message."""
    engine = shutil.which("pdflatex")
    if engine:
        return engine
    sys.exit(
        "Error: pdflatex not found.\n"
        "Install TeX Live (Linux/macOS):  https://tug.org/texlive/\n"
        "Install MiKTeX (Windows):        https://miktex.org/\n"
        "macOS quick install:             brew install --cask mactex-no-gui"
    )


def compile_pdf(tex_path: str, output_pdf: str) -> None:
    """Run pdflatex twice (for stable cross-references) and move the result."""
    tex_path = Path(tex_path).resolve()
    build_dir = tex_path.parent
    engine = find_pdflatex()

    for pass_num in range(1, 3):
        result = subprocess.run(
            [engine, "-interaction=nonstopmode",
             "-output-directory", str(build_dir),
             str(tex_path)],
            capture_output=True,
            text=True,
            errors="replace",
        )
        if result.returncode != 0:
            # Show the last portion of the log for diagnostics
            log_tail = result.stdout[-4000:] if result.stdout else result.stderr
            sys.exit(
                f"pdflatex failed on pass {pass_num}.\n"
                "─── Log (tail) ───\n"
                f"{log_tail}"
            )

    compiled = build_dir / (tex_path.stem + ".pdf")
    shutil.move(str(compiled), output_pdf)

    # Clean up auxiliary files
    for ext in (".aux", ".log", ".out"):
        aux = build_dir / (tex_path.stem + ext)
        if aux.exists():
            aux.unlink()


# ── Validation ────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = ("name", "cook_time", "ingredients", "instructions")


def validate(recipe: dict) -> None:
    missing = [f for f in REQUIRED_FIELDS if not recipe.get(f)]
    if missing:
        sys.exit(f"JSON is missing required field(s): {', '.join(missing)}")

    for i, group in enumerate(recipe["ingredients"]):
        if "items" not in group:
            sys.exit(
                f"Ingredient group {i} has no 'items' list. "
                "Each entry in 'ingredients' must have an 'items' key."
            )

    if not recipe["instructions"]:
        sys.exit("'instructions' list must not be empty.")


# ── Photo resolution ──────────────────────────────────────────────────────────

def _is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))


def resolve_photo(recipe: dict, json_dir: Path) -> None:
    """Resolve local photo paths to absolute. URL photos are left as-is."""
    if not recipe.get("photo"):
        return
    photo = recipe["photo"]
    if _is_url(photo):
        return  # downloaded later, inside the build temp dir
    photo_path = Path(photo)
    if not photo_path.is_absolute():
        photo_path = json_dir / photo_path
    photo_path = photo_path.resolve()
    if not photo_path.exists():
        print(f"Warning: photo not found at '{photo_path}' — it will be omitted from the PDF.")
        recipe["photo"] = None
    else:
        recipe["photo"] = str(photo_path)


def download_photo(url: str, dest_dir: Path) -> Optional[str]:
    """Download an image URL into *dest_dir*. Returns the local path, or None on failure."""
    parsed = urllib.parse.urlparse(url)
    encoded_path = urllib.parse.quote(parsed.path, safe="/%")
    safe_url = parsed._replace(path=encoded_path).geturl()
    ext = Path(parsed.path).suffix or ".jpg"
    dest = dest_dir / f"photo{ext}"
    print(f"  Downloading photo: {url}")
    try:
        urllib.request.urlretrieve(safe_url, dest)
        return str(dest)
    except URLError as exc:
        print(f"Warning: could not download photo ({exc}) — it will be omitted from the PDF.")
        return None


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a recipe PDF from a JSON file."
    )
    parser.add_argument("json_file", help="Path to the recipe JSON file")
    parser.add_argument(
        "-o", "--output",
        help="Output PDF path (default: <recipe name>.pdf next to the JSON file)",
    )
    parser.add_argument(
        "-t", "--template",
        help="Path to a custom Jinja2 LaTeX template "
             "(default: recipe_template.tex next to this script)",
    )
    args = parser.parse_args()

    # Load and validate recipe data
    json_path = Path(args.json_file).resolve()
    if not json_path.exists():
        sys.exit(f"Error: JSON file not found: {json_path}")

    with open(json_path, encoding="utf-8") as fh:
        recipe = json.load(fh)

    validate(recipe)
    resolve_photo(recipe, json_path.parent)

    # Locate template
    script_dir = Path(__file__).parent
    template_path = args.template or str(script_dir / "recipe_template.tex")
    if not Path(template_path).exists():
        sys.exit(f"Error: template not found: {template_path}")

    # Output path
    if args.output:
        output_pdf = Path(args.output).resolve()
    else:
        safe_name = re.sub(r"[^\w\-]", "_", recipe.get("name", "recipe"))
        output_pdf = json_path.parent / f"{safe_name}.pdf"

    # Build in a temporary directory so auxiliary files don't pollute anything
    with tempfile.TemporaryDirectory(prefix="recipe_build_") as tmp:
        tmp_path = Path(tmp)
        tex_file = tmp_path / "recipe.tex"

        # Download URL photo into the build dir so pdflatex can reach it
        if recipe.get("photo") and _is_url(recipe["photo"]):
            recipe["photo"] = download_photo(recipe["photo"], tmp_path)

        # Copy template into tmp so relative \includegraphics paths work correctly
        # (pdflatex resolves images relative to the .tex file location)
        shutil.copy(template_path, tmp_path / Path(template_path).name)

        render_template(
            str(tmp_path / Path(template_path).name),
            recipe,
            str(tex_file),
        )
        compile_pdf(str(tex_file), str(output_pdf))

    print(f"✓ PDF generated: {output_pdf}")


if __name__ == "__main__":
    main()
