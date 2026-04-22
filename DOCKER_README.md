  # Running CHESRA with Docker

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 20.10
- (optional) [docker compose](https://docs.docker.com/compose/install/) v2

---

## File layout

The Docker files live in the repository root:

```
CHESRA/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── README.md
├── CHESRA/
└── Experiments/
├── CHESRAFunctions/
├── Tissue_Benchmark/
└── 3DSimulation_Benchmark/
```

---

## Build the image

```bash
# From the repository root (where Dockerfile lives)
docker build -t chesra .
```

This will:
1. Start from the official FEniCS 2019.1.0 image (provides `dolfin`).
2. `pip install` all remaining dependencies at the exact versions listed in the paper.

The first build takes ~10–15 minutes; subsequent builds are cached.

---

## Run experiments

### Interactive shell
```bash
docker run --rm -it chesra
```

### Experiment 1 – Create SEFs with CHESRA
```bash
docker run --rm chesra \
  bash -c "cd Experiments/CHESRAFunctions && python run_experiment.py && python create_figure.py"
```

### Experiment 2 – Tissue benchmark
```bash
docker run --rm chesra \
  bash -c "cd Experiments/Tissue_Benchmark && python run_experiment.py && python create_figure.py"
```

### Experiment 3 – 3D simulation benchmark

**Requires Git LFS data.** Clone the repo with LFS and mount the data folder at runtime:

```bash
git lfs pull   # run once after cloning to fetch the simulation data
```

```bash
docker run --rm -it \
  -v "$(pwd)/Experiments/3DSimulation_Benchmark:/workspace/Experiments/3DSimulation_Benchmark" \
  chesra \
  bash -c "cd Experiments/3DSimulation_Benchmark && \
           unzip -q 3Dsimulation_data.zip && \
           python run_experiment.py -energy_function chesra1 -scenario in_vivo_CMR"
```

---

## Using docker compose (optional)

```bash
# Build
docker compose build

# Interactive shell
docker compose run --rm chesra

# Run a one-off command
docker compose run --rm chesra \
  bash -c "cd Experiments/CHESRAFunctions && python run_experiment.py"
```

---

## Notes on `dolfin` / FEniCS

`dolfin 2019.2.0.dev0` is not on PyPI and cannot be installed with `pip`.
The Docker image solves this by using the official
`quay.io/fenicsproject/stable:2019.1.0` base image, which ships a pre-compiled
FEniCS 2019.1 stack (PETSc, dolfin, UFL, FFC, FIAT, dijitso) built against
Python 3.6. All pip dependencies are installed into the same Python 3.6
environment to ensure `dolfin` imports correctly.

To verify the environment is working:

```bash
docker run --rm chesra python -c "import dolfin; print(dolfin.__version__)"
```

Expected output: `2019.1.0`