import os
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from plotter import Plotter

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()

_lock = threading.Lock()
_job = {"status": "idle", "log": []}


def _log(line: str):
    print(line)
    with _lock:
        _job["log"].append(line)


def _run_plot(paths: list):
    with _lock:
        _job["status"] = "running"
        _job["log"] = []
    try:
        p = Plotter(log_fn=_log)
        pens = ["A", "B"]
        for i, path in enumerate(paths):
            p.swap_pen(pens[i] if i < len(pens) else "A")
            p.plot_image(path)
        p.swap_pen("C")
        p.return_home()
        p.close()
        with _lock:
            _job["status"] = "done"
    except Exception as exc:
        _log(f"Error: {exc}")
        with _lock:
            _job["status"] = "error"


class PlotRequest(BaseModel):
    files: list[str]


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    fname = uuid.uuid4().hex + Path(file.filename).suffix
    (UPLOAD_DIR / fname).write_bytes(await file.read())
    return {"filename": fname}


@app.post("/plot")
def plot(req: PlotRequest):
    with _lock:
        if _job["status"] == "running":
            return JSONResponse({"error": "already running"}, status_code=409)
    paths = [str(UPLOAD_DIR / f) for f in req.files]
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        return JSONResponse({"error": f"files not found: {missing}"}, status_code=400)
    threading.Thread(target=_run_plot, args=(paths,), daemon=True).start()
    return {"ok": True}


@app.get("/status")
def status():
    with _lock:
        return {"status": _job["status"], "log": list(_job["log"])}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
