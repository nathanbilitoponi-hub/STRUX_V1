Copia e incolla tutto questo dentro `RUN.md`:

````md
# How to run STRUX V1

From the STRUX_V1 root folder:

```bash
pip install -r requirements.txt
python benchmarks/test_strux_v1.py
````

Expected output:

* dataset generated
* STRUX LIFE runs
* large regions detected
* strong filament detected
* MST backbone extracted
* persistent cluster detected
* 3D figure displayed

Reference first pass:

```txt
LARGE REGIONS: 2
STRONG FILAMENTS: 1
MST EDGES: 1
PERSISTENT CLUSTERS: 1
PERSISTENT CORE: 1
```

Reference image:

```txt
exports/first_pass/strux_v1_first_pass.png
```

Project structure:

```txt
STRUX_V1/
│
├── core/
│   ├── backbone/
│   ├── connections/
│   ├── multiscale/
│   ├── persistence/
│   └── compare/
│
├── benchmarks/
│   └── test_strux_v1.py
│
├── exports/
│   └── first_pass/
│
├── requirements.txt
├── README.md
└── RUN.md
```

Core modules:

* multiscale_life.py
* connection_scoring.py
* backbone_mst.py
* persistence.py
* structure_compare.py

Current scope:

STRUX V1 is a minimal operational release focused on:

* multiscale clustering
* geometric filament scoring
* backbone extraction
* persistence estimation
* structural comparison

This release intentionally excludes:

* frontend
* login systems
* Stripe/payment systems
* business logic
* aggressive reconnect logic
* experimental VOID-first modules
* unvalidated theoretical layers

Purpose of this release:

Freeze a minimal reproducible operational STRUX pipeline before future theoretical and engineering expansion.

```
```
