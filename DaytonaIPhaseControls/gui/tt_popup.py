from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog
import os
import csv
import subprocess

class ttPopup(QtWidgets.QWidget):

    def __init__(self, tt_dict, parent=None):
        super(ttPopup, self).__init__(parent) 
        ui_path = os.path.join(os.path.dirname(__file__), 'tt_popup.ui')
        uic.loadUi(ui_path, self)
        self.setWindowTitle("Timing Table Output")
        self.tt_data = tt_dict
        self.table_headers = ["Opcode", "Ticks", "Address", "Value"]

        self.search_btn.clicked.connect(self.browse_to_path)
        self.generateOUT_btn.clicked.connect(self.write_tts_to_csv)

        self.table_dict = {
            "0": self.ctrl_timingtable,
            "4": self.pathA_timingtable,
            "5": self.pathB_timingtable,
            "6": self.pathC_timingtable
        }
        if self.tt_data is not None:
            self.parse_tt_data(self.tt_data)
    
    def parse_tt_data(self, tt_dict):
        # This function will parse the timing table data and populate the popup
        # For now, it just prints the data to the console
        for module, steps in tt_dict.items():
            self.update_gui_tables(module, steps)

    def update_gui_tables(self, board_id, data):
        table_widget = self.table_dict[board_id]
        table_widget.setHorizontalHeaderLabels(self.table_headers)
        if table_widget:
            table_widget.setRowCount(0) 
            for row_index, row_data in enumerate(data):
                row_position = table_widget.rowCount()
                table_widget.insertRow(row_position)
                #line_item = QtWidgets.QTableWidgetItem(str(row_index))
                #table_widget.setItem(row_position, 0, line_item)
                for column_index, cell_value in enumerate(row_data.values()):
                    item = QtWidgets.QTableWidgetItem(str(cell_value))
                    table_widget.setItem(row_position, column_index, item)

    def browse_to_path(self):
        pathname = QFileDialog.getExistingDirectory(self, "Open Directory")
        if pathname:
            self.filepath.setText(pathname)

    def write_tts_to_csv(self):
        current_path = self.filepath.text()
        if not current_path:
            print("No folder selected.")
            return

        tables = [self.ctrl_timingtable, self.pathA_timingtable, self.pathB_timingtable, self.pathC_timingtable]
        board_ids = ['0', '4', '5', '6']

        for i, table in enumerate(tables):
            if table is None:
                continue

            # Get the index of the "ticks" column
            ticks_col_index = -1
            for col in range(table.columnCount()):
                header_item = table.horizontalHeaderItem(col)
                if header_item and header_item.text().strip().lower() == "ticks":
                    ticks_col_index = col
                    break

            if ticks_col_index == -1:
                print(f"No 'ticks' column found in {table.objectName()}")
                continue

            tick_sum = 0
            for row in range(table.rowCount()):
                item = table.item(row, ticks_col_index)
                if item:
                    text = int(item.text())
                    tick_sum += int(text)

            # Export to CSV
            filename = f"{table.objectName()}.csv"
            file_path = f"{current_path}/{filename}"
            with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                for row in range(table.rowCount()):
                    row_data = [str(row)]  # Add row index at the start
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            bin_err = self.build_timing_tables(duration_ticks=tick_sum, board_id=board_ids[i], csv_file=file_path)

            if bin_err:
                print(f"Executable failed! Command: {bin_err.cmd}, Exit code: {bin_err.returncode}")

    def build_timing_tables(self, duration_ticks, board_id, csv_file):
        exe_path = os.path.join(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'convert_csv.exe'))

        try:
            subprocess.run([
                exe_path,
                "--duration_ticks", str(duration_ticks),
                "--board_id", str(board_id),
                "--csv_file", str(csv_file)
            ], check=True)  # check=True raises exception if the exe fails
        
        except subprocess.CalledProcessError as e:
            return e