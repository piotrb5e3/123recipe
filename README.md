# 123recipe

Generate beautiful recipe PDFs from a simple JSON file using a LaTeX template.

## Layout

```
┌──────────────────────────────────────────────┐
│           Recipe Name                        │
│              [photo]                         │
│   Cook: 20 min  │  Prep: 10 min  │ Serves: 4 │
├──────────┬───────────────────────────────────┤
│          │                                   │
│Ingredients  Instructions                     │
│ • item   │  1. Step one…                     │
│ • item   │  2. Step two…                     │
│          │                                   │
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
  "description": "Short tagline.",       // optional
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
