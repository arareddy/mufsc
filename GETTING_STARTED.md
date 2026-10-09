# Getting started

Download the complete reproducibility ZIP from the [v1.0.0 repository release](https://github.com/arareddy/mufsc/releases/tag/v1.0.0) and extract it in a local working directory. It includes the data; no account or raw-dataset download is needed. A Git clone contains the code, documentation, metadata and compact evidence, but omits `data/**/*.npz`. Copy the ZIP's data directory into the clone if using that route.

Use Python 3.12 and install the pinned requirements described in README.md. Start with:

```sh
python reproduce.py verify --output ../ftf-checks/verify
python reproduce.py aggregate --output ../ftf-checks/tables
```

Use new output directories. The first command checks the frozen scientific sources and data; the second regenerates table summaries from saved evidence, not from new experiments. For fresh execution, see the README's representative and full-grid commands. Timings depend on hardware and execution conditions; see TIMING_SCOPE.md. Lean reproduction is optional and separate, described in formal_verification/README.md.

For agents: read AI_REPRODUCTION_GUIDE.md, use one benchmark process at a time, and distinguish supplied historical receipts from checks you run yourself.
