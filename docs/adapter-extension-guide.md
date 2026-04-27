# Adapter Extension Guide

Model adapters can be registered through the public registry seam.

## Register a model adapter

Implement the adapter contract and register it:

```python
from model_failure_lab.adapters import register_model

register_model("my-adapter", MyAdapterClass)
```

Then run:

```bash
failure-lab run --dataset reasoning-failures-v1 --model my-adapter:my-model
```

## Register a classifier

Implement a classifier callable and register it:

```python
from model_failure_lab.classifiers import register_classifier

register_classifier("my-classifier", my_classifier)
```

Then run:

```bash
failure-lab run --dataset reasoning-failures-v1 --model demo --classifier my-classifier
```
