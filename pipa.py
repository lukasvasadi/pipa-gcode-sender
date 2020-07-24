import os
import sys
import platform
import time
import serial
from serial.tools import list_ports
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import qtmodern.styles
import qtmodern.windows


class Window(QMainWindow):
    """
    GUI for passing g-code commands to liquid handler.

    Use the following helpful g-code commands upon startup:
        M31 print time
        M92 set axis steps per unit
        M106 turns on fan and sets speed; M107 turns fan off
        M114 current position
        M119 endstop status
        M122 driver status/TMC debug
        M500 saves new settings to EEPROM
        M502 factory reset of all configurable settings (EEPROM)
        M906 set or report motor current in milliamps using axis codes X, Y, Z, E
        M914 alone shows Stallguard sensitivity values (can also be used to override values)
    """

    def __init__(self):
        super(Window, self).__init__()
        QApplication.setStyle(QStyleFactory.create('Plastique'))

        self.layout = QVBoxLayout()
        self.layout_v0 = QVBoxLayout()
        # self.layout_v0.addStretch(1)
        self.layout_v1 = QVBoxLayout()
        self.layout_v1.addStretch(1)
        self.layout_v2 = QVBoxLayout()
        # self.layout_v2.addStretch(1)
        self.layout_h0 = QHBoxLayout()
        self.layout_h1 = QHBoxLayout()
        self.layout_h2 = QHBoxLayout()
        self.layout_h3 = QHBoxLayout()
        self.layout_h4 = QHBoxLayout()
        self.layout_h5 = QHBoxLayout()
        self.layout_h6 = QHBoxLayout()
        self.layout_h7 = QHBoxLayout()

        self.protocol_table = QTableWidget()

        self.lbl_command_name = QLabel("Command name")
        self.lbl_command_type = QLabel("Type")
        self.lbl_command_duration = QLabel("Time")
        self.lbl_serial_terminal = QLabel("Serial terminal")
        self.lbl_command_line = QLabel("Command line")

        self.txt_command_name = QLineEdit("Step 1...")
        self.txt_command_duration = QLineEdit("00:00:30")
        self.txt_gcode_direct = QLineEdit("G0 X0 Y0 Z0")
        self.txt_command_line = QLineEdit("G1 E0")

        self.command = QComboBox()
        self.command.addItem("Home")
        self.command.addItem("Add solution")
        self.command.addItem("Wash")
        self.command.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        self.btn_add = QPushButton("Add")
        self.btn_connect = QPushButton("Connect")
        self.btn_start = QPushButton("Start")
        self.btn_reset = QPushButton("Reset")
        self.btn_stop = QPushButton("EOS")
        self.btn_send = QPushButton("Send")

        self.btn_stop.setStyleSheet("background-color: #DD1D1D")

        self.progress = QProgressBar()
        self.step_index = -1

        self.text_editor = QTextEdit()

        self.instructions = {"command": [], "type": [], "time": []}
        self.gcode_command_array = []
        self.motherboard = ''

        # Positions
        self.tip_x_init = 50
        self.tip_x = self.tip_x_init
        self.tip_y_init = 53.5
        self.tip_y = self.tip_y_init
        self.tip_delta = 9

        self.reservoir_x_init = 252
        self.reservoir_x = self.reservoir_x_init
        self.reservoir_y_init = 122
        self.reservoir_y = self.reservoir_y_init
        self.reservoir_delta = 13

        self.sequence_counter = 1

        # Execute main window
        self.main_window()

    def main_window(self):
        # Create layout
        self.setGeometry(400, 100, 600, 600)
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(self.layout)

        self.generate_table()

        self.btn_add.clicked.connect(self.add_step)
        self.btn_connect.clicked.connect(self.connect)
        self.btn_start.clicked.connect(self.start)
        self.btn_reset.clicked.connect(self.reset)
        self.btn_stop.clicked.connect(self.em_stop)
        self.btn_send.clicked.connect(self.transmit_cmd_line)
        # self.txt_command_line.keyPressEvent = self.keyPressEvent

        # Widget display
        self.layout_h0.addWidget(self.protocol_table)
        self.layout_v0.addWidget(self.lbl_command_name)
        self.layout_v1.addWidget(self.lbl_command_type)
        self.layout_v2.addWidget(self.lbl_command_duration)
        self.layout_v0.addWidget(self.txt_command_name)
        self.layout_v1.addWidget(self.command)
        self.layout_v2.addWidget(self.txt_command_duration)
        self.layout_h2.addWidget(self.btn_connect)
        self.layout_h2.addWidget(self.btn_start)
        self.layout_h2.addWidget(self.btn_reset)
        self.layout_h2.addWidget(self.btn_stop)
        self.layout_h3.addWidget(self.progress)
        self.layout_h4.addWidget(self.lbl_serial_terminal)
        self.layout_h5.addWidget(self.text_editor)
        self.layout_h6.addWidget(self.lbl_command_line)
        self.layout_h7.addWidget(self.txt_command_line)
        self.layout_h7.addWidget(self.btn_send)

        self.layout.addLayout(self.layout_h0)
        self.layout_h1.addLayout(self.layout_v0)
        self.layout_h1.addLayout(self.layout_v1)
        self.layout_h1.addLayout(self.layout_v2)
        self.layout_h1.addWidget(self.btn_add)
        self.layout.addLayout(self.layout_h1)
        self.layout.addLayout(self.layout_h2)
        self.layout.addLayout(self.layout_h3)
        self.layout.addLayout(self.layout_h4)
        self.layout.addLayout(self.layout_h5)
        self.layout.addLayout(self.layout_h6)
        self.layout.addLayout(self.layout_h7)

        self.layout.setSpacing(10)

        self.show()

    def generate_table(self):
        self.protocol_table.setSelectionBehavior(QTableView.SelectRows)
        self.protocol_table.setRowCount(len(self.instructions["command"]))
        self.protocol_table.setColumnCount(3)
        self.protocol_table.setHorizontalHeaderLabels(["Command Name", "Command Type", "Delay Time"])
        header = self.protocol_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        for row in range(len(self.instructions["command"])):
            self.protocol_table.setItem(row, 0, QTableWidgetItem(self.instructions["command"][row]))
            self.protocol_table.setItem(row, 1, QTableWidgetItem(self.instructions["type"][row]))
            self.protocol_table.setItem(row, 2, QTableWidgetItem(self.instructions["time"][row]))

        self.protocol_table.resizeRowsToContents()

    def add_step(self):
        command_name = self.txt_command_name.text()
        command_type = str(self.command.currentText())
        command_time = self.txt_command_duration.text()

        self.instructions["command"].append(command_name)
        self.instructions["type"].append(command_type)
        self.instructions["time"].append(command_time)

        self.text_editor.append(command_name + ", " + command_type + ", " + command_time)
        self.generate_table()

    def load_instructions(self):
        try:
            # Re-initialize command array
            self.gcode_command_array = []
            file_path = QFileDialog.getOpenFileName(self, 'Open file', os.getenv('HOME'))[0]
            with open(file_path, 'r') as file_gcode:  # Open with intention to read
                for line in file_gcode:
                    self.gcode_command_array.append(line)
        except IndexError:
            self.text_editor.append("Error: file may have incorrect format")
        except NameError:
            self.text_editor.append("Error: cannot load file")

    def step_indexer(self):
        progress = (self.sequence_counter / len(self.instructions["command"])) * 100
        progress = int(progress)
        self.progress.setValue(progress)

    def connect(self):
        self.text_editor.append("Welcome")
        port = ""
        try:
            ports_available = list(list_ports.comports())
            if platform.system() == "Windows":
                for com in ports_available:
                    if "USB Serial Device" in com.description:
                        port = com[0]
            elif platform.system() == "Darwin" or "Linux":
                for com in ports_available:
                    if "Marlin USB Device" in com.description:
                        port = com[0]
            else:
                port = "COM31"

            self.text_editor.append("Port: " + port)
            self.motherboard = serial.Serial(port=port, baudrate=250000, timeout=1)
            # Toggle DTR to reset microcontroller — important for cleaning serial buffer
            self.motherboard.setDTR(False)
            time.sleep(0.1)
            # Wipe serial buffer
            self.motherboard.reset_input_buffer()
            self.motherboard.reset_output_buffer()
            self.motherboard.setDTR(True)
            self.initialize()
        except AttributeError:
            self.text_editor.append("Error: motherboard not detected")

    def reset(self):
        # Toggle DTR to reset microcontroller — important for cleaning serial buffer
        self.motherboard.setDTR(False)
        time.sleep(0.1)
        # Wipe serial buffer
        self.motherboard.reset_input_buffer()
        self.motherboard.reset_output_buffer()
        self.motherboard.setDTR(True)
        self.initialize()
        self.text_editor.append("Reset performed")

    def initialize(self):
        # Retrieve firmware info
        # self.transmit("M115")

        # Set units to mm
        self.transmit("G21")

        # Enable cold extrusion
        self.transmit("M302 S0")

        # TMC debugging
        # self.transmit("M122")

        # Home motors
        self.transmit("G28 Y")
        self.transmit("G28 X")
        self.transmit("G28 Z")

        # Update z-axis default feedrate
        # self.transmit("M203 Z1000")

        # Move z-axis up for clearance
        self.transmit("G1 X10 Y10 Z80 F1000")

    def transmit(self, command):
        command = command.upper() + "\r\n"
        # self.text_editor.append(command[0:-2])
        self.motherboard.write(command.encode())
        # Wait for motherboard to receive transmission
        time.sleep(1)
        self.receive()

    def transmit_cmd_line(self):
        command = self.txt_command_line.text()
        command = command.upper() + "\r\n"
        self.motherboard.write(command.encode())
        self.text_editor.append(command[0:-2])
        time.sleep(1)
        self.receive()
        self.gcode_command_array.append(command)
        # self.txt_command_line.setText("G1 E0")
        # self.motherboard.close()
        self.step_index = -1

    def receive(self):
        # Attempt to read all incoming messages from motherboard
        while True:
            transmission = self.motherboard.readline()[0:-1].decode('utf-8', 'ignore')
            if transmission == "":
                break
            self.text_editor.append(transmission)
            time.sleep(0.1)

    def em_stop(self):
        # M112 EMERGENCY STOP
        self.transmit("M112")
        self.receive()

    def start(self):
        for i in range(len(self.instructions["command"])):
            self.step_index = i
            delay_list = self.instructions["time"][i].split(':')
            delay = (int(delay_list[0]) * 3600) + (int(delay_list[1]) * 60) + int(delay_list[2])
            delay += 20  # Buffer time
            self.sequence(delay)
        self.text_editor.append("Experiment finished")

    def collect_tip(self):
        # self.transmit("G1 Z80 F1000")  # Raise pipettes for clearance
        self.transmit("G1 X" + str(self.tip_x) + " Y" + str(self.tip_y) + "F2000")  # Move to tip
        self.transmit("G1 Z8.5 F500")  # Lower pipettes to collect tips
        self.transmit("G1 Z80 F1000")  # Raise pipettes for clearance

        if self.sequence_counter == 5 or self.sequence_counter == 10 or self.sequence_counter == 15 or \
                self.sequence_counter == 20:
            self.tip_x = self.tip_x_init
            self.tip_y += self.tip_delta
        else:
            self.tip_x += self.tip_delta

    def collect_solution(self):
        self.transmit("G1 X" + str(self.reservoir_x) + " Y" + str(self.reservoir_y) + "F2000")  # Move to reservoir
        self.transmit("G1 E-9 F100")  # Compress plunger
        self.transmit("G1 Z8 F500")  # Lower pipettes into reservoir
        self.transmit("G1 E0 F100")  # Draw solution
        self.transmit("G1 Z100 F1000")  # Raise pipettes

        if self.sequence_counter == 10 or self.sequence_counter == 20:
            self.reservoir_x += self.reservoir_delta
            self.reservoir_y = self.reservoir_y_init
        else:
            self.reservoir_y -= self.reservoir_delta

    def eject_tips(self):
        self.transmit("G1 Z160 F1000")  # Raise pipettes
        self.transmit("G1 X60 Y200 F2000")  # Move to waste collection
        self.transmit("G1 E-12 F100")  # Eject tips
        self.transmit("G1 E0 F100")  # Return plunger to position 0

    def sequence(self, delay):
        # Dispensing phase
        self.collect_tip()
        self.collect_solution()
        self.transmit("G1 X178.5 Y162 F2000")  # Move to sensor
        self.transmit("G1 Z22 F500")  # Lower into well
        self.transmit("G1 E-9 F100")  # Inject
        self.eject_tips()

        self.sequence_counter += 1

        time.sleep(delay)

        # Aspiration phase
        self.collect_tip()
        self.transmit("G1 X178.5 Y162 F2000")  # Move to sensor
        self.transmit("G1 E-9 F100")  # Compress plunger
        self.transmit("G1 Z20.5 F500")  # Lower into well
        self.transmit("G1 E0 F100")  # Withdraw
        self.eject_tips()

    def toggle_up(self):
        if (-1 * self.step_index) < len(self.instructions["command"]):
            self.txt_command_line.setText(self.gcode_command_array[self.step_index])
            self.step_index -= 1

    def toggle_down(self):
        if self.step_index < len(self.instructions["command"]):
            self.txt_command_line.setText(self.gcode_command_array[self.step_index])
            self.step_index += 1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.transmit_cmd_line()
        elif event.key() == Qt.Key_Up:
            self.toggle_up()
        elif event.key() == Qt.Key_Down:
            self.toggle_down()
        else:
            pass
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    qtmodern.styles.dark(app)
    mw = qtmodern.windows.ModernWindow(window)
    mw.show()
    sys.exit(app.exec_())
