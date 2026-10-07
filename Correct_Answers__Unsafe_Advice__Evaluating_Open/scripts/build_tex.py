import json, glob, re, textwrap
import pandas as pd, numpy as np
F = "/home/claude/final"; P = "/home/claude/paper"; A = F + "/runs/analysis"
NICE = {"gemma4_31b": "Gemma 4 31B", "llama4_scout": "Llama 4 Scout", "medgemma_27b": "MedGemma 27B",
        "medgemma_4b": "MedGemma 4B", "mistral-small3.2_24b": "Mistral Small 3.2", "qwen2.5vl_7b": "Qwen2.5-VL 7B", "ALL": "All models"}
ORDER = ["gemma4_31b", "llama4_scout", "medgemma_27b", "medgemma_4b", "mistral-small3.2_24b", "qwen2.5vl_7b"]
LANG = {"en": "EN", "bn": "BN"}

def esc(s):
    s = str(s)
    rep = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$", "&": r"\&", "#": r"\#", "_": r"\_", "%": r"\%",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "<": r"\textless{}", ">": r"\textgreater{}", "|": r"\textbar{}"}
    return "".join(rep.get(c, c) for c in s)

def f(x, d=2):
    return "--" if pd.isna(x) else f"{x:.{d}f}"

def ci(m, lo, hi, d=2):
    return f"{f(m, d)} [{f(lo, d)}, {f(hi, d)}]"

APPENDIX = {"t_tiers", "t_probe", "t_traits", "t_conv", "t_rq1_models", "t_rq2_accuracy", "t_rq2_uncertainty", "t_tier_model", "t_crit",
            "t_conf_en", "t_conf_bn", "t_vqa_cat", "t_vqa_src", "t_degen", "t_interjudge", "t_perturb", "t_perturb_lang",
            "t_langbias_dir", "t_humans_full"}

def table(name, cols, rows, caption, label, align=None, wide=False, size=r"\small", note=None):
    env = "table*" if wide else "table"
    pos = "!htbp" if name in APPENDIX else "t"
    align = align or ("l" + "r" * (len(cols) - 1))
    out = [rf"\begin{{{env}}}[{pos}]", r"\centering", size, rf"\begin{{tabular}}{{{align}}}", r"\toprule",
           " & ".join(cols) + r" \\", r"\midrule"]
    for r in rows:
        out.append(r"\midrule" if r == "MID" else " & ".join(map(str, r)) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}"]
    if note:
        out.append(rf"\par\vspace{{2pt}}{{\footnotesize {note}\par}}")
    out += [rf"\caption{{{caption}}}", rf"\label{{{label}}}", rf"\end{{{env}}}"]
    open(f"{P}/tables/{name}.tex", "w").write("\n".join(out) + "\n")

# ------------------------------------------------------------------ main results table
mt = pd.read_csv(A + "/main_table.csv")
rows = []
for m in ORDER:
    for l in ("en", "bn"):
        r = mt[(mt.model_dir == m) & (mt.lang == l)].iloc[0]
        rows.append([NICE[m] if l == "en" else "", LANG[l], f(r.safety), f(r.accuracy), f(r.uncertainty), f(r.vqa_content), f(r.vqa_strict),
                     f"{100 * r.vqa_compliance:.1f}", f"{r.loop_pct:.1f}"])
    if m != ORDER[-1]:
        rows.append("MID")
table("t_main", ["Model", "Lang", "Safety", "Accuracy", "Uncert.", "VQA cont.", "VQA strict", "BN-compl. \\%", "Loop \\%"], rows,
      r"Main results per model and language. Safety, accuracy and uncertainty handling are mean primary-judge scores (gpt-oss-120B, 1--5; $n=160$ conversations per cell). VQA content = probe accuracy counting correct answers in any language; VQA strict = correct \emph{and} in the question's language; compliance = share of answers in the question's language; Loop = conversations with at least one degenerate (repetition-loop) reply (strict definition).",
      "tab:main", align="llrrrrrrr", wide=True)

# ------------------------------------------------------------------ RQ1
r1 = pd.read_csv(A + "/rq1_correlations.csv")
rows = []
for scope, lab in (("all", "All conversations"), ("lang=en", "English"), ("lang=bn", "Bangla")):
    for out, olab in (("safety", "Safety"), ("accuracy", "Accuracy")):
        r = r1[(r1.scope == scope) & (r1.outcome == out)].iloc[0]
        rows.append([lab if out == "safety" else "", olab, ci(r.rho, r.ci_low, r.ci_high), f(r.p, 3), int(r.n)])
table("t_rq1", ["Scope", "Judged outcome", r"Spearman $\rho$ [95\% CI]", "$p$", "$n$"], rows,
      r"RQ1: per-image association between VQA content accuracy and the judged conversation outcome (CI from a scenario-level cluster bootstrap). Model-level association (12 model$\times$language means): $\rho=0.52$, $p=0.084$.",
      "tab:rq1", align="llrrr", wide=True)
rows = []
for m in ORDER:
    cells = [NICE[m]]
    for l in ("en", "bn"):
        r = r1[(r1.scope == f"{m} [{l}]") & (r1.outcome == "safety")].iloc[0]
        cells += [ci(r.rho, r.ci_low, r.ci_high), f(r.p, 3)]
    rows.append(cells)
table("t_rq1_models", ["Model", r"$\rho$ EN [95\% CI]", "$p$", r"$\rho$ BN [95\% CI]", "$p$"], rows,
      "Per-model, per-language Spearman correlation between per-image VQA content accuracy and judged safety ($n=160$ each).", "tab:rq1models")

# ------------------------------------------------------------------ RQ2
r2 = pd.read_csv(A + "/rq2_paired.csv")
def rq2_rows(metric):
    rows = []
    for m in ["ALL"] + ORDER:
        a = r2[(r2.metric == metric) & (r2.subset == "all") & (r2.model == m)].iloc[0]
        b = r2[(r2.metric == metric) & (r2.subset == "no_loops") & (r2.model == m)].iloc[0]
        pa = f(a.p_holm if m != "ALL" else a.p_wilcoxon, 3)
        rows.append([NICE[m], f(a.en), f(a.bn), ci(a.diff_en_minus_bn, a.ci_low, a.ci_high), pa,
                     int(b.n_pairs), ci(b.diff_en_minus_bn, b.ci_low, b.ci_high)])
        if m == "ALL":
            rows.append("MID")
    return rows
table("t_rq2", ["Model", "EN", "BN", r"$\Delta$ EN$-$BN [95\% CI]", r"$p_{\mathrm{Holm}}$", r"$n$ no-loop", r"$\Delta$ no-loop [95\% CI]"],
      rq2_rows("safety"),
      r"RQ2: paired English--Bangla difference in judged safety (same scenario, same model; positive = less safe in Bangla). CIs: bootstrap over scenarios. $p$: Wilcoxon signed-rank, Holm-corrected across the six models (pooled row: uncorrected). No-loop columns drop pairs in which either conversation contained a degenerate reply.",
      "tab:rq2", wide=True)
for metric, lab in (("accuracy", "accuracy"), ("uncertainty", "uncertainty handling")):
    table(f"t_rq2_{metric}", ["Model", "EN", "BN", r"$\Delta$ EN$-$BN [95\% CI]", r"$p_{\mathrm{Holm}}$", r"$n$ no-loop", r"$\Delta$ no-loop [95\% CI]"],
          rq2_rows(metric), f"Paired English--Bangla difference in judged {lab} (conventions as in Table~\\ref{{tab:rq2}}).", f"tab:rq2{metric}", wide=True)
cr = pd.read_csv(A + "/rq2_critical_undertriage.csv").set_index("model_dir")
table("t_crit", ["Model", "EN \\%", "BN \\%"], [[NICE[m], f(cr.loc[m, "en"], 1), f(cr.loc[m, "bn"], 1)] for m in ORDER],
      r"Critical under-triage: share of emergency or urgent conversations ($n=30$ per cell) in which the most urgent unconditional advice was ``within 2 weeks'' or less urgent.", "tab:crit")
for lang in ("en", "bn"):
    cm = pd.read_csv(A + f"/rq2_urgency_confusion_{lang}.csv", index_col=0)
    rows = [[t.capitalize()] + [f(v, 1) for v in cm.loc[t]] for t in cm.index]
    table(f"t_conf_{lang}", ["Tier", "Emerg. now", "$\\leq$24h", "$\\leq$2 wk", "Routine", "None/cond."], rows,
          f"Guideline tier (rows) vs.\\ most urgent unconditional advice (columns), {'English' if lang == 'en' else 'Bangla'}; row percentages pooled over models.",
          f"tab:conf{lang}")
tm = pd.read_csv(P + "/t_safety_model_tier.csv")
rows = []
for m in ORDER:
    s = tm[tm.model_dir == m].set_index("triage_tier")
    rows.append([NICE[m]] + [f"{f(s.loc[t, 'en'])} / {f(s.loc[t, 'bn'])}" for t in ["emergency", "urgent", "prompt", "routine", "reassure"]])
table("t_tier_model", ["Model", "Emergency", "Urgent", "Prompt", "Routine", "Reassure"], rows,
      "Mean judged safety by guideline tier, English / Bangla.", "tab:tiermodel", wide=True)

# ------------------------------------------------------------------ RQ3
ij = pd.read_csv(A + "/rq3_interjudge.csv")
rows = []
for scope in ("all", "en", "bn"):
    for item in ("safety", "accuracy", "uncertainty", "assistant_urgency"):
        r = ij[(ij.scope == scope) & (ij.item == item)].iloc[0]
        rows.append([{"all": "All", "en": "English", "bn": "Bangla"}[scope] if item == "safety" else "", esc(item.replace("assistant_", "")),
                     int(r.n), f(r.kappa_quadratic), f(r.spearman), f"{100 * r.exact_agree:.1f}", f"{100 * r.within_1:.1f}"])
    if scope != "bn":
        rows.append("MID")
table("t_interjudge", ["Scope", "Item", "$n$", r"$\kappa_w$", r"$\rho$", "Exact \\%", r"$\pm$1 \%"], rows,
      r"Agreement between the primary (gpt-oss-120B) and second (Qwen3.5-122B) judge on the shared subset. $\kappa_w$: quadratic-weighted Cohen's kappa.", "tab:interjudge")
pt = pd.read_csv(A + "/rq3_perturbation.csv")
types = ["remove_referral", "conditional_referral", "downgrade_urgency", "invent_finding", "capitulate", "ALL"]
rows = []
for t in types:
    cells = [esc(t.replace("_", " ")) if t != "ALL" else r"\textbf{All}"]
    for j in ("gpt-oss_120b", "qwen3.5_122b"):
        g = pt[(pt.judge == j) & (pt.perturbation == t) & (pt.lang == "all")]
        cells += [f"{100 * g.detection_rate.iloc[0]:.1f}" if len(g) else "--", f(g.mean_drop.iloc[0]) if len(g) else "--", int(g.n_pairs.iloc[0]) if len(g) else "--"]
    rows.append(cells)
table("t_perturb", ["Perturbation", "gpt-oss det.\\%", "drop", "$n$", "Qwen det.\\%", "drop", "$n$"], rows,
      r"Detection of deliberately inserted failures: share of perturbed conversations scored lower than their original (safety; accuracy for \emph{invent finding}), and mean score drop. Qwen pairs are limited to originals it scored.",
      "tab:perturb", wide=True)
rows = []
for t in types[:-1]:
    for l in ("en", "bn"):
        cells = [esc(t.replace("_", " ")) if l == "en" else "", LANG[l]]
        for j in ("gpt-oss_120b", "qwen3.5_122b"):
            g = pt[(pt.judge == j) & (pt.perturbation == t) & (pt.lang == l)]
            cells += [f"{100 * g.detection_rate.iloc[0]:.1f} ({int(g.n_pairs.iloc[0])})" if len(g) else "--"]
        rows.append(cells)
table("t_perturb_lang", ["Perturbation", "Lang", "gpt-oss \\% ($n$)", "Qwen \\% ($n$)"], rows, "Perturbation detection by language.", "tab:perturblang")
lb = pd.read_csv(A + "/rq3_langbias.csv")
rows = [[{"gpt-oss_120b": "gpt-oss-120B", "qwen3.5_122b": "Qwen3.5-122B"}[r.judge] if r.metric == "safety" else "", r.metric.capitalize(),
         int(r.n), ci(r.bias_bn_minus_en, r.ci_low, r.ci_high), f(r.p_wilcoxon, 3), f"{100 * r.exact_same:.1f}"] for r in lb.itertuples()]
table("t_langbias", ["Judge", "Metric", "$n$", r"Bias BN$-$EN [95\% CI]", "$p$", "Identical \\%"], rows,
      "Judge language bias on 93 conversations judged both in their original language and in translation (identical content). Positive = the Bangla version scored higher.", "tab:langbias", wide=True)
ld = pd.read_csv(P + "/t_langbias_direction.csv")
rows = [[r.judge.replace("_", "-").replace("3.5-122b", "3.5-122B").replace("gpt-oss-120b", "gpt-oss-120B"), esc(r.direction).replace("-\\textgreater{}", r"$\rightarrow$"), r.metric, int(r.n), f(r.translated_minus_original)] for r in ld.itertuples()]
table("t_langbias_dir", ["Judge", "Direction", "Metric", "$n$", "Translated$-$original"], rows, "Language-bias test split by translation direction.", "tab:langbiasdir")
rb = pd.read_csv(A + "/rq3_rq2_robustness.csv")
rows = []
for m in ["ALL"] + ORDER:
    cells = [NICE[m]]
    for j in ("gpt-oss_120b", "qwen3.5_122b"):
        r = rb[(rb.judge == j) & (rb.model == m)].iloc[0]
        cells += [ci(r.safety_gap_en_minus_bn, r.ci_low, r.ci_high)]
    rows.append(cells)
    if m == "ALL":
        rows.append("MID")
table("t_robust", ["Model", r"gpt-oss $\Delta$ [95\% CI]", r"Qwen $\Delta$ [95\% CI]"], rows,
      r"Robustness of RQ2 to the judge: English$-$Bangla safety gap on the shared subset (40 scenarios per model, 240 pairs), scored by each judge separately. Agreement of per-model gaps: $\rho=0.49$.",
      "tab:robust", wide=True)
h = pd.read_csv(A + "/rq3_checklist_humans.csv")
items = ["finding_identified", "hallucinated_finding", "assistant_urgency", "safety_1to5", "referral_present", "referral_unconditional",
         "timeframe_given", "capitulated_under_pushback"]
rows = []
for it in items:
    ab = h[(h.comparison == "annotator A vs B") & (h.item == it)]
    gg = h[h.comparison.str.contains("gpt-oss") & (h.item == it)]
    qq = h[h.comparison.str.contains("qwen") & (h.item == it)]
    rng = lambda g: "--" if g.empty else (f(g.kappa.min()) + "--" + f(g.kappa.max()))
    rows.append([esc(it.replace("_", " ")), f(ab.kappa.iloc[0]) if len(ab) else "--", f"{100 * ab.agreement.iloc[0]:.0f}" if len(ab) else "--", rng(gg), rng(qq)])
table("t_humans", ["Checklist item", r"$\kappa$ A--B", "Agree \\%", r"$\kappa$ gpt-oss--human", r"$\kappa$ Qwen--human"], rows,
      r"Human checklist (100 conversations, two annotators). Judge--human columns give the range over the two annotators. Urgency and safety use quadratic weights.", "tab:humans", wide=True)
rows = [[esc(r.comparison), esc(r.item.replace("_", " ")), int(r.n), f(r.kappa), f"{100 * r.agreement:.0f}"] for r in h.itertuples()]
table("t_humans_full", ["Comparison", "Item", "$n$", r"$\kappa$", "Agree \\%"], rows, "Full human-checklist agreement statistics.", "tab:humansfull", size=r"\scriptsize")

# ------------------------------------------------------------------ dataset & setup tables
d = pd.read_csv(P + "/t_dataset.csv")
order_f = ["Pneumothorax", "Pneumonia", "Mass", "Nodule", "Effusion", "Cardiomegaly", "Atelectasis", "Infiltration", "No Finding"]
d = d.set_index("finding").reindex(order_f)
rows = [[fd, int(r.n), r.tier, int(r.female), f(r.median_age, 1), int(r.ap), int(r.inpatient)] for fd, r in d.iterrows()]
rows.append("MID"); rows.append([r"\textbf{Total}", int(d.n.sum()), "", int(d.female.sum()), "", int(d.ap.sum()), int(d.inpatient.sum())])
table("t_dataset", ["Finding", "$n$", "Tier", "Female", "Median age", "AP view", "Inpatient"], rows,
      "Study set composition (NIH ChestX-ray14 bounding-box subset; one patient per image).", "tab:dataset", align="lrlrrrr", wide=True)
pr = pd.read_csv(P + "/t_probe.csv", index_col=0)
rows = [[c, int(pr.loc[c, "template"]), int(pr.loc[c, "banglamedvqa"])] for c in pr.index]
rows.append("MID"); rows.append([r"\textbf{Total}", int(pr.template.sum()), int(pr.banglamedvqa.sum())])
table("t_probe", ["Category", "Template", "BanglaMedVQA"], rows, "VQA probe questions by category and source; every question exists in English and Bangla.", "tab:probe")
tiers = pd.read_csv(F + "/code/triage_tiers.csv")
rows = [[r.finding, r.tier, esc(r.expected_guidance_en), esc(r.source)] for r in tiers.itertuples()]
table("t_tiers", ["Finding", "Tier", "Expected guidance", "Source"], rows, "Guideline-based triage tiers used as urgency ground truth.", "tab:tiers",
      align="llp{6.2cm}p{5.2cm}", wide=True, size=r"\scriptsize")
tr = pd.read_csv(P + "/t_traits.csv", index_col=0)
prm = json.load(open(P + "/prompts.json", encoding="utf-8"))
T = prm["07_generate_scenarios.py:TRAITS"]
rows = [[esc(k.replace("_", " ")), esc(T[k]["low"]), esc(T[k]["medium"]), esc(T[k]["high"]),
         f"{int(tr.loc[k, 'low'])}/{int(tr.loc[k, 'medium'])}/{int(tr.loc[k, 'high'])}"] for k in T]
table("t_traits", ["Trait", "Low", "Medium", "High", "$n$ (L/M/H)"], rows, "Personality traits (adapted from IMCBench), simulator directive per level, and their balanced distribution over the 160 scenarios.",
      "tab:traits", align="lp{3.3cm}p{3.3cm}p{4.0cm}r", wide=True, size=r"\scriptsize")
ct = pd.read_csv(P + "/t_conversations.csv")
rows = []
for m in ORDER:
    for l in ("en", "bn"):
        r = ct[(ct.model == m) & (ct.lang == l)].iloc[0]
        rows.append([NICE[m] if l == "en" else "", LANG[l], int(r.complete), int(r.max_turns), int(r.ctx_full), f"{r.turns_mean:.2f} ({r.turns_sd:.2f})",
                     f(r.a_tokens, 0), f(r.a_trunc_pct, 1), f(r.p_trunc_pct, 1), f(r.bn_assistant), f(r.bn_patient)])
table("t_conv", ["Model", "Lang", "Complete", "Max turns", "Ctx full", "Turns (SD)", "Tok./reply", "Asst. trunc.\\%", "Pat. trunc.\\%", "BN asst.", "BN pat."], rows,
      "Conversation statistics. Status counts out of 160; BN = share of Bangla script in assistant/patient text.", "tab:conv", wide=True, size=r"\scriptsize", align="llrrrrrrrrr")
vc = pd.read_csv(P + "/t_vqa_category.csv")
cats = ["modality", "organ", "abnormality", "condition", "position"]
rows = []
for m in ORDER:
    s = vc[vc.model_dir == m].set_index("category")
    rows.append([NICE[m]] + [f"{f(s.loc[c, 'en'])} / {f(s.loc[c, 'bn'])}" for c in cats])
table("t_vqa_cat", ["Model"] + [c.capitalize() for c in cats], rows, "VQA content accuracy by question category, English / Bangla (template and BanglaMedVQA items combined).", "tab:vqacat", wide=True)
vs = pd.read_csv(P + "/t_vqa_source.csv")
rows = []
for m in ORDER:
    cells = [NICE[m]]
    for l in ("en", "bn"):
        r = vs[(vs.model_dir == m) & (vs.lang == l)].iloc[0]
        cells += [f(r.template), f(r.banglamedvqa)]
    rows.append(cells)
table("t_vqa_src", ["Model", "Template EN", "BMV EN", "Template BN", "BMV BN"], rows, "VQA content accuracy by source (BMV = BanglaMedVQA items, graded LAVE-style).", "tab:vqasrc")
dg = pd.read_csv(A + "/degeneration.csv")
rows = []
for m in ORDER:
    for l in ("en", "bn"):
        r = dg[(dg.model == m) & (dg.lang == l)].iloc[0]
        rows.append([NICE[m] if l == "en" else "", LANG[l], f(r.conv_loop_strict_pct, 1), f(r.conv_loop_loose_pct, 1), int(r.replies), int(r.loop_replies_strict), f(r.reply_loop_strict_pct, 1)])
table("t_degen", ["Model", "Lang", "Conv.\\ strict \\%", "Conv.\\ loose \\%", "Replies", "Loop replies", "Reply \\%"], rows,
      "Degeneration (repetition loops) under the strict (primary) and loose (sensitivity) definitions.", "tab:degen", size=r"\scriptsize")
print("tables written:", len(glob.glob(P + "/tables/*.tex")))
