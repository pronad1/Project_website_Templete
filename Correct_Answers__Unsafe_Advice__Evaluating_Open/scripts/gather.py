import json, glob, os, re
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
F = "/home/claude/final"; OUT = "/home/claude/paper"; FIG = OUT + "/figures"
A = F + "/runs/analysis"
NICE = {"gemma4_31b": "Gemma 4 31B", "llama4_scout": "Llama 4 Scout", "medgemma_27b": "MedGemma 27B",
        "medgemma_4b": "MedGemma 4B", "mistral-small3.2_24b": "Mistral Small 3.2", "qwen2.5vl_7b": "Qwen2.5-VL 7B"}
ORDER = list(NICE); EN, BN = "#1E40AF", "#047857"
safe = lambda s: re.sub(r"[^A-Za-z0-9._-]+", "_", s)
S = {}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

# ---- dataset
st = pd.read_csv(F + "/data/processed/study_set_final.csv"); sc = [json.loads(l) for l in open(F + "/data/scenarios/scenarios.jsonl", encoding="utf-8")]
scd = pd.DataFrame(sc)
comp = st.groupby("finding").agg(n=("scenario_id", "size"), tier=("triage_tier", "first"), female=("sex", lambda x: int((x == "F").sum())),
                                 median_age=("age", "median"), ap=("view", lambda x: int((x == "AP").sum())))
comp = comp.join(scd.groupby("finding").care_setting.apply(lambda x: int((x == "inpatient").sum())).rename("inpatient"))
S["dataset"] = {"n": len(st), "PA": int((st.view == "PA").sum()), "AP": int((st.view == "AP").sum()), "male": int((st.sex == "M").sum()),
                "female": int((st.sex == "F").sum()), "age_mean": round(st.age.mean(), 1), "age_sd": round(st.age.std(), 1),
                "inpatient": int((scd.care_setting == "inpatient").sum()), "outpatient": int((scd.care_setting == "outpatient").sum())}
comp.to_csv(OUT + "/t_dataset.csv")
pr = pd.read_csv(F + "/data/processed/probe_all.csv"); pr.groupby(["category", "source"]).size().unstack().fillna(0).astype(int).to_csv(OUT + "/t_probe.csv")
S["probe"] = {"total": len(pr), "template": int((pr.source == "template").sum()), "bmv": int((pr.source == "banglamedvqa").sum())}
S["intents"] = scd.intent.apply(lambda d: d["category"]).value_counts().to_dict()
S["narrators"] = scd.narrator.value_counts().to_dict()
pers = pd.DataFrame(list(scd.personality)); pers.apply(lambda c: c.value_counts()).T.fillna(0).astype(int).to_csv(OUT + "/t_traits.csv")

# ---- conversations
rows = []
for f in glob.glob(F + "/runs/conversations/*/*/*.json"):
    d = json.load(open(f, encoding="utf-8"))
    a = [t for t in d["turns"] if t["role"] == "assistant"]
    rows.append({"lang": d["lang"], "model": f.split("/")[-2], "status": d["status"], "turns": d["n_patient_turns"], "upload": d["upload_turn"],
                 "a_trunc": d.get("n_assistant_truncated", 0) > 0, "p_trunc": d.get("n_patient_truncated", 0) > 0,
                 "a_tokens": np.mean([t["tokens"] for t in a if t.get("tokens")]) if any(t.get("tokens") for t in a) else np.nan, "bn_a": d["assistant_bengali_ratio"], "bn_p": d["patient_bengali_ratio"],
                 "minutes": d["seconds"] / 60})
C = pd.DataFrame(rows)
ct = C.groupby(["model", "lang"]).agg(n=("status", "size"), complete=("status", lambda x: int((x == "complete").sum())),
                                      max_turns=("status", lambda x: int((x == "max_turns").sum())), ctx_full=("status", lambda x: int((x == "context_full").sum())),
                                      turns_mean=("turns", "mean"), turns_sd=("turns", "std"), a_tokens=("a_tokens", "mean"),
                                      a_trunc_pct=("a_trunc", lambda x: 100 * x.mean()), p_trunc_pct=("p_trunc", lambda x: 100 * x.mean()),
                                      bn_assistant=("bn_a", "mean"), bn_patient=("bn_p", "mean")).round(2)
ct.to_csv(OUT + "/t_conversations.csv")
S["conv"] = {"n": len(C), "turns_mean": round(C.turns.mean(), 2), "turns_sd": round(C.turns.std(), 2), "complete": int((C.status == "complete").sum()),
             "max_turns": int((C.status == "max_turns").sum()), "ctx_full": int((C.status == "context_full").sum()),
             "upload_dist": C[C.lang == "en"].groupby("upload").size().div(len(C) / 2).round(3).to_dict()}
fig, ax = plt.subplots(figsize=(6.5, 2.8))
for lang, col in (("en", EN), ("bn", BN)):
    v = C[C.lang == lang].turns.value_counts().sort_index()
    ax.bar(v.index + (-0.2 if lang == "en" else 0.2), v.values, width=0.4, color=col, label={"en": "English", "bn": "Bangla"}[lang])
ax.set_xlabel("Patient turns per conversation"); ax.set_ylabel("Conversations"); ax.legend(frameon=False); ax.set_xticks(range(1, 14))
fig.tight_layout(); fig.savefig(FIG + "/figS_conv_length.png", dpi=200); plt.close(fig)

# ---- judgments (primary) for extra breakdowns
J = pd.DataFrame([json.load(open(f)) for f in glob.glob(F + "/runs/judgments/gpt-oss_120b/*/*/*.json")])
J = J[J.raw_ok == True]
tier = J.groupby(["triage_tier", "lang"]).safety.mean().unstack().reindex(["emergency", "urgent", "prompt", "routine", "reassure"])
tier.round(2).to_csv(OUT + "/t_safety_by_tier.csv")
care = J.groupby(["care_setting", "lang"]).safety.mean().unstack().round(2); care.to_csv(OUT + "/t_safety_by_care.csv")
tm = J.groupby(["model_dir", "triage_tier", "lang"]).safety.mean().unstack().round(2); tm.to_csv(OUT + "/t_safety_model_tier.csv")
fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), gridspec_kw={"width_ratios": [3, 1.3]})
x = np.arange(5)
axes[0].bar(x - 0.2, tier["en"], 0.4, color=EN, label="English"); axes[0].bar(x + 0.2, tier["bn"], 0.4, color=BN, label="Bangla")
axes[0].set_xticks(x, [t.capitalize() for t in tier.index]); axes[0].set_ylabel("Mean safety (1-5)"); axes[0].set_ylim(1, 5); axes[0].legend(frameon=False)
axes[0].set_title("A. Safety by guideline tier (all models)")
xs = np.arange(len(care)); axes[1].bar(xs - 0.2, care["en"], 0.4, color=EN); axes[1].bar(xs + 0.2, care["bn"], 0.4, color=BN)
axes[1].set_xticks(xs, [c.capitalize() for c in care.index]); axes[1].set_ylim(1, 5); axes[1].set_title("B. By care setting")
fig.tight_layout(); fig.savefig(FIG + "/figS_safety_tier_care.png", dpi=200); plt.close(fig)
# score distribution
fig, axes = plt.subplots(1, 3, figsize=(11, 3.3), sharey=True)
for a, met in zip(axes, ("safety", "accuracy", "uncertainty")):
    dist = J.groupby(["model_dir", "lang"])[met].value_counts(normalize=True).unstack().fillna(0).reindex(columns=[1, 2, 3, 4, 5], fill_value=0)
    labels, bottom = [], None
    idx = [(m, l) for m in ORDER for l in ("en", "bn")]
    dist = dist.reindex(idx)
    cols = ["#7F1D1D", "#C2410C", "#E9C46A", "#93C5FD", "#1E3A8A"]
    left = np.zeros(len(idx))
    for k, s in enumerate([1, 2, 3, 4, 5]):
        a.barh(range(len(idx)), dist[s] * 100, left=left, color=cols[k], label=str(s)); left += dist[s].to_numpy() * 100
    a.set_yticks(range(len(idx)), [f"{NICE[m]} {'EN' if l == 'en' else 'BN'}" for m, l in idx], fontsize=7); a.invert_yaxis()
    a.set_title(met.capitalize()); a.set_xlabel("% of conversations")
axes[-1].legend(title="Score", frameon=False, bbox_to_anchor=(1, 1), loc="upper left", fontsize=7)
fig.tight_layout(); fig.savefig(FIG + "/figS_score_dist.png", dpi=200); plt.close(fig)

# ---- inter-judge confusion (safety)
Q = pd.DataFrame([json.load(open(f)) for f in glob.glob(F + "/runs/judgments/qwen3.5_122b/*/*/*.json")])
sub = set(open(F + "/runs/judge2_subset_ids.txt").read().split())
Q = Q[(Q.raw_ok == True) & (Q.think.fillna("off") == "off") & Q.scenario_id.isin(sub)]
m = J.merge(Q, on=["scenario_id", "model_dir", "lang"], suffixes=("_g", "_q"))
cm = confusion_matrix(m.safety_g.astype(int), m.safety_q.astype(int), labels=[1, 2, 3, 4, 5])
fig, ax = plt.subplots(figsize=(4, 3.5))
ax.imshow(cm, cmap="Purples")
for i in range(5):
    for j in range(5):
        ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8, color="white" if cm[i, j] > cm.max() * 0.55 else "#111")
ax.set_xticks(range(5), range(1, 6)); ax.set_yticks(range(5), range(1, 6))
ax.set_xlabel("Qwen3.5-122B safety"); ax.set_ylabel("gpt-oss-120B safety"); ax.set_title(f"Safety scores, n = {len(m)}")
fig.tight_layout(); fig.savefig(FIG + "/figS_interjudge_safety.png", dpi=200); plt.close(fig)

# ---- degeneration
dg = pd.read_csv(A + "/degeneration.csv")
dg.to_csv(OUT + "/t_degeneration.csv", index=False)
fig, ax = plt.subplots(figsize=(6.5, 2.8))
for k, (lang, col) in enumerate((("en", EN), ("bn", BN))):
    v = dg[dg.lang == lang].set_index("model").reindex(ORDER).conv_loop_strict_pct
    ax.bar(np.arange(6) + (k - 0.5) * 0.4, v, 0.4, color=col, label={"en": "English", "bn": "Bangla"}[lang])
    for i, val in enumerate(v):
        ax.text(i + (k - 0.5) * 0.4, val + 1.5, f"{val:.1f}", ha="center", fontsize=7)
ax.set_xticks(range(6), [NICE[m] for m in ORDER], fontsize=8, rotation=15); ax.set_ylabel("% conversations with a loop"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(FIG + "/figS_degeneration.png", dpi=200); plt.close(fig)

# ---- VQA breakdowns
mt = pd.read_csv(A + "/main_table.csv")
fig, ax = plt.subplots(figsize=(7.5, 3))
b = mt[mt.lang == "bn"].set_index("model_dir").reindex(ORDER); e = mt[mt.lang == "en"].set_index("model_dir").reindex(ORDER)
w = 0.2; x = np.arange(6)
ax.bar(x - 1.5 * w, e.vqa_content, w, color=EN, label="Content, English")
ax.bar(x - 0.5 * w, b.vqa_content, w, color=BN, label="Content, Bangla")
ax.bar(x + 0.5 * w, b.vqa_strict, w, color="#86EFAC", label="Strict, Bangla")
ax.bar(x + 1.5 * w, b.vqa_compliance, w, color="#CBD5E1", label="Answered in Bangla")
ax.set_xticks(x, [NICE[m] for m in ORDER], fontsize=8, rotation=15); ax.set_ylim(0, 1.05); ax.set_ylabel("Proportion"); ax.legend(frameon=False, fontsize=7, ncol=2)
fig.tight_layout(); fig.savefig(FIG + "/figS_vqa_breakdown.png", dpi=200); plt.close(fig)
vs = pd.read_csv(F + "/runs/vqa/summary.csv")
vs["model_dir"] = vs.model.map(safe)
vcat = vs.assign(c=vs.content_accuracy * vs.n).groupby(["model_dir", "lang", "category"]).agg(c=("c", "sum"), n=("n", "sum"))
vcat = (vcat.c / vcat.n).unstack(["lang"]).round(3); vcat.to_csv(OUT + "/t_vqa_category.csv")
vsrc = vs.assign(c=vs.content_accuracy * vs.n).groupby(["model_dir", "lang", "source"]).agg(c=("c", "sum"), n=("n", "sum"))
(vsrc.c / vsrc.n).unstack(["source"]).round(3).to_csv(OUT + "/t_vqa_source.csv")

# ---- human agreement figure
h = pd.read_csv(A + "/rq3_checklist_humans.csv")
items = ["finding_identified", "hallucinated_finding", "assistant_urgency", "safety_1to5", "referral_present", "referral_unconditional"]
fig, ax = plt.subplots(figsize=(8, 3.2))
groups = [("annotator A vs B", "#B45309", "Human vs human"), ("gpt-oss", "#334155", "gpt-oss vs humans"), ("qwen", "#6D28D9", "Qwen vs humans")]
for k, (key, col, lab) in enumerate(groups):
    vals = []
    for it in items:
        g = h[(h.item == it) & h.comparison.str.contains(key)]
        vals.append(g.kappa.mean() if len(g) else np.nan)
    ax.bar(np.arange(len(items)) + (k - 1) * 0.27, vals, 0.27, color=col, label=lab)
ax.set_xticks(range(len(items)), ["Finding\nnamed", "Finding\ninvented", "Urgency\n(weighted)", "Safety 1-5\n(weighted)", "Referral\npresent", "Referral\nunconditional"], fontsize=8)
ax.set_ylabel("Cohen's kappa"); ax.axhline(0, color="#94A3B8", lw=0.8); ax.legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(FIG + "/figS_human_agreement.png", dpi=200); plt.close(fig)

# ---- language bias by direction
rows = []
for judge in ("gpt-oss_120b", "qwen3.5_122b"):
    base = J if judge.startswith("gpt") else Q
    T = pd.DataFrame([json.load(open(f)) for f in glob.glob(F + f"/runs/validation/judgments_langbias/{judge}/*/*/*.json")])
    T = T[T.raw_ok == True]
    T["src_model"] = T.model_dir.str.split("__from_").str[0]; T["src_lang"] = T.model_dir.str.split("__from_").str[1]
    x = T.merge(base, left_on=["scenario_id", "src_model", "src_lang"], right_on=["scenario_id", "model_dir", "lang"], suffixes=("_t", "_o"))
    for direction, g in x.groupby("src_lang"):
        for met in ("safety", "accuracy", "uncertainty"):
            d = (g[f"{met}_t"] - g[f"{met}_o"]).astype(float)   # translated minus original
            rows.append({"judge": judge, "direction": "EN->BN" if direction == "en" else "BN->EN", "metric": met, "n": len(g),
                         "translated_minus_original": round(d.mean(), 3)})
pd.DataFrame(rows).to_csv(OUT + "/t_langbias_direction.csv", index=False)

json.dump(S, open(OUT + "/stats.json", "w"), indent=1, default=str)
print(json.dumps(S, indent=1, default=str)[:1500])
print(ct.to_string())
