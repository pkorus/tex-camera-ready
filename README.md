# tex-camera-ready

Python script for cleaning LaTeX sources for dissemination. Helpful for producing camera-ready versions or arXiv pre-prints.

TLDR:

- Parses a LaTex source file and produces a new directory with a cleaned version
- Distills a single file with matching BibTeX entries
- Renames figures and copies directly included resources from TiKz figures
- Can crop fragments of larger images to reduce file size
- Not thoroughly tested, and possibly buggy but saves me time

## Usage

```
usage: tex-camera-ready.py [-h] [-o OUTPUT] [-c] [-v] [-f] [-b] filename

LaTeX source cleanup: take a working LaTeX sources and export a copy for
dissemination (with resource refactoring, bibtex items selection, etc.)

positional arguments:
  filename              input file (*.tex)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory, default: ./final
  -c, --crop            Crop bitmaps based on LaTeX trim parameters
  -v, --verbose         Print analysis summary to stdout
  -f, --force           Force output to an existing directory
  -b, --bib             Cleanup Bibtex entries (leave only cited)
```

## Example

```bash
> python3 tex-camera-ready.py -b document.tex
Loaded 588 lines from document.tex
Writing to ./final_new

 + figure 01      : ./figures/Architecture.pdf
                  > includes/figure_01.pdf

 + figure 02      : ./figures/Pipeline.pdf
                  > includes/figure_02.pdf

 + figure 03      : ./figures/Results.tex
                  > includes/figure_03.tex
   Refactoring file ./figures/Results.tex -> ./final_new/includes/figure_03.tex
                    ../figures/Results-000.png
                    ../figures/Results-001.png
                    ../figures/Results-002.png
                    ../figures/Results-003.png

Missing dependencies (you may need to handle them manually):
 + figures/boxplot_accuracy.tex
   \inetdata

Found 40 citations:
  [1] Chen2008
  ...
  [40] Zhou2018
Found 3 Bibtex databases: ['../bib/surveys', '../bib/general', '../bib/software']
Parsing ../bib/surveys
Parsing ../bib/general
Parsing ../bib/software
Matched 40 entries

```

## Output Structure

```
.
├── bib
│   └── references.bib
├── document.tex
├── includes
│   ├── figure_01.pdf
│   ├── figure_02.pdf
│   └── figure_03.tex
└── resources
    └── figure_03
        ├── Results-000.png
        ├── Results-001.png
        ├── Results-002.png
        └── Results-003.png
```

## Ideas for Later

- Auto-compile TiKz figures and replace `includestandalone` with `includegraphics`
