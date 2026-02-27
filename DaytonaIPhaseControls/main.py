import sys
from PyQt5.QtWidgets import QApplication
from ics_client.client import ICS_Client
from gui.daytona_gui import DaytonaGUI

#Daytona I-Phase Controls
#Developed by Mikey Slem (aka Mikey Pancakes, aka Dirty Mike, aka Michael Slemko)
#2026

def main():
    app = QApplication([])
    gui = DaytonaGUI()
    gui.show()
    app.exec_()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()