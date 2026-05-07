import os
import serial
import time
from nextdraw import NextDraw

PEN_SERVO_PIN = 3
TOOL_SERVO_PIN = 4
SERVO_SPEED = 500

PEN_UP = 100
PEN_DOWN = 40
PEN_BRUSH_A = 16000
PEN_BRUSH_B = 19200
PEN_IDLE = 17500


class Plotter:
    def __init__(self, log_fn=print):
        self._log = log_fn
        self.ad = NextDraw()
        self.ad.interactive()
        self.plotter_found = self._connect_plotter()
        self.ebb = None

    def _connect_plotter(self):
        self.ad.options.model = 2
        self.ad.options.pen_pos_up = PEN_UP
        self.ad.options.pen_pos_down = PEN_DOWN
        self.ad.options.speed_pendown = 100
        if self.ad.connect():
            self._log(f"NextDraw connected. Model: {self.ad.options.model}")
            return True
        self._log("NextDraw not found. Simulation mode.")
        return False

    # --- EBB serial ---

    def _open_ebb(self):
        if self.ebb:
            return
        for i in range(4):
            try:
                self.ebb = serial.Serial(f"/dev/ttyACM{i}", 115200, timeout=1)
                time.sleep(0.3)
                return
            except serial.SerialException:
                continue
        self._log("EBB serial not found.")

    def _close_ebb(self):
        if self.ebb:
            self.ebb.close()
            self.ebb = None

    def _send(self, cmd):
        if not self.ebb:
            return
        self.ebb.write(f"{cmd}\r".encode())
        time.sleep(0.1)
        response = self.ebb.read_all().decode(errors="ignore").strip()
        if response and response != "OK":
            self._log(f"EBB: {cmd!r} → {response!r}")

    # --- tool head ---

    def swap_pen(self, pen="A"):
        positions = {"A": PEN_BRUSH_A, "B": PEN_BRUSH_B, "C": PEN_IDLE}
        self._open_ebb()
        self._send(f"S2,0,{TOOL_SERVO_PIN}")
        self._send(f"S2,{positions[pen.upper()]},{TOOL_SERVO_PIN},{SERVO_SPEED}")
        time.sleep(0.8)
        self._log(f"Tool → pen {pen.upper()}")

    # --- plotting ---

    def plot_image(self, svg_path):
        svg_path = os.path.abspath(svg_path)
        if not os.path.exists(svg_path):
            self._log(f"SVG not found: {svg_path}")
            return
        if not self.plotter_found:
            self._log("Simulation mode: skipping plot.")
            return

        self._close_ebb()
        self.ad.interactive()
        self.ad.connect()
        self.ad.plot_setup(svg_path)
        self.ad.options.mode = "plot"
        self._log(f"Plotting {os.path.basename(svg_path)} ...")
        self.ad.plot_run()
        self.ad.disconnect()
        time.sleep(0.5)

        self._open_ebb()
        self._send("CU,10,0")
        self._send("SC,8,8")
        self._send(f"S2,0,{TOOL_SERVO_PIN}")
        self._log("Plot complete.")

    def return_home(self):
        if not self.plotter_found:
            return
        self._close_ebb()
        self.ad.interactive()
        if self.ad.connect():
            self._log("Returning home.")
            self.ad.moveto(0, 0)
            self.ad.disconnect()

    def close(self):
        if self.plotter_found:
            self.ad.disconnect()
        self._close_ebb()
        self._log("Closed.")
