# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
python -m venv plotter-env
source plotter-env/bin/activate
pip install -r requirements.txt
```

## Running

```bash
# Run plotter directly
python plotter.py

# Run HTTP server (WIP)
uvicorn server:app --host 0.0.0.0 --port 5000
```

## Architecture

This is a plotting server for the Bantam Tools NextDraw (AxiDraw A3) on Raspberry Pi 5. The hardware has two independent serial connections to the EBB control board:

1. **NextDraw Python library** — high-level API for SVG plotting (`nextdraw` package, `interactive()` + `plot_setup()` / `plot_run()`)
2. **Direct EBB serial via `pyserial`** — for raw `S2` commands that control the SG90 tool servo on pin 4 (pen/brush changer)

**Critical constraint:** Both connections talk to `/dev/ttyACM*`. They cannot be open simultaneously. Before plotting, close the raw serial (`_close_ebb()`); after plotting, reclaim it (`_open_ebb()`) and reset EBB state with `CU,10,0` and `SC,8,8` before issuing further `S2` commands.

### Key hardware pins
- Pin 3 — NextDraw brushless pen lift (controlled via `pen_pos_up` / `pen_pos_down` options)
- Pin 4 — SG90 tool servo (brush/pen changer, controlled via `S2` EBB commands)

### Key servo positions (plottertest-2.py constants)
| Constant | Value | Meaning |
|---|---|---|
| `PEN_UP` / `PEN_DOWN` | 100 / 40 | Pen lift % travel |
| `PEN_BRUSH_A` | 16000 | SG90 ~97° |
| `PEN_BRUSH_B` | 19200 | SG90 ~113° |
| `PEN_IDLE` | 17500 | SG90 ~104° neutral |

### File structure
- `plotter.py` — canonical `Plotter` class; accepts optional `log_fn` (defaults to `print`) so the server can capture output
- `server.py` — FastAPI server; runs plot jobs in a background thread; endpoints: `POST /upload`, `POST /plot`, `GET /status`
- `static/index.html` — minimal web UI; two SVG slots (A required, B optional); polls `/status` at 800ms
- `plottertest-2.py` — standalone quick-test script (Plotter class inline, no imports); run directly on the Pi
- `plottertest.py` — earlier prototype, NextDraw only (no tool servo)
- `servo.py` — raw EBB serial diagnostic
- `uploads/` — uploaded SVGs stored here by the server (uuid-named)
- `demo/` — sample SVGs

### Simulation mode
When no plotter is connected, `_connect_plotter()` returns `False` and plot/move calls are skipped silently. Serial calls (`_open_ebb`) print a warning but do not crash.
