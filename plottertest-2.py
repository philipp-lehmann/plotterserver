import os
import serial
import time
from nextdraw import NextDraw

PEN_SERVO_PIN = 3      # NextDraw brushless pen lift
TOOL_SERVO_PIN = 4     # SG90 tool servo
SERVO_SPEED = 500

PEN_UP = 100            # % travel
PEN_DOWN = 40          # % travel
PEN_BRUSH_A = 16000    # SG90 position (~97°)
PEN_BRUSH_B = 19200    # SG90 position (~113°)
PEN_IDLE = 17500       # SG90 position (~104°)

DEMO_DIR = "demo"

class Plotter:
    def __init__(self):
        print("Starting Plotter Demo ...")
        self.ad = NextDraw()
        self.ad.interactive()
        self.plotter_found = self._connect_plotter()
        self.ebb = None  # opened on demand, closed during plots

    def _connect_plotter(self):
        self.ad.options.model = 2
        self.ad.options.pen_pos_up = PEN_UP
        self.ad.options.pen_pos_down = PEN_DOWN
        self.ad.options.speed_pendown = 100
        if self.ad.connect():
            print(f"NextDraw connected. Model: {self.ad.options.model}")
            return True
        print("NextDraw not found. Simulation mode.")
        return False

    # --- EBB serial (for direct S2 commands) ---

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
        print("EBB serial not found.")

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
            print(f"EBB: {cmd!r} → {response!r}")

    # --- tool head ---

    def set_tool_servo(self, position, rate=SERVO_SPEED):
        self._send(f"S2,{position},{TOOL_SERVO_PIN},{rate}")
        time.sleep(0.8)

    def swap_pen(self, pen="A"):
        positions = {"A": PEN_BRUSH_A, "B": PEN_BRUSH_B, "C": PEN_IDLE}
        self._open_ebb()
        self._send(f"S2,0,{TOOL_SERVO_PIN}")
        self.set_tool_servo(positions[pen.upper()])
        print(f"Tool → pen {pen.upper()}")

    # --- plotting ---

    def plot_image(self, svg_path):
        svg_path = os.path.abspath(svg_path)
        if not os.path.exists(svg_path):
            print(f"SVG not found: {svg_path}")
            return
        if not self.plotter_found:
            print("Simulation mode: skipping plot.")
            return

        self._close_ebb()  # release port to NextDraw
        self.ad.interactive()
        self.ad.connect()
        self.ad.plot_setup(svg_path)
        self.ad.options.mode = "plot"
        print(f"Plotting {svg_path}")
        self.ad.plot_run()
        self.ad.disconnect()
        time.sleep(0.5)

        # Reclaim port + reset state for tool servo
        self._open_ebb()
        self._send("CU,10,0")        # exit future syntax mode
        self._send("SC,8,8")         # restore default S2 channel count
        self._send(f"S2,0,{TOOL_SERVO_PIN}")  # release tool channel
        print("Plot complete.")

    def return_home(self):
        if self.plotter_found:
            self.ad.moveto(0, 0)

    def close(self):
        if self.plotter_found:
            self.ad.disconnect()
        self._close_ebb()
        print("Closed.")


if __name__ == "__main__":
    p = Plotter()
    p.swap_pen("A")
    p.plot_image(os.path.join(DEMO_DIR, "demo-1.svg"))
    p.swap_pen("B")
    p.plot_image(os.path.join(DEMO_DIR, "demo-2.svg"))
    p.swap_pen("C")
    p.return_home()
    p.close()