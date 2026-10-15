# Prepare the Week 2 environment before class

Use Python 3.11 to 3.13 and a dedicated Week 2 environment. Do not install packages
into the Week 1 environment. Week 2 runs locally and needs no model API key.

For a new CPU-only environment, Mentor Liu can run tutor.py setup --week week02
--workspace YOUR_STUDENT_FOLDER --install cpu. This creates the Week 2 .venv,
installs requirements-cpu.txt and verifies actual imports, data and starter tests.
The first download may take several minutes; finish it before the 100-minute core.

For a prepared laboratory CUDA environment, ask Mentor Liu to verify its exact
Python interpreter with setup --python ABSOLUTE_PYTHON_PATH. Use the PyTorch
2.10 installation instructions for the lab's platform and NVIDIA driver. Do not
install CPU wheels over an already working CUDA environment. If an environment
already exists, inspect and repair it instead of recreating it automatically.

```text
python preflight.py
python -m pytest -q tests/test_model.py -o pythonpath=. -k "vocabulary or data_disjoint or config"
```

These three starter tests can pass before model.py's four TODOs are completed.
Full model tests should initially fail on the unfinished forward methods.
CUDA unavailable means a real GPU comparison remains pending, not an invitation
to invent a result. Apple MPS is not the CUDA branch of this experiment.

Reference installation page: https://pytorch.org/get-started/previous-versions/
