# Bangla MedConv (BMC)

[![Paper](https://img.shields.io/badge/Paper-PDF-red.svg)](./Correct_Answers__Unsafe_Advice__Evaluating_Open_Weight.pdf)
[![Benchmark](https://img.shields.io/badge/Benchmark-1%2C920%20Consultations-blue.svg)](#benchmark-overview)
[![License](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](http://creativecommons.org/licenses/by-sa/4.0/)
[![Lab](https://img.shields.io/badge/Lab-CIMILab-indigo.svg)](https://github.com/CIMILab)

> **Correct Answers, Unsafe Advice? Evaluating Open-Weight Vision-Language Models in Bangla Image-Grounded Medical Consultations**  
> *Computation Informatics and Machine Intelligence Lab (CIMILab), University of Missouri, Columbia, USA*

---

## 📌 Overview

**Bangla MedConv (BMC)** is the first image-grounded, multi-turn medical consultation safety benchmark for **Bangla** (spoken by >250 million people) paired with an English twin for every conversation.

Evaluating six open-weight vision-language models (**Gemma 4 31B**, **Llama 4 Scout**, **MedGemma 27B**, **MedGemma 4B**, **Mistral Small 3.2**, **Qwen2.5-VL 7B**) across 160 frozen chest X-ray scenarios (**1,920 conversations**), we uncover critical safety gaps that standard single-turn VQA benchmarks miss entirely:

1. **VQA Accuracy Barely Predicts Advice Safety ($\rho = 0.17$):** High visual recognition accuracy does not guarantee clinically safe patient recommendations. In English, the correlation drops to $\rho = 0.05$ ($p = 0.097$).
2. **Language Disparity for Identical Patients ($\Delta = 0.44$):** Identical patient cases receive substantially lower safety scores in Bangla ($3.79 \rightarrow 3.35$, $p < 0.001$).
3. **Catastrophic Bangla Degeneration Loops:** Qwen2.5-VL 7B collapses into repetitive phrase generation loops in **83.1%** of Bangla conversations (vs. 0.6% in English), causing an 83.3% critical emergency under-triage rate.
4. **Reliable Clinician-Free Evaluation (84.9% Detection):** A dual-judge protocol successfully detects 84.9% of deliberately inserted clinical safety failures and exhibits negligible language bias ($+0.02$, $p = 0.910$).

---

## 🗂️ Repository Structure

```text
├── index.html                                                    # Interactive project webpage
├── static/
│   ├── css/
│   │   ├── bulma.min.css                                         # Base grid layout
│   │   ├── index.css                                             # Base styles
│   │   ├── bmc.css                                               # Academic clinical design system
│   │   └── bmc-extra.css                                         # Interactive arena & mobile responsiveness
│   ├── js/
│   │   ├── index.js                                              # Navigation & counters
│   │   └── bmc.js                                                # Interactive Arena comparator & chat stepper
│   └── images/
│       ├── bmc_logo.jpeg                                         # Project emblem
│       ├── cimilogo.png                                          # CIMILab emblem
│       ├── fig_method.png                                        # Figure 1: Benchmark pipeline (300 DPI)
│       ├── fig_rq1_vqa_vs_safety.png                             # Figure 2: RQ1 VQA vs. Safety
│       ├── fig_rq2_safety_gap.png                                # Figure 3: RQ2 English-Bangla safety gap
│       ├── fig_rq2_urgency.png                                   # Figure 4: Triage under-triage confusion
│       ├── fig_rq3_perturbation.png                              # Figure 5: Deliberate failure detection
│       └── figS_*.png                                            # Figures S1-S7: Supplementary analyses
├── Correct_Answers__Unsafe_Advice__Evaluating_Open_Weight.pdf    # Full conference paper PDF
├── appendix.pdf                                                  # Full appendix document
└── README.md                                                     # Project documentation
```

---

## 🚀 Running the Webpage Locally

The project webpage is built using pure semantic HTML5, Vanilla CSS, and JavaScript with zero build steps or heavy dependencies:

```bash
# Clone the repository
git clone https://github.com/pronad1/Project_website_Templete.git
cd Project_website_Templete

# Start a local web server (Python 3)
python -m http.server 8080

# Open in your browser
# Navigate to: http://localhost:8080/index.html
```

---

## 📑 Citation

If you find this work, benchmark, or code useful, please cite our paper:

```bibtex
@article{BanglaMedConv2026,
  title   = {Correct Answers, Unsafe Advice? Evaluating Open-Weight Vision-Language Models in Bangla Image-Grounded Medical Consultations},
  author  = {Pronad Roy and Md. Ashiqur Rahman and CIMILab Team},
  journal = {arXiv preprint},
  year    = {2026},
  url     = {https://github.com/CIMILab}
}
```

---

## ⚖️ License & Ethical Notice

The benchmark scenarios and synthetic patient profiles are released under the [Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)](http://creativecommons.org/licenses/by-sa/4.0/).  
*Disclaimer: Evaluated models are research prototypes and must not be used for unsupervised clinical triage or real-world patient care.*
