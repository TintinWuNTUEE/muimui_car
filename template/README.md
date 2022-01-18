# Remote Control Simulation

## Prerequisites
```
$ pip3 install -r requirements.txt
```

## How to run simulation code
- **1. Simulate jetson nano car first (in network A)**
```python
$ python3 jetson.py
```
- **2. Simulate browser (in network B)**
```python
$ python3 browser.py
```

- if multiprocessing shows error, try
```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

