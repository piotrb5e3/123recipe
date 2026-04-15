# 123recipe

Generate beautiful recipe PDFs from a simple JSON file using a LaTeX template.

## Layout

```
┌──────────────────────────────────────────────┐
│              Recipe Name                     │
├──────────┬───────────────────────────────────┤
│          │  [photo]                          │
│Ingredients  Cook: 20 min  Prep: 10 min       │
│ • item   │                                   │
│ • item   │  Instructions                     │
│ • item   │  1. Step one…                     │
│          │  2. Step two…                     │
└──────────┴───────────────────────────────────┘
```

## Requirements

- Python 3.8+
- [TeX Live](https://tug.org/texlive/) or [MiKTeX](https://miktex.org/) (`pdflatex` must be in `PATH`)
  - macOS: `brew install --cask mactex-no-gui`
  - Ubuntu/Debian: `sudo apt install texlive-latex-extra`

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### yt-dlp (optional — YouTube recipes only)

`yt-dlp` is only needed when converting YouTube videos into recipes. Install a recent version via Homebrew (recommended) or pip:

```bash
# Homebrew (macOS) — always up to date
brew install yt-dlp

# pip — requires Python 3.10+
pip install -U yt-dlp
```

## Usage

```bash
python generate_recipe.py example_recipe.json
python generate_recipe.py example_recipe.json -o my_recipe.pdf
python generate_recipe.py example_recipe.json -t custom_template.tex
```

## JSON schema

```jsonc
{
  "name":        "Recipe Name",          // required
  "cook_time":   "20 min",               // required
  "prep_time":   "10 min",               // optional
  "servings":    4,                      // optional
  "source":      "https://example.com",  // optional — rendered at the bottom for attribution
  "photo":       "path/to/photo.jpg",    // optional (relative to JSON file)

  // required — list of ingredient groups
  "ingredients": [
    {
      "group": "Group label",            // optional — omit for ungrouped
      "items": [
        { "amount": "400 g", "name": "spaghetti" },
        { "amount": "",      "name": "salt"       }  // empty amount is fine
      ]
    }
  ],

  // required — ordered list of instruction strings
  "instructions": [
    "Step one.",
    "Step two."
  ]
}
```

See `example_recipe.json` for a full working example.

## Customising the template

`recipe_template.tex` is a [Jinja2](https://jinja.palletsprojects.com/) template
with custom delimiters that avoid conflicts with LaTeX syntax:

| Purpose   | Delimiter      |
|-----------|---------------|
| Variable  | `<< var >>`   |
| Block     | `<% if … %>`  |
| Comment   | `<# … #>`     |

The `latex` filter (e.g. `<< recipe.name \| latex >>`) escapes special LaTeX characters automatically.
