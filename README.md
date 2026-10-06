# DSANet-ISLES

[![Dataset](https://img.shields.io/badge/Dataset-ISLES%202022-blue)](https://zenodo.org/records/7153326)
[![Paper](https://img.shields.io/badge/Paper-Under%20Review-red)](#citation)
[![License](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey)](http://creativecommons.org/licenses/by-sa/4.0/)

**DSANet-ISLES: An Interpretable Multi-Architecture Ensemble of DerNet, SegResNet, and Attention U-Net for Low-Resource Stroke Lesion Segmentation**

## Overview

DSANet-ISLES is a paper-aligned framework for 3D ischemic stroke lesion segmentation from multi-modal MRI. The method is designed for robust performance in low-resource clinical settings by combining complementary model families and a lightweight post-processing stack.

- Project page: pronad1.github.io/DSANet/
- Dataset: ISLES 2022 (https://zenodo.org/records/7153326)
- Paper status: Under review

## Abstract

Accurate automated segmentation of ischemic stroke lesions is critical for timely diagnosis and treatment planning. However, robust deployment is difficult in low-resource settings where compute budgets are limited and MRI quality is heterogeneous.

DSANet-ISLES addresses this challenge with an interpretable multi-architecture ensemble of DerNet, SegResNet, and Attention U-Net over FLAIR, DWI, and ADC modalities. Outputs are fused via validation-guided weighting and refined using thresholding, test-time augmentation (TTA), and morphological post-processing to improve robustness and suppress false positives.

## Main Contributions

1. Introduces a multi-architecture ensemble tailored for ischemic stroke lesion segmentation in low-resource environments.
2. Uses validation-guided weighted fusion to exploit complementary strengths of DerNet and Attention U-Net.
3. Integrates TTA-based prediction aggregation with connected-component filtering for robust final masks.
4. Reports strong performance on ISLES 2022 with interpretable and reproducible design choices.

## Dataset and Protocol

- Dataset: ISLES 2022
- Input modalities: FLAIR, DWI, ADC
- Data split: 70% train / 15% validation / 15% test
- Task: 3D voxel-wise lesion segmentation

## Experimental Setup

- Optimization: AdamW optimizer with cosine annealing schedule
- Initial learning rate: $1\times10^{-4}$
- Losses: DiceFocalLoss / DiceCELoss
- Training horizon: 100-150 epochs (model-dependent)
- Effective batch size: 1-4 (with gradient accumulation)
- Input crop size: $64 \times 64 \times 64$

## Method

### Pipeline Summary

1. Build 3D multi-modal inputs from FLAIR, DWI, and ADC.
2. Train DerNet, SegResNet, and Attention U-Net independently.
3. Fuse model probabilities with validation-driven weights.
4. Apply TTA aggregation.
5. Binarize and refine masks with connected-component filtering.

### Weighted Ensemble Formulation

$$
P_{ens} = w_D P_{DerNet} + w_A P_{AttUNet} + w_S P_{SegResNet}
$$

Final weights used in the reported setup:

$$
w_D = 0.7000000000000002,\quad w_A = 0.19999999999999982,\quad w_S = 0.1
$$


### TTA and Decision Rule

$$
\begin{aligned}
P_{TTA} = \frac{1}{3}\Big(&P_{ens}(x)
+ Flip_x^{-1}(P_{ens}(Flip_x(x))) \\
&+ Flip_y^{-1}(P_{ens}(Flip_y(x)))\Big)
\end{aligned}
$$

$$
\hat{Y} = \mathbb{1}[P_{TTA} \geq \tau], \quad \tau = 0.45
$$

Morphological post-processing removes connected components smaller than 30 voxels.

## Discussion

The reported performance indicates that combining heterogeneous architectures improves stability over single-model inference. In practice, weighted fusion captures complementary lesion evidence, while TTA and connected-component filtering reduce small noisy regions. This design is particularly suitable for constrained environments because it improves output quality without requiring complex deployment-time optimization.

## Why DSANet-ISLES Works

- Complementary experts reduce single-model failure modes.
- Validation-driven fusion stabilizes lesion probability estimates.
- TTA and morphology refinement suppress small noisy predictions.
- The full pipeline is practical for constrained-resource workflows.

## Conclusion

DSANet-ISLES provides an interpretable and reproducible ensemble strategy for ischemic stroke lesion segmentation using multi-modal MRI. The framework combines complementary model priors with lightweight refinement steps, yielding strong Dice and Micro-F1 performance on ISLES 2022 while remaining aligned with low-resource clinical deployment constraints.

## Repository Structure

```text
.
|- index.html
|- README.md
|- cimilab.md
`- static/
   |- css/
   |- images/
   `- js/
```

## Local Preview

```bash
python -m http.server 8000
```

Open http://localhost:8000 in your browser.

## Citation

```bibtex
@article{DSANetISLES2026,
  author  = {Anonymized Authors},
  title   = {DSANet-ISLES: An Interpretable Multi-Architecture Ensemble of DerNet, SegResNet, and Attention U-Net for Low-Resource Stroke Lesion Segmentation},
  journal = {Under Review},
  year    = {2026}
}
```

## Authors

- ~Anonymized Authors~


## License

See [LICENSE](LICENSE) for project licensing terms.
