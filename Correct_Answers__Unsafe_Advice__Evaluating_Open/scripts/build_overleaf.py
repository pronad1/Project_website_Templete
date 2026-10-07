"""Build the fast Overleaf version: pdfLaTeX main paper + pre-built appendix PDF.

Run from the project folder (needs XeLaTeX locally):  python scripts/build_overleaf.py
Inputs : main_full_xelatex.tex (the complete XeLaTeX source) and its folders.
Outputs: main.tex (pdfLaTeX), appendix_prebuilt.pdf, appendix_labels.tex, bn_*.pdf (Bangla snippets).
"""
import re, shutil, subprocess, pathlib, os
from pypdf import PdfReader, PdfWriter

ROOT = pathlib.Path(__file__).resolve().parents[1]
FULL = ROOT / "main_full_xelatex.tex"
WORK = ROOT / "_build_full"

def run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 1) full XeLaTeX build (appendix on) to get the PDF and the label numbers
if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir()
for item in ["acl.sty", "acl_natbib.bst", "refs.bib", "fig_method.pdf", "figures", "tables", "appendix", "fonts"]:
    src = ROOT / item
    (shutil.copytree if src.is_dir() else shutil.copy)(src, WORK / item)
full = FULL.read_text(encoding="utf-8").replace(r"\newif\ifappendix \appendixfalse", r"\newif\ifappendix \appendixtrue")
(WORK / "full.tex").write_text(full, encoding="utf-8")
for cmd in (["xelatex", "-interaction=nonstopmode", "full.tex"], ["bibtex", "full"],
            ["xelatex", "-interaction=nonstopmode", "full.tex"], ["xelatex", "-interaction=nonstopmode", "full.tex"]):
    run(cmd, WORK)

# 2) appendix pages -> appendix_prebuilt.pdf
aux = (WORK / "full.aux").read_text(encoding="utf-8", errors="ignore")
labels = {m.group(1): (m.group(2), int(m.group(3)) if m.group(3).isdigit() else None)
          for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{([^}]*)\}", aux)}
start = labels["app:impl"][1]                      # first appendix page
reader = PdfReader(str(WORK / "full.pdf"))
writer = PdfWriter()
for i in range(start - 1, len(reader.pages)):
    writer.add_page(reader.pages[i])
with open(ROOT / "appendix_prebuilt.pdf", "wb") as fh:
    writer.write(fh)
print(f"appendix: pages {start}-{len(reader.pages)} of the full build ({len(reader.pages) - start + 1} pages)")

# 3) Bangla snippets as tiny vector images on the text baseline
body = full[full.index(r"\begin{document}"):full.index("\\ifappendix\n")]
phrases = {"বুকের এক্স-রে": "bn_chest_xray", "সিসিএক্স": "bn_cicix"}
for text, name in phrases.items():
    # Bangla runs in the Bangla font; ASCII punctuation (e.g. the hyphen) in the Times-like main font, as in the paper
    tex = re.sub(r"[\u0980-\u09FF\u200c\u200d]+(?: [\u0980-\u09FF\u200c\u200d]+)*", lambda m: r"{\bnfont " + m.group(0) + "}", text)
    doc = (r"\documentclass[11pt,border=0pt]{standalone}\usepackage{fontspec}\setmainfont{TeX Gyre Termes}"
           r"\newfontfamily\bnfont{NotoSansBengali}[Path=fonts/,Extension=.ttf,UprightFont=*-Regular,Script=Bengali,Scale=0.92]"
           r"\begin{document}\strut " + tex + r"\end{document}")
    (WORK / f"{name}.tex").write_text(doc, encoding="utf-8")
    run(["xelatex", "-interaction=nonstopmode", f"{name}.tex"], WORK)
    shutil.copy(WORK / f"{name}.pdf", ROOT / f"{name}.pdf")

# 4) main.tex for pdfLaTeX
pre = r"""% FAST OVERLEAF VERSION (pdfLaTeX). The appendix is included as a pre-built PDF (appendix_prebuilt.pdf).
% The complete XeLaTeX source with the editable appendix is main_full_xelatex.tex; after editing it, rebuild
% this version locally with:  python scripts/build_overleaf.py
\documentclass[11pt]{article}
\usepackage[final]{acl}
\usepackage{times}
\usepackage{latexsym}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{courier}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{algorithm}
\usepackage[noend]{algpseudocode}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{multirow}
\usepackage{caption}
\usepackage{xurl}
\usepackage[section]{placeins}
\usepackage{pdfpages}
\captionsetup{font=small}
\setlist{itemsep=1pt,topsep=3pt}
\newcommand{\bnimg}[1]{\raisebox{-\dp\strutbox}{\includegraphics{#1}}}% Bangla snippet (pre-rendered)
\input{appendix_labels}% numbers of appendix sections/tables/figures, from the full build
"""
m = re.search(r"\\newcommand\{\\bmc\}.*?\n\n", full, re.S)          # project macros
macros = "\n".join(l for l in m.group(0).splitlines() if l.startswith(r"\newcommand{\bmc}") or l.startswith(r"\newcommand{\gpt}") or l.startswith(r"\newcommand{\qw}"))
title = full[full.index(r"\title{"):full.index(r"\begin{document}")]
b = body
b = re.sub(r"(\\includegraphics(?:\[[^\]]*\])?\{figures/[^}]+)\.png\}", r"\1.pdf}", b)
b = b.replace(r"\bn{বুকের এক্স}-\bn{রে}", r"\bnimg{bn_chest_xray}").replace(r"\bn{সিসিএক্স}", r"\bnimg{bn_cicix}")
assert r"\bn{" not in b, "unhandled Bangla in main body"
main = pre + macros + "\n\n" + title + b + "\n\\clearpage\n\\includepdf[pages=-,link,linkname=appx]{appendix_prebuilt.pdf}\n\\end{document}\n"
(ROOT / "main.tex").write_text(main, encoding="utf-8")
# pre-build the bibliography so Overleaf does not need BibTeX (fewer passes = faster compiles)
tmp = ROOT / "_bbl"; tmp.mkdir(exist_ok=True)
for item in ["acl.sty", "acl_natbib.bst", "refs.bib"]:
    shutil.copy(ROOT / item, tmp / item)
(tmp / "b.tex").write_text(main.replace("\\includepdf", "%\\includepdf").replace("\\input{appendix_labels}", ""), encoding="utf-8")
for item in ["fig_method.pdf", "figures", "tables", "bn_chest_xray.pdf", "bn_cicix.pdf"]:
    src = ROOT / item
    (shutil.copytree if src.is_dir() else shutil.copy)(src, tmp / item)
run(["pdflatex", "-interaction=nonstopmode", "b.tex"], tmp); run(["bibtex", "b"], tmp)
shutil.copy(tmp / "b.bbl", ROOT / "refs_prebuilt.bbl"); shutil.rmtree(tmp)
main = main.replace("\\bibliography{refs}", "% Pre-built bibliography (no BibTeX needed). If you add or change citations, replace the next line with\n% \\bibliography{refs} and recompile (Overleaf then runs BibTeX automatically).\n\\input{refs_prebuilt.bbl}")
(ROOT / "main.tex").write_text(main, encoding="utf-8")

# 5) appendix labels: every label the main text references but does not define
refs = set(re.findall(r"\\(?:ref|label)\{([^}]+)\}", b))
defined = set(re.findall(r"\\label\{([^}]+)\}", b))
for t in re.findall(r"\\input\{(tables/[^}]+)\}", b):
    defined |= set(re.findall(r"\\label\{([^}]+)\}", (ROOT / (t + ".tex")).read_text(encoding="utf-8")))
need = sorted(r for r in refs - defined)
lines = ["% Generated by scripts/build_overleaf.py from the full XeLaTeX build. Links jump to the appendix pages."]
for k in need:
    num, page = labels[k]
    lines.append(rf"\newlabel{{{k}}}{{{{{num}}}{{{page}}}{{}}{{appx.{page - start + 1}}}{{}}}}")
(ROOT / "appendix_labels.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"main.tex written; {len(need)} appendix labels; snippets: {', '.join(phrases.values())}")
shutil.rmtree(WORK)
