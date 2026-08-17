# UIAutomator 3.0

Next-generation Android automation framework focused on precision UI inspection, robust
element identification, and reliable mobile automation.

Status: **Phase 1 (architecture)** — see [docs/UIAUTOMATOR3_ARCHITECTURE.md](docs/UIAUTOMATOR3_ARCHITECTURE.md)
for the full design and phase plan, and [docs/UIAUTOMATOR2_ANALYSIS.md](docs/UIAUTOMATOR2_ANALYSIS.md)
for the analysis of the predecessor project this design responds to.

## Phase 1 scope

Device discovery, connection, and health checks only — no hierarchy dumping, selectors,
gestures, or screenshots yet.

```python
import uiautomator3 as u3

d = u3.connect()          # connect to the first attached/authorized device
print(d.health())

for dev in u3.devices():  # enumerate all attached devices
    print(dev.serial)
```

```bash
u3 devices
u3 doctor
u3 version
```

## Development

```bash
pip install -e .
pytest
```
