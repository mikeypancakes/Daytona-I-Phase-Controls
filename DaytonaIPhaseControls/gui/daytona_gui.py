import os
import csv
import json
from urllib import response
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication, QTableWidgetItem, QFileDialog, QWidget
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

        version = "v0.1"
        title = "Daytona I-Phase Controls"
        self.menuVersion.setTitle(version)
        self.setWindowTitle(title)

        #Path options
        self.HDC_paths = ["Both", "Path A", "Path B"]
        self.JH_paths = ["Passthrough", "Around", "Alternating"]
        self.ICD_options = ["Default", "Jughandle"]
        self.pathComboBox.addItems(self.HDC_paths)
        self.JHpathComboBox.addItems(self.JH_paths)
        self.ICDComboBox.addItems(self.ICD_options)

        self.updateGUI_with_intent(os.path.join(os.path.dirname(__file__), "config", "default_daytona_intent.json"))

        #Wire up buttons to functions
        self.connect_btn.clicked.connect(self.connect_to_ICS)
        self.getreadbacks_btn.clicked.connect(lambda: self.get_readbacks(self.get_ics_channels(self.parameter_table)))
        self.method_combo_box.currentTextChanged.connect(self.on_method_dropdown_change)
        self.putsetpoints_btn.clicked.connect(lambda: self.post_setpoints(self.get_ics_channels(self.parameter_table)))
        self.upload_method_btn.clicked.connect(self.load_csv_file)
        self.generateTT_btn.clicked.connect(self.generate_tt)

        self.twr_headers = ['Time (ms)', 'Frequency (Hz)', 'Amplitude (V)']
        self.pathA_tbl.setHorizontalHeaderLabels(self.twr_headers)
        self.pathB_tbl.setHorizontalHeaderLabels(self.twr_headers)

        self.plotting_widget.setBackground('w')
        self.plotting_widget.clear()
        self.plotting_widget.addLegend()

        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

        self.find_methods()
        self.update_method_table(os.path.join(os.path.dirname(__file__), "methods", "init", "init_method_daytona.csv"))
        

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
            response = self.ics_client.send_request('api/ics/instrument/version/', 
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
        methods_dir = os.path.join(os.path.dirname(__file__), "methods")
        method_files = [f for f in os.listdir(methods_dir) if f.endswith('.csv')]
        method_names = [os.path.splitext(f)[0] for f in method_files]
        self.method_combo_box.clear()
        self.method_combo_box.addItems(method_names)

    def on_method_dropdown_change(self, method_name):
        '''
        Handle changes in the method dropdown selection.
        When a new method is selected, this function updates the parameter table with the corresponding CSV file for that method.
        '''
        if method_name:
            csv_file_path = os.path.join(os.path.dirname(__file__), "methods", f"{method_name}.csv")
            self.update_method_table(csv_file_path)

    def update_method_table(self, csv_file_path):
        '''
        Update the parameter table in the GUI with the provided parameters.
        Clears existing entries and populates the table with new parameter data.
        '''
        self.parameter_table.setRowCount(0)  # Clear existing rows

        with open(csv_file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # First row = column headers

            # Set column count and headers
            self.parameter_table.setColumnCount(len(headers))
            self.parameter_table.setHorizontalHeaderLabels(headers)

            for row_data in reader:
                row_position = self.parameter_table.rowCount()
                self.parameter_table.insertRow(row_position)

                for column, cell_value in enumerate(row_data):
                    item = QtWidgets.QTableWidgetItem(cell_value)
                    self.parameter_table.setItem(row_position, column, item)

    def get_ics_channels(self, table_widget):
        '''
        Extract canonical names from the parameter table and return them as a list.
        Iterates through the rows of the table and collects the canonical names from the first column.
        '''
        channel_result = []
        for row in range(table_widget.rowCount()):
            board_id = table_widget.item(row, 1)  # Second column = board_id
            parameter = table_widget.item(row, 2)  # Third column = parameter
            setpoint = table_widget.item(row, 3)  # Fourth column = setpoint value
            if board_id:
                channel_array = (f"@{board_id.text()}.{parameter.text()}", setpoint.text())
                channel_result.append(channel_array)
        return channel_result
    
    def handle_readback_response(self, response, table_widget=None):
        print(table_widget.rowCount())   
        if isinstance(response, Exception):
            print(f"Error retrieving readbacks: {response}")
            return None
        else:
            print(f"Readback response: {response}")
            # Process the response as needed (e.g., update the GUI, plot data, etc.)
            for row in range(table_widget.rowCount()):
                dict_response = response[row]
                item = table_widget.item(row, 4)  # Fifth column = readback value
                if item:
                    item.setText(str(dict_response.get("value", "N/A")))
            return response    

    def get_readbacks(self, data):
        print(f"Getting readbacks for channels: {data}")

        readback_list = []
        for paramter, setpoint in data:
            readback_list.append(paramter)
            print(f"Parameter: {paramter}, Setpoint: {setpoint}")

        # Keep the worker alive
        self.worker = RequestWorker(
            self.ics_client.send_request,
            'api/ics/channels/',
            8001,
            method='GET',
            data=";".join(readback_list)
        )

        self.worker.finished.connect(lambda response: self.handle_readback_response(response, self.parameter_table))
        self.worker.finished.connect(self.worker.deleteLater)  # safely delete after done
        self.worker.start()
    
    def post_setpoints(self, data):
        print(f"Posting setpoints for channels: {data}")

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

    def load_csv_file(self):
        expected_columns = ['Canonical Name', 'Board ID', 'Parameter', 'Setpoint']
        
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

                self.parameter_table.setRowCount(0)  # Clear existing data

                for row_data in reader:
                    row_index = self.parameter_table.rowCount()
                    self.parameter_table.insertRow(row_index)

                    for col_index, col_name in enumerate(expected_columns):
                        value = row_data.get(col_name, "")
                        item = QTableWidgetItem(value)
                        self.parameter_table.setItem(row_index, col_index, item)

        except Exception as e:
            print(f"Error loading CSV: {e}")
    
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
            self.input_fill_params_amp.setText(str(intent_data["fillAmp"]))
            self.input_fill_params_freq.setText(str(intent_data["fillFrequency"]))
            self.input_trap_params_amp.setText(str(intent_data["trapAmp"]))
            self.input_trap_params_freq.setText(str(intent_data["trapFrequency"]))
            self.input_release_params_amp.setText(str(intent_data["releaseAmp"]))
            self.input_release_params_freq.setText(str(intent_data["releaseFrequency"]))
            self.wait4ready_box.setChecked(intent_data["wait_for_ready"])
            self.pathComboBox.setCurrentIndex(self.HDC_paths.index(intent_data["HDCpath"])) if intent_data["HDCpath"] in self.HDC_paths else 0
            self.JHpathComboBox.setCurrentIndex(self.JH_paths.index(intent_data["JHpath"])) if intent_data["JHpath"] in self.JH_paths else 0   
            self.update_twr_gui_tables(intent_data)
            #print(intent_data["pathA_traveling_wave_profile"])     
        except Exception as e:
            print(f"Error loading intent file: {e}")

    def build_intent(self):
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
            "flushVoltage": float(self.input_flush_voltage.text()),
            "fillAmp": float(self.input_fill_params_amp.text()),
            "fillFrequency": float(self.input_fill_params_freq.text()),
            "trapAmp": float(self.input_trap_params_amp.text()),
            "trapFrequency": float(self.input_trap_params_freq.text()),
            "releaseAmp": float(self.input_release_params_amp.text()),
            "releaseFrequency": float(self.input_release_params_freq.text()),
            "wait_for_ready": self.wait4ready_box.isChecked(),
            "HDCpath": self.pathComboBox.currentText(),
            "JHpath": self.JHpathComboBox.currentText(),
            "pathA_traveling_wave_profile": {
                "initial_state": {
                    "frequency": float(self.pathA_tbl.item(0, 1).text()),
                    "amplitude": float(self.pathA_tbl.item(0, 2).text())
                },
                "ramps": [
                    {
                        "time": float(self.pathA_tbl.item(row, 0).text()),
                        "state": {
                            "frequency": float(self.pathA_tbl.item(row, 1).text()),
                            "amplitude": float(self.pathA_tbl.item(row, 2).text())
                        }
                    }
                    for row in range(self.pathA_tbl.rowCount())
                ]
            },
            "pathB_traveling_wave_profile": {
                "initial_state": {
                    "frequency": float(self.pathB_tbl.item(0, 1).text()),
                    "amplitude": float(self.pathB_tbl.item(0, 2).text())
                },
                "ramps": [
                    {
                        "time": float(self.pathB_tbl.item(row, 0).text()),
                        "state": {
                            "frequency": float(self.pathB_tbl.item(row, 1).text()),
                            "amplitude": float(self.pathB_tbl.item(row, 2).text())
                        }
                    }
                    for row in range(self.pathB_tbl.rowCount())
                ]
            }
        }
        return intent
    
    def generate_tt(self):
        intent = self.build_intent()
        tt = Daytona_HDC_tt(intent=intent) if intent['HDCpath'] == 'Both' else Daytona_SinglePath_tt(intent=intent)
        tt_dictionary = tt.get_tts()
        tt_dict = {}
        for module in list(tt_dictionary.keys()):
            step_info = []
            last_time = 0.0
            for item in tt_dictionary[module]:
                step_info.append({
                    "opcode": item.opcode.value,
                    "ticks": int((float(item.abs_time_ms) - last_time) * 10.0), #to clock ticks
                    "address": self.parameter_mapping(item.canonical_name),
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
        # Not found → return None or default values
        return None, None

    def update_twr_gui_tables(self, data_dict):
        twr_keys = ['pathA_traveling_wave_profile', 'pathB_traveling_wave_profile']
        for key in twr_keys:
            ramps = data_dict[key]['ramps']
            table = self.pathA_tbl if key == 'pathA_traveling_wave_profile' else self.pathB_tbl
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
