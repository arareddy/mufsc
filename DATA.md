# Data and rights

All frozen experimental populations are included as compressed NPZ arrays: Adult (30,162 rows, 103 columns, 100 clients), Bank (45,211 rows, 42 columns, 20 clients), Credit (30,000 rows, 23 columns, 100 clients), and eight ACS populations ranging from 100,000 to 1,000,000 rows with 16 columns. The adjacent JSON is authoritative for exact dimensions, dtype and checksums. Containers contain no pickled objects. Conversion was checked array by array against the retained original data, including ordered row identities and persistent client IDs; no quantization, resampling or preprocessing was introduced by packaging.

## UCI attribution

The processed datasets are adaptations of:

- Becker, Barry and Kohavi, Ron (1996). Adult. UCI Machine Learning Repository. DOI [10.24432/C5XW20](https://doi.org/10.24432/C5XW20), [dataset page](https://archive.ics.uci.edu/dataset/2/adult).
- Moro, Sérgio; Rita, Paulo; Cortez, Paulo (2014). Bank Marketing. UCI Machine Learning Repository. DOI [10.24432/C5K306](https://doi.org/10.24432/C5K306), [dataset page](https://archive.ics.uci.edu/dataset/222/bank+marketing).
- Yeh, I-Cheng (2009). Default of Credit Card Clients. UCI Machine Learning Repository. DOI [10.24432/C55S3H](https://doi.org/10.24432/C55S3H), [dataset page](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients).

These UCI dataset pages identify [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/) as the license. Modifications in the inherited processed artifacts include numeric featurization/standardization and federation into clients. The review conversion changes the storage container only. The dataset creators do not endorse this study. The copyright notice for research code is separate, in `licenses/LEGACY_MIT_LICENSE.txt`.

The Adult and Credit original raw-to-processed pipelines are not completely recoverable from retained evidence. This package reproduces the frozen represented-data experiments; it does not claim byte-identical regeneration from new UCI downloads. In particular, the standardized representation was fitted before deletion and is held fixed. Its preprocessing influence is outside the deletion target. Bank's frozen processed representation is also used directly.

Binary group masks are: Adult group1 = supplied male mask; Bank group1 = supplied married mask; Credit group1 = education code in {1,2}. Group0 is the complement. Inspect the supplied `groups` arrays rather than infer labels from a rounded feature. The Credit grouping is an education-code grouping, not a claim about a universally appropriate protected attribute.

## ACS public-use source

U.S. Census Bureau, American Community Survey 2018 1-Year Public Use Microdata Sample, person files for the 50 states, excluding DC and Puerto Rico. [Official source directory](https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/), [2018 access page](https://www.census.gov/programs-surveys/acs/microdata/access/2018.html), and [Census citation policy](https://www.census.gov/about/policies/citation.html). Census is the original data source; the analysis and conclusions belong to the researchers.

The fixed ACS version is `acs2018-ftf1-p3-v1`, a new public population used in the accepted P3 execution. It is not a reconstruction of an unavailable older ACS population or an explanation of old seed1 behavior. `raw_acs/manifests/source_manifest_v1.json` gives all 50 official URLs and immutable ZIP/CSV hashes. These are public-use source record identifiers, not author identities.

Features: AGEP, SCHL, MAR, RELP, DIS, ESP, CIT, MIG, MIL, ANC, NATIVITY, DEAR, DEYE, DREM, SEX and RAC1P. Missing numeric codes are replaced with -1. Pooled standardization uses the frozen 50-state ordering, means and population standard deviations in `data/acs_transform.json`. Encoding uses b=12 and clip=8. Binary ACS groups use SEX, group0=1 and group1=2. The categorical prototype uses nine RAC1P groups (code minus one), with RAC1P still included as a feature. Client1 in its fixed 50-state population is Missouri.

Optional raw regeneration (not run during packaging; no data download needed for any regular command):

```sh
python -m pip install folktables==0.0.12
python raw_acs.py fetch --workspace /local/path/acs-rebuild --states MO
python raw_acs.py fetch --workspace /local/path/acs-rebuild
python serial.py -- python raw_acs.py rebuild --workspace /local/path/acs-rebuild
```

Acquisition is sequential and resumes/caches verified downloads. All 50 original archives total 571,621,503 bytes; expanded CSVs total 2,249,097,340 bytes. Rebuilding the pooled transform also needs several GB of RAM and scratch. Use local nonsynced storage. The optional wrapper runs the original transformation arithmetic and compares every rebuilt population's array bytes to this release. It records fresh provenance; it does not mint a new copy of the historical preparation gate. This path was inspected and its CLI checked, but was not downloaded or end-to-end rerun for this package.
