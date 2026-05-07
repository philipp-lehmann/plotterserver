# plotterserver

A standalone plotting server for the Bantam Tools NextDraw (AxiDraw A3), running on Raspberry Pi 5. Inspired by [saxi](https://github.com/nornagon/saxi), built for a custom dual-servo tool head setup.

## Hardware

- Bantam Tools NextDraw (AxiDraw A3 rebrand)
- Raspberry Pi 5
- EBB control board (USB serial via `/dev/ttyACM*`)
- Pin 3 — NextDraw brushless pen lift
- Pin 4 — SG90 tool servo (brush/pen changer)

## Setup

```bash
git clone git@github.com:philipp-lehmann/plotterserver.git
cd plotterserver
python -m venv plotter-env
source plotter-env/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python plotter.py
```

Or run the server (WIP):

```bash
uvicorn server:app --host 0.0.0.0 --port 5000
```

## Configuration

Key constants in `plotter.py`:

| Constant | Default | Description |
|---|---|---|
| `PEN_UP` | 60 | Pen lift up position (% travel) |
| `PEN_DOWN` | 40 | Pen lift down position (% travel) |
| `PEN_BRUSH_A` | 16500 | Tool servo position for brush A |
| `PEN_BRUSH_B` | 19000 | Tool servo position for brush B |
| `PEN_IDLE` | 17500 | Tool servo idle/neutral position |

## Project Structure

```
plotterserver/
├── plotter.py        # Plotter class, EBB serial, servo control
├── server.py         # FastAPI HTTP server (WIP)
├── static/           # Web UI
├── uploads/          # Incoming SVGs
└── requirements.txt
```