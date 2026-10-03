# ReLiC Immune Error Signal Screen

This is a **public, non-interventional computational hypothesis test**.

## Hypothesis

Cancer cells can carry several classes of immune-visible anomaly: altered/stress ligands, antigen-presentation state, danger-context signals, and immune-evasion signals. The first screen asks a deliberately narrow question:

> In public melanoma bulk RNA-seq data, are stronger expression proxies for anomaly/stress visibility and danger context associated with stronger cytotoxic immune activity?

The screen does **not** attempt to alter cells, prescribe a treatment, or claim a cure.

## Public data

The workflow queries cBioPortal's public API and uses **Skin Cutaneous Melanoma (TCGA, PanCancer Atlas)**. cBioPortal reports 443 samples with RNA-seq in this study.

## Signatures

- anomaly visibility: MICA, MICB, ULBP1/2/3, HLA-A/B/C, B2M
- danger-context proxy: CALR, HMGB1, IFNB1, CXCL10
- cytotoxic activity: CD8A, NKG7, GNLY, GZMB, PRF1, IFNG
- immune evasion: CD274, IDO1, LGALS9

Each gene is standardized across available samples and group scores are means of standardized expression.

## Primary test

Spearman correlation between the combined visibility+danger score and the cytotoxic-activity score, with a bootstrap 95% confidence interval and Benjamini-Hochberg correction across the planned correlations.

A positive association is only an **observational signal**. Bulk RNA-seq mixes tumor and immune cells, so a positive result could reflect immune infiltration or shared inflammatory regulation.

## Reproducibility

The GitHub Actions workflow runs the analysis on a public server and publishes:

- results.md
- results.json
- sample_scores.csv

The workflow is intentionally read-only with respect to cBioPortal and the repository.

## Scientific boundary

CALR/HMGB1 transcript abundance is not evidence that those proteins were exposed or released during immunogenic cell death. This screen cannot establish causality, immune memory, clinical benefit, treatment efficacy, or a cure. Those claims would require independent cohorts and controlled biological/clinical research.
