import os
import csv
import json
from urllib import response
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication, QTableWidgetItem, QFileDialog, QWidget
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from gui.tt_popup import ttPopup
from ics_client.client import ICS_Client
from workers.request_worker import RequestWorker
from tt_engine.tt_builder import Daytona_HDC_tt, Daytona_SinglePath_tt
from scripts.fpga_map import SC, TW

class DaytonaGUI(QtWidgets.QMainWindow):

    def __init__(self):
        super(DaytonaGUI, self).__init__()
        ui_path = os.path.join(os.path.dirname(__file__), 'gui.ui')
        uic.loadUi(ui_path, self)

        version = "v0.5"
        title = "Daytona I-Phase Controls (PreRelease)"
        self.menuVersion.setTitle(version)
        self.setWindowTitle(title)

        #Path options
        self.HDC_paths = ["Both", "Path A", "Path B"]
        self.JH_paths = ["Passthrough", "Around", "Alternating"]
        self.ICD_options = ["Default", "Jughandle"]
        self.paramter_tbl_headers = ["Canonical Name", "Board ID", "Parameter", "Setpoint"]
        self.readback_tbl_headers = ['Parameter Name', 'Board ID', 'Parameter', 'Readback']
        self.pathComboBox.addItems(self.HDC_paths)
        self.JHpathComboBox.addItems(self.JH_paths)
        self.ICDComboBox.addItems(self.ICD_options)
        self.column_combo_box.addItems(self.paramter_tbl_headers)

        self.twr_tables = [self.pathA_tbl, self.pathB_tbl]

        self.updateGUI_with_intent(os.path.join(os.path.dirname(__file__), "config", "default_daytona_intent.json"))

        #Wire up buttons to functions
        self.connect_btn.clicked.connect(self.connect_to_ICS)
        self.getreadbacks_btn.clicked.connect(lambda: self.get_readbacks(self.get_ics_channels(self.parameter_table), table_widget=self.parameter_table))
        self.method_combo_box.currentTextChanged.connect(self.on_method_dropdown_change)
        self.intent_combo_box.currentTextChanged.connect(self.on_intent_dropdown_change)
        self.putsetpoints_btn.clicked.connect(lambda: self.post_setpoints(self.get_ics_channels(self.parameter_table)))
        self.upload_method_btn.clicked.connect(lambda: self.load_csv_file(self.parameter_table, self.paramter_tbl_headers[:-1]))
        self.upload_readbacks_btn.clicked.connect(lambda: self.load_csv_file(self.params_table, self.readback_tbl_headers[:-1]))
        self.generateTT_btn.clicked.connect(self.generate_tt)
        self.addRow_TWRA_btn.clicked.connect(lambda: self.add_remove_row(self.pathA_tbl, add = True))
        self.addRow_TWRB_btn.clicked.connect(lambda: self.add_remove_row(self.pathB_tbl, add = True))
        self.removeRow_TWRA_btn.clicked.connect(lambda: self.add_remove_row(self.pathA_tbl))
        self.removeRow_TWRB_btn.clicked.connect(lambda: self.add_remove_row(self.pathB_tbl))
        self.add_row_btn.clicked.connect(self.add_plotter_tbl_row)
        self.remove_row_btn.clicked.connect(self.rmv_plotter_tbl_row)
        self.begin_plot_btn.clicked.connect(self.start_polling)
        self.save_method_btn.clicked.connect(self.save_csv_file)
        self.refreshMethods_btn.clicked.connect(self.find_methods)
        self.uploadIntent_btn.clicked.connect(self.load_json_file)
        self.saveIntent_btn.clicked.connect(self.save_json_file)
        self.refreshIntents_btn.clicked.connect(self.find_intents)
        self.stop_plot_btn.clicked.connect(self.stop_plotting)
        self.export_data_btn.clicked.connect(self.export_plot_data)
        self.clear_plot_btn.clicked.connect(self.clear_plot)

        self.input_filter_text.textChanged.connect(self.filter_parameter_table)
        self.column_combo_box.currentIndexChanged.connect(self.filter_parameter_table)
        self.applyFilterBox.toggled.connect(
            lambda checked: self.input_filter_text.clear() if not checked else None
        )

        self.twr_headers = ['Time (ms)', 'Frequency (Hz)', 'Amplitude (V)']
        
        self.pathA_tbl.setHorizontalHeaderLabels(self.twr_headers)
        self.pathB_tbl.setHorizontalHeaderLabels(self.twr_headers)
        self.params_table.setHorizontalHeaderLabels(self.readback_tbl_headers)

        self.plotting_widget.setBackground('w')
        self.plotting_widget.clear()
        self.plotting_widget.addLegend()
        self.curve = self.plotting_widget.plot(pen=pg.mkPen(color='b', width=2))
        self.readback_data_series = [] 
        self.max_points = 500000 
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_readbacks)

        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

        self.find_methods()
        self.find_intents()
        self.update_method_table(os.path.join(os.path.dirname(__file__), "methods", "init", "init_method_daytona.csv"))

    def add_plotter_tbl_row(self):
        row_position = self.params_table.rowCount()
        self.params_table.insertRow(row_position)

    def rmv_plotter_tbl_row(self):
        current_row = self.params_table.currentRow()
        if current_row >= 0:
            self.params_table.removeRow(current_row)

    def start_polling(self):
        interval_str = self.interval_input.text().strip()
        try:
            interval = int(interval_str)
            if interval <= 0:
                raise ValueError
        except ValueError:
            self.show_error_popup("Invalid interval. Enter a positive number.")
            return

        self.update_readbacks() 
        self.timer.start(interval * 1000) 

    def show_error_popup(self, error_code):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Token Retrieval Failed")
        msg.setText(f"Failed to get token.\nError code: {error_code}")
        msg.exec_()

    def update_readbacks(self):

        self.get_readbacks(self.get_ics_channels(self.params_table), self.params_table)

        table_data = self.get_table_data()

        if len(self.readback_data_series) != len(table_data):
            self.plotting_widget.clear()
            self.plotting_widget.addLegend()
            self.readback_data_series = [[] for _ in table_data]
            self.curves = []
            for i, row in enumerate(table_data):
                param_name = row[0]
                color = pg.intColor(i)
                pen = pg.mkPen(color=color, width=2)
                curve = self.plotting_widget.plot(pen=pen, name=param_name)
                self.curves.append(curve)

    def update_plot(self, list_of_readbacks):
        for i, readback in enumerate(list_of_readbacks):
            series = self.readback_data_series[i]
            series.append(float(readback))
            if len(series) > self.max_points:
                series.pop(0)
            self.curves[i].setData(series)

    def stop_plotting(self):
        self.timer.stop()
        self.status_label.setText("Plotting Stopped")
        self.status_label.setStyleSheet("color: black; font-weight: bold;")

    def clear_plot(self):
        self.plotting_widget.clear()
        self.curves = []
        self.readback_data_series = []

    def export_plot_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Data as CSV", "", "CSV Files (*.csv);;All Files (*)")
        
        if not file_path:
            return

        if not file_path.endswith('.csv'):
            file_path += '.csv'

        try:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                header = ['Index'] + [self.curves[i].name() for i in range(len(self.readback_data_series))]
                writer.writerow(header)

                max_length = max(len(series) for series in self.readback_data_series)
                for i in range(max_length):
                    row = [i]
                    for series in self.readback_data_series:
                        row.append(series[i] if i < len(series) else '')
                    writer.writerow(row)

            print(f"Data exported successfully to {file_path}")

        except Exception as e:
            print(f"Failed to write {file_path}: {e}")

    def get_table_data(self):
        table_data = []
        row_count = self.params_table.rowCount()
        col_count = self.params_table.columnCount()

        for row in range(row_count):
            row_data = []
            for col in range(col_count - 1): 
                item = self.params_table.item(row, col)
                row_data.append(item.text() if item else "")
            table_data.append(row_data)

        return table_data

    def connect_to_ICS(self):
        '''
        Connect to ICS and retrieve the version information to confirm connection.
        Uses the address input from the GUI to establish connection. Updates the status label based on connection success or failure.
        '''
        # Connecting to ICS
        self.hostAddress = self.address_input.text()
        print(f"Connecting to ICS at {self.hostAddress}...")
        #Get the version of the electronics to confirm connection
        try:
            self.ics_client = ICS_Client(base_url=self.hostAddress)
            response = self.ics_client.send_request('/api/ics/instrument/initialization/', 
                                                    method='GET',
                                                    port=8001)
            if response:
                print("Connected to ICS successfully!")
                print(f"ICS Status: {response}")
                self.status_label.setText("Connected")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                print("Failed to connect to ICS.")
        except Exception as e:
            print(f"Error connecting to ICS: {e}")

    def find_methods(self):
        '''
        Scan the "methods" directory for available method CSV files and populate the method dropdown.
        Looks for CSV files in the "methods" directory and adds their names (without extension) to the dropdown menu.
        '''
        current_item = self.method_combo_box.currentText()
        methods_dir = os.path.join(os.path.dirname(__file__), "methods")
        method_files = [f for f in os.listdir(methods_dir) if f.endswith('.csv')]
        method_names = [os.path.splitext(f)[0] for f in method_files]
        dropdown_index = method_names.index(current_item) if current_item in method_names else -1

        self.method_combo_box.clear()
        self.method_combo_box.addItems(method_names)
        self.method_combo_box.setCurrentIndex(dropdown_index)

    def find_intents(self):

        current_item = self.intent_combo_box.currentText()
        intents_dir = os.path.join(os.path.dirname(__file__), "intents")
        intent_files = [f for f in os.listdir(intents_dir) if f.endswith('.json')]
        intents = [os.path.splitext(f)[0] for f in intent_files]
        dropdown_index = intents.index(current_item) if current_item in intents else -1

        self.intent_combo_box.clear()
        self.intent_combo_box.addItems(intents)
        self.intent_combo_box.setCurrentIndex(dropdown_index)
        
    def on_method_dropdown_change(self, method_name):
        '''
        Handle changes in the method dropdown selection.
        When a new method is selected, this function updates the parameter table with the corresponding CSV file for that method.
        '''
        if method_name:
            csv_file_path = os.path.join(os.path.dirname(__file__), "methods", f"{method_name}.csv")
            self.update_method_table(csv_file_path)

    def on_intent_dropdown_change(self, intent_name):
        '''
        Handle changes in the method dropdown selection.
        When a new method is selected, this function updates the parameter table with the corresponding CSV file for that method.
        '''
        if intent_name:
            json_path = os.path.join(os.path.dirname(__file__), "intents", f"{intent_name}.json")
            self.updateGUI_with_intent(json_path)

    def update_method_table(self, csv_file_path):
        '''
        Update the parameter table in the GUI with the provided parameters.
        Clears existing entries and populates the table with new parameter data.
        Adds an extra "Readback" column at the end.
        '''
        self.parameter_table.setRowCount(0)  # Clear existing rows

        with open(csv_file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # First row = column headers

            # Step 1: Add extra header for readbacks
            headers.append("Readback")

            # Step 2: Set column count and headers
            self.parameter_table.setColumnCount(len(headers))
            self.parameter_table.setHorizontalHeaderLabels(headers)

            # Step 3: Populate the table
            for row_data in reader:
                row_position = self.parameter_table.rowCount()
                self.parameter_table.insertRow(row_position)

                for column, cell_value in enumerate(row_data):
                    item = QtWidgets.QTableWidgetItem(cell_value)
                    self.parameter_table.setItem(row_position, column, item)

                # Step 4: Add empty QTableWidgetItem for the Readback column
                readback_column_index = len(headers) - 1
                self.parameter_table.setItem(
                    row_position,
                    readback_column_index,
                    QtWidgets.QTableWidgetItem("")  # Empty initially
                )

    def get_ics_channels(self, table_widget):
        '''
        Extract canonical names from the parameter table and return them as a list.
        Iterates through the rows of the table and collects the canonical names from the board_id, parameter, and setpoint columns.
        '''
        channel_result = []

        for row in range(table_widget.rowCount()):
            board_id_item = table_widget.item(row, 1)  # Second column = board_id
            parameter_item = table_widget.item(row, 2)  # Third column = parameter
            setpoint_item = table_widget.item(row, 3)  # Fourth column = setpoint value

            if board_id_item and parameter_item:  # Need both to form canonical name
                board_id_text = board_id_item.text() if board_id_item.text() else ''
                parameter_text = parameter_item.text() if parameter_item.text() else ''
                setpoint_text = setpoint_item.text() if setpoint_item else ''  # Safely handle None

                channel_array = (f"@{board_id_text}.{parameter_text}", setpoint_text)
                channel_result.append(channel_array)

        return channel_result
        
    def handle_readback_response(self, response, table_widget=None):

        if isinstance(response, Exception):
            print(f"Error retrieving readbacks: {response}")
            return None

        values = [item["value"] for item in response]

        if table_widget.rowCount() < len(values):
            table_widget.setRowCount(len(values))

        for row, value in enumerate(values):
            table_widget.setItem(row, 4 if table_widget == self.parameter_table else 3, QTableWidgetItem(str(value)))

        if table_widget == self.params_table:
            self.update_plot(values)
    
        return response

    def get_readbacks(self, data, table_widget):

        readback_list = []
        for paramter, setpoint in data:
            readback_list.append(paramter)

        # Keep the worker alive
        self.worker = RequestWorker(
            self.ics_client.send_request,
            'api/ics/channels/',
            8001,
            method='GET',
            data=";".join(readback_list)
        )

        self.worker.finished.connect(lambda response: self.handle_readback_response(response, table_widget))
        self.worker.finished.connect(self.worker.deleteLater)  # safely delete after done
        self.worker.start()
    
    def post_setpoints(self, data):

        payload = [{"canonical_name": canonical,"value": value} for canonical, value in data]
        
        # Keep the worker alive
        self.worker = RequestWorker(
            self.ics_client.send_request,
            'api/ics/channels/',
            8001,
            method='POST',
            data=payload
        )

        self.worker.finished.connect(lambda response: print(f"Setpoint post response: {response}"))
        self.worker.finished.connect(self.worker.deleteLater)  # safely delete after done
        self.worker.start()

    def load_csv_file(self, table, expected_columns):
        
        
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)",
            options=options
        )
        
        if not file_name:
            return

        try:
            with open(file_name, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                csv_columns = reader.fieldnames

                # Check if all expected columns are present
                if not all(col in csv_columns for col in expected_columns):
                    print(f"CSV must contain columns: {expected_columns}")
                    return

                table.setRowCount(0)  # Clear existing data

                for row_data in reader:
                    row_index = table.rowCount()
                    table.insertRow(row_index)

                    for col_index, col_name in enumerate(expected_columns):
                        value = row_data.get(col_name, "")
                        item = QTableWidgetItem(value)
                        table.setItem(row_index, col_index, item)

        except Exception as e:
            print(f"Error loading CSV: {e}")

    def save_csv_file(self):

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Table CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)",
            options=options
        )

        if not file_name:
            return

        with open(file_name, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Write header row
            headers = []
            for col in range(self.parameter_table.columnCount() - 1): #We dont want the readback column.
                header = self.parameter_table.horizontalHeaderItem(col)
                headers.append(header.text() if header else "")
            writer.writerow(headers)

            # Write table data
            for row in range(self.parameter_table.rowCount()):
                row_data = []
                for col in range(self.parameter_table.columnCount() - 1): #We dont want the readback column.
                    item = self.parameter_table.item(row, col)
                    row_data.append(item.text() if item else "")
                writer.writerow(row_data)

    def load_json_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open JSON File",
            "",
            "JSON Files (*.json);;All Files (*)",
            options=options
        )
        
        if not file_name:
            return
        
        try:
            self.updateGUI_with_intent(file_name)

        except Exception as e:
            print(f"Error loading JSON intent: {e}")

    def save_json_file(self):

        
        dict_list =[]

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Intent",
            "",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        for table in self.twr_tables:
            if not self.is_twr_table_empty(table):
                tbl_dict = self.get_twrs_from_tables(table) if table == self.pathA_tbl else self.get_twrs_from_tables(table, pathA=False)
                dict_list.append(tbl_dict)

        intent = self.build_intent(dict_list)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(intent, f, indent=4)

    def updateGUI_with_intent(self, intent):
        '''
        Update the GUI with the provided intent data.
        This function can be expanded to update various parts of the GUI based on the intent structure.
        '''
        try:
            with open(intent, 'r') as f:
                intent_data = json.load(f)

            self.input_sip_period.setText(str(intent_data["sipPeriod"]))
            self.input_stall_time.setText(str(intent_data["stallDuration"]))
            self.input_fill_time.setText(str(intent_data["fill"]))
            self.input_release_time.setText(str(intent_data["release"]))
            self.input_trap_time.setText(str(intent_data["trap"]))
            self.input_flush_voltage.setText(str(intent_data["flushVoltage"]))
            self.input_flush_time.setText(str(intent_data["flushDuration"]))
            self.input_fill_params_amp.setText(str(intent_data["fillAmp"]))
            self.input_fill_params_freq.setText(str(intent_data["fillFrequency"]))
            self.input_trap_params_amp.setText(str(intent_data["trapAmp"]))
            self.input_trap_params_freq.setText(str(intent_data["trapFrequency"]))
            self.input_release_params_amp.setText(str(intent_data["releaseAmp"]))
            self.input_release_params_freq.setText(str(intent_data["releaseFrequency"]))
            self.pathComboBox.setCurrentIndex(self.HDC_paths.index(intent_data["HDCpath"])) if intent_data["HDCpath"] in self.HDC_paths else 0
            self.JHpathComboBox.setCurrentIndex(self.JH_paths.index(intent_data["JHpath"])) if intent_data["JHpath"] in self.JH_paths else 0   
            self.update_twr_gui_tables(intent_data)
            #print(intent_data["pathA_traveling_wave_profile"])     
        except Exception as e:
            print(f"Error loading intent file: {e}")

    def build_intent(self, twr_list):
        '''
        Build an intent dictionary from the current GUI input values.
        This function gathers all relevant parameters from the GUI and constructs a dictionary that represents the intent for the experiment.
        '''
        intent = {
            "sipPeriod": float(self.input_sip_period.text()),
            "stallDuration": float(self.input_stall_time.text()),
            "fill": float(self.input_fill_time.text()),
            "release": float(self.input_release_time.text()),
            "trap": float(self.input_trap_time.text()),
            "flushDuration": float(self.input_flush_time.text()),
            "flushVoltage": float(self.input_flush_voltage.text()),
            "fillAmp": float(self.input_fill_params_amp.text()),
            "fillFrequency": float(self.input_fill_params_freq.text()),
            "trapAmp": float(self.input_trap_params_amp.text()),
            "trapFrequency": float(self.input_trap_params_freq.text()),
            "releaseAmp": float(self.input_release_params_amp.text()),
            "releaseFrequency": float(self.input_release_params_freq.text()),
            "HDCpath": self.pathComboBox.currentText(),
            "JHpath": self.JHpathComboBox.currentText()
            }
        
        for twr in twr_list:
            key = list(twr.keys())[0]
            intent[key] = twr[key]

        return intent
    
    def generate_tt(self):
        twr_dictionarys_list = []
        for table in self.twr_tables:
            if not self.is_twr_table_empty(table):
                twr_dictionarys_list.append(self.get_twrs_from_tables(self.pathA_tbl))
        intent = self.build_intent(twr_dictionarys_list)
        tt = Daytona_HDC_tt(intent=intent) if intent['HDCpath'] == 'Both' else Daytona_SinglePath_tt(intent=intent)
        tt_dictionary = tt.get_tts()
        tt_dict = {}
        for module in list(tt_dictionary.keys()):
            step_info = []
            last_time = 0.0
            for item in tt_dictionary[module]:
                step_info.append({
                    "opcode": item.opcode.value,
                    "ticks": int(round((round(float(item.abs_time_ms), 1) - last_time) * 10.0)), #to clock ticks
                    "address": int(item.canonical_name) if item.opcode.value == "C0" else self.parameter_mapping(item.canonical_name),
                    "setpoint": item.setpoint
                })
                last_time = float(item.abs_time_ms)
            tt_dict[module] = step_info
        self.create_popup(tt_dict)
    
    def create_popup(self, tt_dict):
        self.popup = ttPopup(tt_dict)
        self.popup.show()
    
    def fpga_register_lookup(self, board_id, parameter):
        if board_id == 0:
            fpga_address = format(SC[int(parameter)], 'x').upper()
            return fpga_address
        elif board_id == 4 or board_id == 5 or board_id == 6:
            fpga_address = format(TW[int(parameter)], 'x').upper()
            return fpga_address
        else:
            print(f"No FPGA address found for Board ID {board_id} and Parameter {parameter}")
            return None

    def parameter_mapping(self, canonical_name):
        with open(os.path.join(os.path.dirname(__file__), "config", "daytona_canonical_names.csv"), newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Canonical Name'] == canonical_name:
                    board_id = int(row['Board ID'])
                    parameter = row['Parameter']
                    fpga_address = self.fpga_register_lookup(board_id, parameter)
                    return fpga_address
                elif "0x" in canonical_name:
                    return format(int(canonical_name, 16), 'x').upper()
        # Not found → return None or default values
        return None, None

    def update_twr_gui_tables(self, data_dict):
        twr_keys = ['pathA_traveling_wave_profile', 'pathB_traveling_wave_profile']
        self.pathA_tbl.clearContents()
        self.pathB_tbl.clearContents()
        for key in twr_keys:
            table = self.pathA_tbl if key == 'pathA_traveling_wave_profile' else self.pathB_tbl
            if key in data_dict:
                ramps = data_dict[key]['ramps']
                if len(ramps) > 0:          
                    table.setRowCount(len(ramps) + 1)  # +1 for initial state
                    initial_state = data_dict[key]['initial_state']
                    table.setItem(0, 0, QTableWidgetItem(str(0)))
                    table.setItem(0, 1, QTableWidgetItem(str(initial_state['frequency'])))
                    table.setItem(0, 2, QTableWidgetItem(str(initial_state['amplitude'])))
                for i, ramp in enumerate(ramps):
                    time = ramp['time']
                    frequency = ramp['state']['frequency']
                    amplitude = ramp['state']['amplitude']
                    table.setItem(i+1, 0, QTableWidgetItem(str(time)))
                    table.setItem(i+1, 1, QTableWidgetItem(str(frequency)))
                    table.setItem(i+1, 2, QTableWidgetItem(str(amplitude)))

    def add_remove_row(self, twr_table, add = False):
        if add:
            row = twr_table.rowCount()
            twr_table.insertRow(row)
            for col in range(twr_table.columnCount()):
                twr_table.setItem(row, col, QTableWidgetItem(""))
        else:
            row = twr_table.currentRow()
            if row >= 0:
                twr_table.removeRow(row)

    def get_twrs_from_tables(self, table_input, pathA=True):
            
            path_key = "pathA_traveling_wave_profile" if pathA else "pathB_traveling_wave_profile"

            def get_cell(row, col):
                item = table_input.item(row, col)
                return float(item.text()) if item and item.text() not in ("", "initial") else None

            # Row 0 = initial state
            initial_state = {
                "frequency": get_cell(0, 1),
                "amplitude": get_cell(0, 2)
            }

            # Remaining rows = ramps
            ramps = []
            for row in range(1, table_input.rowCount()):
                ramps.append({
                    "time": get_cell(row, 0),
                    "state": {
                        "frequency": get_cell(row, 1),
                        "amplitude": get_cell(row, 2)
                    }
                })

            return {
                path_key: {
                    "initial_state": initial_state,
                    "ramps": ramps
                }
            } 

    def is_twr_table_empty(self, table_input):
        for row in range(table_input.rowCount()):
            for col in range(table_input.columnCount()):
                item = table_input.item(row, col)
                if item and item.text().strip():
                    return False
        return True

    def filter_parameter_table(self):
        if self.applyFilterBox.isChecked():
            filter_text = self.input_filter_text.text().lower()
            filter_column_name = self.column_combo_box.currentText()

            # Get column index from header text
            column_index = None
            for col in range(self.parameter_table.columnCount()):
                header = self.parameter_table.horizontalHeaderItem(col)
                if header and header.text() == filter_column_name:
                    column_index = col
                    break

            if column_index is None:
                return

            for row in range(self.parameter_table.rowCount()):
                item = self.parameter_table.item(row, column_index)

                if item and filter_text in item.text().lower():
                    self.parameter_table.setRowHidden(row, False)
                else:
                    self.parameter_table.setRowHidden(row, True)

        else:
            # Show all rows if filter is disabled
            for row in range(self.parameter_table.rowCount()):
                self.parameter_table.setRowHidden(row, False)