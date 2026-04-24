# 123recipe

Turn any recipe URL or YouTube cooking video into a beautiful, print-ready Polish-language PDF — using an AI agent and a LaTeX template.

## How it works

1. Give your AI agent a recipe URL or YouTube link
2. The agent follows `agent_instructions.md` to extract the recipe and write a JSON file
3. You run `generate_recipe.py` to render the PDF

## Layout

```
┌──────────────────────────────────────────────┐
│              Nazwa przepisu                  │
├──────────┬───────────────────────────────────┤
│          │  [zdjęcie]                        │
│Składniki │  Gotowanie: 20 min  Przygot.: 10  │
│ • item   │                                   │
│ • item   │  Przygotowanie                    │
│ • item   │  1. Krok pierwszy…                │
│          │  2. Krok drugi…                   │
└──────────┴───────────────────────────────────┘
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/piotrb5e3/123recipe.git
cd 123recipe
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install pdflatex

- macOS: `brew install --cask mactex-no-gui`
- Ubuntu/Debian: `sudo apt install texlive-latex-extra`
- Windows: [MiKTeX](https://miktex.org/)

### 4. Install yt-dlp (YouTube recipes only)

```bash
# macOS
brew install yt-dlp

# pip
pip install -U yt-dlp
```

## Using with an AI agent

Point your agent at `agent_instructions.md` — it contains the full extraction workflow.

**GitHub Copilot CLI:**
```
@agent_instructions.md — here's a recipe URL: https://...
```

**Claude / Claude Code:**
```
Read agent_instructions.md and then process: https://...
```

**Any other agent:** paste the contents of `agent_instructions.md` into the system prompt or first message, then provide the URL.

Once the agent writes a `.json` file, generate the PDF:

```bash
python generate_recipe.py kurczak_z_ryzem.json
```

## Generating a PDF manually

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
