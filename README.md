# tex-camera-ready

Python script for cleaning LaTeX sources for dissemination. Helpful for producing camera-ready versions or arXiv pre-prints.

TLDR:

- Parses a LaTex source file and produces a new directory with a cleaned version
- Distills a single file with matching BibTeX entries
- Renames figures and copies directly included resources from TiKz figures
- Can crop fragments of larger images to reduce file size
- Can compile standalone figures and include them as PDFs instead
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
  -t, --tikz            Compile standalone TikZ figures and include resulting
                        PDFs  
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

## Handling Figures and their dependencies

I extensively use the `standalone` package for figures. In order to ensure correct building of both the main document, and the figures (when built independently), I define new commands to handle path differences. In the figure *.tex while, this would be:

```
\newcommand*{\FigPath}{../figures/}
...
\includegraphics[width=2in]{\FigPath schematic/graphics.jpg}}
```

In the main document, this becomes:

```
\newcommand*{\FigPath}{./figures/}
```

The tool will refactor `\FigPath` and `\DataPath` commands.

## Cropping

LaTeX allows you to trim included graphics files, but the bitmaps embedded in the PDF are actually full size. In order to reduce file size, this tool can crop the files for you. The graphics will be opened, trimmed, and saved in a new location. The parser looks for a trimming definition `,trim=A S D F,clip`, so the following line:

```
\subfloat[Thumbnails]{\includegraphics[width=\columnwidth,trim=10 10 10 10,clip]{figures/graphics.jpg}}
```

will be replaced with 
```
\subfloat[Thumbnails]{\includegraphics[width=\columnwidth]{includes/figure_01.jpg}}
```

## BibTeX Entries

The current implementation requires BibTeX entries to have the final closing bracket in a separate line. Attributes should also be defined in lower case. There might be more limitations. Entries copied from Google Scholar are typically handled correctly.


## Building Standalone Figures on the Fly

The tool can compile standalone figures and include them as graphics files (see `-t` option). In the process, `latexmk -pdf` will be called, and the resulting PDFs will be used in the include commands (`includestandalone` becomes `includegraphics`). For this to work, make sure that `latexmk` can build your figures with the figure directory as the current dir. 
