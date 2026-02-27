from PyQt5 import QtWidgets, uic
import os

class ttPopup(QtWidgets.QWidget):
    def __init__(self, tt_dict, parent=None):
        super(ttPopup, self).__init__(parent) 
        ui_path = os.path.join(os.path.dirname(__file__), 'tt_popup.ui')     
        uic.loadUi(ui_path, self)
        self.setWindowTitle("Timing Table Output")
        self.tt_data = tt_dict
        self.table_headers = ["Line", "Opcode", "Ticks", "Address", "Value"]

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
                line_item = QtWidgets.QTableWidgetItem(str(row_index))
                table_widget.setItem(row_position, 0, line_item)
                for column_index, cell_value in enumerate(row_data.values()):
                    item = QtWidgets.QTableWidgetItem(str(cell_value))
                    table_widget.setItem(row_position, column_index + 1, item)