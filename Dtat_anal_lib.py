import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QColorDialog, QCheckBox, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView, QDialog,
    QLineEdit, QFormLayout, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure




class MathOpsDialog(QDialog):
    def __init__(self, parent, datasets):
        super().__init__(parent)
        self.datasets = datasets
        self.setWindowTitle("Math Operations")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Info about available datasets
        info_text = "Available datasets:\n"
        for i, data in enumerate(self.datasets, 1):
            info_text += f"  T{i}: {data['name']} (len={len(data['x'])})\n"

        layout.addWidget(QLabel(info_text))

        # Formula input
        form_layout = QFormLayout()
        self.expr_input = QLineEdit()
        self.expr_input.setPlaceholderText("e.g. T1.y**4 - T2.y")
        form_layout.addRow("f(x) =", self.expr_input)
        layout.addLayout(form_layout)

        # Apply button
        apply_btn = QPushButton("Apply and Plot")
        apply_btn.clicked.connect(self.apply_expression)
        layout.addWidget(apply_btn)

    def apply_expression(self):
        expr = self.expr_input.text().strip()
        if not expr:
            QMessageBox.warning(self, "Error", "Please enter an expression")
            return

        # Build evaluation environment
        env = {}
        for i, data in enumerate(self.datasets, 1):
            env[f"T{i}"] = {"x": data["x"], "y": data["y"]}

        try:
            # Convert ROOT-style Tn.y to Python Tn['y']
            safe_expr = expr.replace(".x", "['x']").replace(".y", "['y']")
            result = eval(safe_expr, {"np": np}, env)

            if not isinstance(result, np.ndarray):
                QMessageBox.warning(self, "Error", "Expression did not return an array")
                return

            # Return result to parent
            self.parent().add_dataset(
                self.datasets[0]["x"],  # assume same x for now
                result,
                label=f"Math: {expr}"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Evaluation Error", str(e))



class DataPlotWidget(QWidget):
    def __init__(self):
        super().__init__()

        # --- Splitter Layout (plot left, table right) ---
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(splitter)

        # Left container for plot + controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        splitter.addWidget(left_widget)

        # matplotlib figure + toolbar
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)

        left_layout.addWidget(self.toolbar)
        left_layout.addWidget(self.canvas)

        # --- Control panel under plot ---
        control_layout = QHBoxLayout()
        left_layout.addLayout(control_layout)

        self.add_btn = QPushButton("Add Data")
        self.add_btn.clicked.connect(self.add_data)
        control_layout.addWidget(self.add_btn)

        self.color_btn = QPushButton("Set Default Color")
        self.color_btn.clicked.connect(self.set_default_color)
        control_layout.addWidget(self.color_btn)

        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.stateChanged.connect(self.toggle_grid)
        control_layout.addWidget(self.grid_checkbox)

        control_layout.addWidget(QLabel("Line Style:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(["-", "--", ":", "-."])
        self.style_combo.currentTextChanged.connect(self.change_style)
        control_layout.addWidget(self.style_combo)

        # Axis scale toggle buttons
        self.logx_btn = QPushButton("Toggle X Log")
        self.logx_btn.clicked.connect(self.toggle_xlog)
        control_layout.addWidget(self.logx_btn)

        self.logy_btn = QPushButton("Toggle Y Log")
        self.logy_btn.clicked.connect(self.toggle_ylog)
        control_layout.addWidget(self.logy_btn)

        # --- Toggle table button ---
        self.toggle_table_btn = QPushButton("Hide Table")
        self.toggle_table_btn.clicked.connect(self.toggle_table)
        control_layout.addWidget(self.toggle_table_btn)

        # --- Right side = table ---
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Name", "# Points", "Style", "Color", "Scale Y", "Show", "Delete"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        splitter.addWidget(self.table)

        splitter.setSizes([800, 300])  # initial ratio

        # Storage
        self.lines = []       # list of line objects
        self.data_store = {}  # mapping line -> original (x, y)
        self.current_color = "blue"
        self.current_style = "-"

        # Track hidden state
        self.table_hidden = False

        # Initial test plot
        self.add_data()

    # --- Plotting functions ---
    def add_data(self):
        """Add a new dataset to the plot"""
        x = np.linspace(0.1, 10, 200)  # safe for log axes
        y = np.sin(x) + np.random.randn(len(x)) * 0.1
        name = f"Data {len(self.lines) + 1}"

        line, = self.ax.plot(x, y,
                             color=self.current_color,
                             linestyle=self.current_style,
                             label=name)
        self.lines.append(line)
        self.data_store[line] = (x, y)
        self.ax.legend()
        self.canvas.draw()
        self.add_to_table(line, name, x, y)

    def add_to_table(self, line, name, x, y):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Name
        self.table.setItem(row, 0, QTableWidgetItem(name))

        # # Points
        self.table.setItem(row, 1, QTableWidgetItem(str(len(x))))

        # Style
        self.table.setItem(row, 2, QTableWidgetItem(line.get_linestyle()))

        # Color
        color_btn = QPushButton()
        color_btn.setStyleSheet(f"background-color: {line.get_color()}")
        color_btn.clicked.connect(lambda _, r=row, l=line: self.change_line_color(r, l))
        self.table.setCellWidget(row, 3, color_btn)

        # Scale Y
        scale_cb = QComboBox()
        scale_cb.addItems(["0.1", "0.5", "1", "2", "10"])
        scale_cb.setCurrentText("1")
        scale_cb.currentTextChanged.connect(lambda s, l=line: self.scale_line_y(l, float(s)))
        self.table.setCellWidget(row, 4, scale_cb)

        # Show/Hide
        show_cb = QCheckBox()
        show_cb.setChecked(True)
        show_cb.stateChanged.connect(lambda state, l=line: self.toggle_line(l, state))
        self.table.setCellWidget(row, 5, show_cb)

        # Delete
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(lambda _, r=row, l=line: self.delete_line(r, l))
        self.table.setCellWidget(row, 6, del_btn)

    def change_line_color(self, row, line):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            line.set_color(hex_color)
            btn = self.table.cellWidget(row, 3)
            if btn:
                btn.setStyleSheet(f"background-color: {hex_color}")
            self.ax.legend()
            self.canvas.draw()

    def scale_line_y(self, line, factor):
        x, y = self.data_store[line]
        line.set_ydata(y * factor)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def toggle_line(self, line, state):
        line.set_visible(state == Qt.CheckState.Checked.value)
        self.ax.legend()
        self.canvas.draw()

    def delete_line(self, row, line):
        if line in self.lines:
            self.lines.remove(line)
            self.data_store.pop(line, None)
        line.remove()
        self.ax.legend()
        self.canvas.draw()
        self.table.removeRow(row)

    # --- Config functions ---
    def set_default_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()

    def toggle_grid(self, state):
        self.ax.grid(state == Qt.CheckState.Checked.value)
        self.canvas.draw()

    def change_style(self, style):
        self.current_style = style

    def toggle_xlog(self):
        self.ax.set_xscale("log" if self.ax.get_xscale() == "linear" else "linear")
        self.canvas.draw()

    def toggle_ylog(self):
        self.ax.set_yscale("log" if self.ax.get_yscale() == "linear" else "linear")
        self.canvas.draw()

    def toggle_table(self):
        """Show/hide the table panel"""
        if self.table_hidden:
            self.table.show()
            self.toggle_table_btn.setText("Hide Table")
        else:
            self.table.hide()
            self.toggle_table_btn.setText("Show Table")
        self.table_hidden = not self.table_hidden


# --- Run app ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DataPlotWidget()
    win.setWindowTitle("Interactive Data Plotter with Collapsible Table")
    win.resize(1200, 600)
    win.show()
    sys.exit(app.exec())
