# LaTeX rules for the slides

Shared rules (English only, git workflow, `\authorrep` / `\ours` / `\todo`, citation keys, no build files in git) are in `../report/RULES.md`. This file only adds what is specific to slides.

## 1. Structure

- Beamer, theme `metropolis`, aspect ratio 16:9, 11 pt. Do not change the theme or the font size.
- Section order is the same as the report: `Introduction`, `Survey of Methods`, `Experiments` (demo and ablation), `In-depth Analysis`, `Conclusion`. Then a `Thank you` frame and a `References` frame in the appendix.
- Everything lives in `main.tex`, one `\section{}` per report section. If a section grows beyond about 8 frames, move it to `sections/NN_name.tex` and `\input` it.
- Packages and macros are added only in the preamble of `main.tex`, next to the existing ones.
- Figures go in `figures/` and are referenced without the path. Share figures with the report by copying the PDF, not by linking across folders.
- Bibliography comes from `../report/refs.bib`. Cite in the text as `[Author, Year]`-style short form only through `\cite`; the full list is on the last frame.

## 2. Time budget

- Video is 10-15 minutes including the demo. Plan about **1 frame per minute**, 14 content frames as a target, at most 18.
- Suggested split: Introduction 2, Survey 5-6, Experiments (demo + ablation) 5-6, Analysis 2, Conclusion 1.
- Frames for the title, outline, team, thank-you and references do not count toward the budget.

## 3. Frame content

- One idea per frame. At most **6 bullets**, each at most 2 lines. No paragraphs.
- Frame titles are short noun phrases; each ends where it says what the frame is about (`Group C: CTC-WS`, `Ablation: bias list size`), not a full sentence.
- One surveyed paper = one frame, two columns: **Main idea** on the left, **Pros / Cons** on the right. Venue and year in the title.
- Prefer a figure, diagram or result table over bullet text. Every figure must be readable at the back of the room: no figure text below about 14 pt.
- Tables: `booktabs`, no vertical lines, font not smaller than `\footnotesize`, at most 5 columns and 6 rows.
- Equations only when they are explained aloud; at most one per frame.
- Do not use animations (`\pause`, overlays) except for step-by-step diagrams. Slides must also make sense as a static PDF, because the PDF is a deliverable.

## 4. Numbers

- Same convention as the report: `\authorrep{}` for numbers from papers, `\ours{}` for our own runs. Add the line `AR: author-reported, OUR: our own runs.` under every table that contains either.
- Every result frame states dataset, metric and the main setting in the title or a one-line footnote.
- Highlight the best value in a table with `\textbf{}`; do not use color alone.

## 5. Visual style

- Use the theme's colors. At most two accent colors in diagrams; red is reserved for `\todo`.
- Keep a consistent color for each method across all frames (for example baseline gray, biased system blue).
- Plots: label axes with units, no chart junk, line width at least 1.5 pt, colorblind-safe palette.
- Screenshots (Colab, terminal) only when they prove something, cropped to the relevant part.

## 6. Demo frames

- One frame for the setup (paper, environment, data), one for the results table, one for a qualitative example (reference / baseline / biased hypothesis with the biased words in bold).
- Live demo or recording is in the video, not in the slides; the slide only says what the viewer will see.

## 7. Build and checks

```bash
cd slides && latexmk -pdf -interaction=nonstopmode main.tex
```

Before opening a pull request:

1. Zero LaTeX errors; no undefined citations or references.
2. No overfull frames: nothing cut off at the bottom or right edge.
3. `grep -n "todo" main.tex sections/` returns nothing for frames you own.
4. Page through the whole PDF once, at full screen, to check readability.
5. Names, student IDs and the supervisor list on the title slide match the report cover.
