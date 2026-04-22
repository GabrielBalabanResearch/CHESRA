# ============================================================
# CHESRA – Cardiac Hyperelastic Evolutionary Symbolic
#          Regression Algorithm
#
# Base image: Ubuntu 20.04 with FEniCS 2019.1 from official PPA
# ============================================================
FROM ubuntu:20.04

LABEL description="CHESRA reproduction environment" \
      fenics="2019.1.0"

ENV DEBIAN_FRONTEND=noninteractive

USER root

# ── System packages + FEniCS from official PPA ──────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        software-properties-common \
        curl \
        git \
        unzip \
    && add-apt-repository ppa:fenics-packages/fenics \
    && apt-get update && apt-get install -y --no-install-recommends \
        fenics \
        python3-pip \
        python3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Python dependencies (exact versions from paper) ─────────
RUN python3 -m pip install --no-cache-dir \
    "deap==1.3.3" \
    "func_timeout==4.3.5" \
    "lmfit==1.0.3" \
    "matplotlib==3.5.3" \
    "numpy==1.23.4" \
    "pandas==1.4.4" \
    "scipy==1.9.3" \
    "seaborn==0.13.2" \
    "sympy==1.10.1" \
    "PyYAML==6.0.2" \
    "pyDOE==0.3.8"

# ── Copy repository ──────────────────────────────────────────
WORKDIR /workspace
COPY . /workspace/

# ── Default command ──────────────────────────────────────────
# Launches an interactive shell; override at `docker run` time, e.g.:
#   docker run --rm chesra \
#     bash -c "cd Experiments/CHESRAFunctions && python run_experiment.py"
CMD ["bash"]