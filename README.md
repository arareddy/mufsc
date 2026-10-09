# MUFSC: Machine Unlearning for Federated Socially Fair k-Means Clustering

Public reproducibility materials for the September 26, 2026 manuscript.

- [Complete reproducibility package, including processed data](https://github.com/arareddy/mufsc/releases/download/v1.0.0/Federated_Fair_Clustering_Unlearning_Reproducibility_v1.0.0.zip)
- [Release and checksums](https://github.com/arareddy/mufsc/releases/tag/v1.0.0)

GitHub hosts only the supplementary material. The manuscript PDF and its complete LaTeX source will be distributed through arXiv; its link will be added after announcement.

The complete release ZIP includes the frozen processed datasets. In a Git clone, the NPZ arrays are intentionally excluded from version control: download the release ZIP and extract its `data/` directory into this repository before running the commands below. Scientific source, dataset identities, saved results and Lean proof bundles are preserved from the ICLR review supplement.

Authors: Aravind Reddy*, Deeraj S K*, Mohd Wasif Raza*, and Saurav Prakash (*equal contribution).

See [PUBLIC_RELEASE.md](PUBLIC_RELEASE.md) for provenance, [DATA.md](DATA.md) for data attribution and preprocessing limits, and [LICENSES.md](LICENSES.md) for rights.

This package contains the frozen scientific implementations, safe processed datasets, exact experiment configurations, compact results, verification evidence and portable reproduction commands for P1–P4 and the eight additional studies. No account, private repository, author machine or network access is needed after dependencies are installed.

## Find the main paper results

- **Table 1 (`tab:replay-main`)**: original P2/P3 total algorithm and E2E ratios, losses and useful coverage. Start with `PAPER_CLAIMS_SNAPSHOT.md` and `evidence/original_p2_p3/`.
- **Table 2 (`tab:client-main`)**: compact whole-client T=0 versus canonical Direct T=1/T=2, with the quality cost of changing the refinement budget. See `evidence/Client_Deletion/` and `evidence/Client_Refinement/`.
- **Table 3 (`tab:lloyd-main`)**: matched-start fair versus Lloyd refinement and group/population costs. See `evidence/Lloyd_Comparison/`.
- **Mathematical proof scope**: `formal_verification/README.md` and the label-based `formal_verification/THEOREM_COVERAGE.md`.

All original compact appendix evidence, including the separate multi-group prototype, is retained. `PAPER_CLAIMS_SNAPSHOT.md` maps stable appendix labels to package paths. This public release derives from review supplement v2, including its frozen proof material and reviewer navigation; experimental code, inputs and saved results are unchanged. Packaging did not rerun full experiments or compile Lean.

## Setup

Use Python 3.12 (tested with 3.12.14) in a new local working directory. The tested scientific environment is NumPy 2.3.5, pandas 2.3.3, pytest 9.1.1 and Matplotlib 3.10.8. CPU only. All commands force five numerical-library thread settings to one. Dependencies are not bundled; installing them needs an existing wheel cache or network access.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r environment/requirements.txt
.venv/bin/python reproduce.py list
```

Use `python` below to mean that environment's interpreter. On Windows, use its corresponding executable. `serial.py` uses POSIX file locking; the scientific commands themselves do not require it. Run only one benchmark at a time. Put output directories outside the extracted release and outside synchronized cloud folders. Every output directory must be new; successful prior results are never overwritten.

## Level 1: offline checks and saved-evidence regeneration

```sh
python reproduce.py verify --output ../review-checks/verify
python serial.py -- python reproduce.py fixtures --output ../review-checks/fixtures
python reproduce.py aggregate --output ../review-checks/tables
python serial.py -- python plots.py --output ../review-checks/figures
```

`verify` checks the full release checksum manifest, immutable scientific-source hashes and all 11 NPZ datasets down to dtype, shape and raw array bytes. `fixtures` runs 193 core/independent tests plus separate scalar whole-client and multi-group suites. It includes ties, invalid requests, degeneracies, exact ideal-law enumeration and negative examples. `aggregate` verifies exact quality identities and reaggregates saved group/Lloyd means, variances and paired differences; it also inventories every CSV and summarizes paired timing ratios. `plots.py` regenerates seven newer-study PDFs and replots four original-experiment figures in a portable style from saved CSVs. Eleven anonymous saved PDFs are supplied under `figures/`.

These commands are offline. They do not rerun full real-data grids. Historical PASS evidence is labeled separately under `evidence/`; it is not presented as a new gate run.

## Level 2: representative real-data replay

```sh
python serial.py -- python reproduce.py run --study Lloyd_Comparison --case record_adult_s10000 --output ../review-checks/lloyd
python serial.py -- python reproduce.py run --study Client_Sequences --limit 1 --output ../review-checks/sequence
python serial.py -- python reproduce.py run --study P3 --limit 1 --output ../review-checks/acs
```

Every executable study supports `--limit 1`, `--case ID`, or `--full`. Exact IDs and parameters are in `configs/STUDY.json`. Use `STUDIES.json` and `REPRODUCTION_MATRIX.md` to select a claim. The replay command checks fresh versus deletion outputs using the complete indexed trajectory, final-center bytes and exact integer aggregates. Lloyd and the available c0 whole-client cases additionally match saved witnesses. Scientific timings in these receipts are diagnostic, not the published benchmark protocol.

## Level 3: full grids and fresh timings

```sh
python serial.py -- python reproduce.py run --study P1 --full --output ../review-full/P1
python serial.py -- python reproduce.py run --study P4 --full --output ../review-full/P4
python serial.py -- python reproduce.py run --study P2 --full --output ../review-full/P2
python serial.py -- python reproduce.py run --study P3 --full --output ../review-full/P3
python serial.py -- python reproduce.py run --study Lloyd_Comparison --full --output ../review-full/Lloyd
python serial.py -- python benchmarks.py run --study Client_Refinement --full --output ../review-full/client-timings
```

Repeat `reproduce.py run --study NAME --full` for Round_Budgets, Client_Deletion, Client_Refinement, Client_Diversity, Client_Sequences and Multigroup. Group_Quality is a derived view of existing populations, so it uses `aggregate` and `plots.py` and adds no independent training trial.

The separate synthetic administrative multi-group growth probe is `python serial.py -- python growth.py --output ../review-full/mg-growth` (m=2,3,5,9; three repeats).

`benchmarks.py` supports P2, P3, Round_Budgets, Client_Deletion, Client_Refinement, Client_Diversity, Client_Sequences and Multigroup. `--repeats N` changes only timing repetitions; defaults are four for Round_Budgets/Client_Refinement and three for the other studies. It rotates method order, gates repeated exact outputs and records new observations. Read `TIMING_SCOPE.md` before comparing times. Full-grid commands are provided; packaging validation does not claim to have rerun every full grid.

## What each directory means

- `core/src`: byte-identical current binary FTF-1D numerical source. Its returned map tag remains the historical string `FTF-1`; do not infer arithmetic version from that tag alone.
- `historical/p1_p4`: exact source snapshot recovered from the original P1/P4 run, with its verified snapshot identity documented in `PROVENANCE.md`.
- `variants`: isolated compact whole-client C0, ordinary Lloyd update/scorer, and categorical multi-group prototype. Positive-round multi-group is a distinct map.
- `data`: lossless NPZ arrays, row/client identities, metadata and frozen deletion requests. Load with `allow_pickle=False` only.
- `configs`, `expected`, `evidence`: frozen grid, selected complete expected witnesses, all compact tables/reports and historical verification records.
- `validation`, `timing_adapters`, `plotting`: portability wrappers and independent checks, described in `ADAPTATIONS.md`.
- `reference_harnesses`: sanitized original orchestration code for inspection. These files retain chronology and symbolic `study://` or `source://` paths; they are not the portable entry points.
- `raw_acs`: optional public-source acquisition/transform provenance. Frozen-data replay never downloads raw data.

See `DATA.md` for dataset attribution, masks and limitations; `CLAIMS_AND_LIMITATIONS.md` for scope; and `AI_REPRODUCTION_GUIDE.md` for an assistant execution recipe. The five optional formal-verification bundles are described in `formal_verification/README.md` and `formal_verification/THEOREM_COVERAGE.md`. They add no required experimental dependency and do not verify the whole paper or executable.
