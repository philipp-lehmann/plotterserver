import os
from nextdraw import NextDraw  # capital N, capital D

class Plotter:
    def __init__(self):
        print("Starting Plotter Demo ...")
        self.ad = NextDraw()  # matches the import
        self.ad.interactive()
        self.plotter_found = self.connect_to_plotter()

    def connect_to_plotter(self):
        # Set options BEFORE connect()
        self.ad.options.model = 2
        self.ad.options.speed_pendown = 100
        # self.ad.options.auto_rotate = True  # not available in NextDraw API

        if self.ad.connect():
            print(f"Nextdraw connected. Model: {self.ad.options.model}")
            return True
        else:
            print("Nextdraw not found. Entering simulation mode.")
            return False

    def return_home(self):
        if self.plotter_found:
            print("Plotter: Returning home.")
            self.ad.moveto(0, 0)
        else:
            print("Simulation Mode: Returning home.")

    def plot_image(self, svg_path):
        svg_path = os.path.abspath(svg_path)
        if os.path.exists(svg_path):
            if self.plotter_found:
                print(f"Plotter: Plotting image from {svg_path}.")
                self.ad.plot_setup(svg_path)
                self.ad.plot_run()
                print("Plotting complete.")
            else:
                print("Simulation Mode: Plotting (simulation).")
        else:
            print("SVG file not found.")

    def close_connection(self):
        if self.plotter_found:
            print("Closing connection to Nextdraw.")
            self.ad.disconnect()

if __name__ == "__main__":
    plotter = Plotter()
    plotter.plot_image("demo.svg")
    plotter.return_home()
    plotter.close_connection()