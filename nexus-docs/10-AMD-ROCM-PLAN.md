# AMD ROCm Integration Plan

## 1. Why AMD matters to NEXUS

AMD should be part of the technical architecture, not merely branding.

NEXUS has workloads that can benefit from accelerator compute:

-   LLM inference
-   embeddings
-   large-scale scenario simulation
-   forecasting
-   model evaluation

AMD ROCm provides the GPU software stack for AMD hardware and supports
major AI frameworks and inference tools.

AMD Developer Cloud provides access to AMD Instinct GPUs, including
MI300X-based environments.

## 2. Important rule

Do not start development on the GPU.

First make the CPU implementation correct and measurable.

Then move one workload to AMD.

## 3. Recommended progression

``` text
CPU implementation
      ↓
Correctness tests
      ↓
CPU benchmark
      ↓
Vectorization / batching
      ↓
ROCm environment
      ↓
AMD GPU implementation
      ↓
GPU benchmark
      ↓
Optimization
```

## 4. Candidate workload: simulation

A simple simulation:

``` python
for scenario in scenarios:
    demand = simulate_demand(...)
    inventory = simulate_inventory(...)
    profit = calculate_profit(...)
```

can eventually become a vectorized workload.

Conceptually:

``` text
CPU
scenario 1
scenario 2
scenario 3
...

AMD GPU
[scenario 1 ... scenario N]
        parallel
```

The exact implementation should be benchmark-driven.

## 5. Candidate workload: LLM inference

Potential stack:

``` text
NEXUS
  ↓
Open-source model
  ↓
vLLM
  ↓
ROCm
  ↓
AMD Instinct GPU
```

Use this only after understanding the model-serving architecture.

## 6. Benchmarking

Record:

``` text
workload
dataset size
scenario count
model
batch size
hardware
software versions
runtime
throughput
memory usage
```

Never report a speedup without the baseline.

## 7. Version discipline

Record exact:

-   ROCm version
-   GPU model
-   PyTorch version
-   vLLM version
-   Python version
-   OS
-   container image

AMD's ROCm documentation and compatibility matrix are the source of
truth for supported combinations.

## 8. Learning topics

Learn:

-   CPU vs GPU
-   parallelism
-   vectorization
-   GPU memory
-   kernels
-   batching
-   mixed precision
-   profiling
-   ROCm
-   PyTorch on ROCm
-   vLLM
-   containerized GPU workloads
