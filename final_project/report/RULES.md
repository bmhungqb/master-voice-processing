# LaTeX writing rules for the report

These rules apply to `report/`. Follow them so that four people can edit in parallel without merge conflicts or inconsistent output. Slide-specific rules are in `../slides/RULE.md`, which also reuses the shared rules below (language, git workflow, numbers, citations, placeholders).

## 1. Language and structure

- Write everything in **English**. Only the names of people, institutions and quoted titles keep Vietnamese diacritics.
- Report top-level sections, in this order: `1 Introduction`, `2 Survey of Methods`, `3 Experiments` (selected paper, setup, demo, ablation study), `4 In-depth Analysis and Proposed Improvement`, `5 Conclusion`. Do not add or reorder top-level sections without team agreement.
- No appendix unless the team decides to add one.

## 2. File layout

- `main.tex` only holds `\input{...}` lines, title/cover and bibliography. No body text.
- `preamble.tex` holds all packages and macros. Put new packages and macros there, never in a section file.
- One file per top-level section in `sections/`, named `NN_name.tex` (`01_intro`, `02_survey`, ...). The cover is `sections/cover.tex`.
- Figures go in `figures/`. Reference them without the path (`\graphicspath` is set) and prefer vector PDF over PNG.
- All references go in a single `refs.bib`. The slides reuse it through `../report/refs.bib`, so keep the path and entry keys stable.
- Do not commit build files (`*.aux`, `*.log`, `*.bbl`, `*.pdf`, ...). The `.gitignore` covers them. Copy the final PDFs to the submission folder by hand.

## 3. Git workflow

- Each person edits their own section file on their own branch. Do not reformat or reflow files you do not own.
- One sentence per line is **not** required, but keep lines short enough to diff (wrap at about 100 characters) and never reflow a paragraph just for style.
- Merge through pull requests. The report must compile with `latexmk -pdf main.tex` before merging.

## 4. Numbers and claims

- Every number from a paper is wrapped in `\authorrep{...}` (author-reported, shown as superscript AR).
- Every number from our own runs is wrapped in `\ours{...}` (superscript OUR).
- Never mix the two in one column of a table without a note. State seed, dataset split and number of runs next to our own results.
- Every surveyed paper needs: reference, main idea, method, key results, strengths, weaknesses, relevance to this project (use `\paperbox`). Give the venue rank (A*/A/Q1/Q2) in the reference line.
- Count toward the survey threshold only A/A* conference or Q1/Q2 journal papers from the last 3-5 years. ICASSP and arXiv do not count.

## 5. Citations and references

- Cite with `\cite{key}`. Key format: `firstauthorYEARshortname`, for example `andrusenko2024ctcws`.
- Every `.bib` entry must be checked against the real paper (authors, venue, year, pages) before submission. Do not invent fields; leave a field out rather than guess.
- Cite the paper, not a blog or a mirror. Add a `url` only for code or datasets.

## 6. Figures, tables, equations

- Every figure and table has a caption and a label, and is referenced in the text with `\ref`/`\autoref`. Labels use prefixes: `fig:`, `tab:`, `eq:`, `sec:`.
- Tables use `booktabs` (`\toprule`, `\midrule`, `\bottomrule`), no vertical lines. Use `tabularx` for full-width tables.
- Captions go below figures and below tables, as set in the template.
- Number equations only when they are referred to later. Define every symbol where it first appears.
- Use `\%`, `\_`, and `\texttt{}` for code, commands, file names and parameter names (for example `\texttt{context\_score}`).
- Use `--` for ranges (`1--3`), `---` sparingly, and `~` before `\cite`/`\ref` to avoid a line break.

## 7. Placeholders

- Mark every unfinished spot with `\todo{what is missing}` (red). Before submission, `grep -rn "todo" sections/ main.tex` must return nothing.
- Do not delete the template structure to hide a `\todo`; fill it in.

## 8. Macros (defined in `preamble.tex`)

| Macro | Use |
|---|---|
| `\TVa` ... `\TVd` | Member names (TV1-TV4). Change names only here. |
| `\authorrep{x}` | Author-reported number |
| `\ours{x}` | Number from our own run |
| `\todo{x}` | Red placeholder |

Add a new macro only if it is used in at least two places.

## 9. Build and check

```bash
cd report && latexmk -pdf -interaction=nonstopmode main.tex
```

Before opening a pull request:

1. Zero LaTeX errors; no `undefined reference` or `undefined citation` warnings.
2. No overfull boxes wider than a few points in text or tables.
3. No `\todo` left in files you own (or a clear list of what remains).
4. Open the PDF and check the pages you changed.
