import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QColorDialog,
    QCheckBox, QMessageBox, QHeaderView, QLineEdit, QLabel,
    QDialog, QGridLayout, QComboBox, QSpinBox , QAbstractItemView, QSlider
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure
from scipy.signal import savgol_filter

# -----------------------------
# Math Operations Dialog
# -----------------------------
class MathOpsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Math Operations")
        layout = QGridLayout(self)

        self.expr_input = QLineEdit()
        layout.addWidget(QLabel("f(x) ="), 0, 0)
        layout.addWidget(self.expr_input, 0, 1, 1, 3)

        self.ok_btn = QPushButton("Apply")
        self.ok_btn.clicked.connect(self.accept)
        layout.addWidget(self.ok_btn, 1, 2)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn, 1, 3)

    def get_expression(self):
        return self.expr_input.text()


class FilterDialog(QDialog):
    def __init__(self, parent, datasets):
        super().__init__(parent)
        self.setWindowTitle("Apply Filter")
        self.datasets = datasets
        self.parent = parent

        layout = QVBoxLayout(self)

        # Dataset selector
        self.dataset_box = QComboBox()
        for i, ds in enumerate(datasets):
            self.dataset_box.addItem(f"T{i+1}")
        layout.addWidget(QLabel("Select Dataset"))
        layout.addWidget(self.dataset_box)

        # Filter selector
        self.filter_box = QComboBox()
        self.filter_box.addItems(["Moving Average", "Cosine", "Savitzky-Golay"])
        layout.addWidget(QLabel("Select Filter"))
        layout.addWidget(self.filter_box)

        # Parameters
        self.param1 = QSpinBox()
        self.param1.setRange(1, 999)
        self.param1.setValue(5)
        layout.addWidget(QLabel("Window Size"))
        layout.addWidget(self.param1)

        self.param2 = QSpinBox()
        self.param2.setRange(1, 10)
        self.param2.setValue(2)
        layout.addWidget(QLabel("Polyorder (SG only)"))
        layout.addWidget(self.param2)

        # Apply button
        apply_btn = QPushButton("Apply Filter")
        apply_btn.clicked.connect(self.apply_filter)
        layout.addWidget(apply_btn)

    def apply_filter(self,checked=False):
        try:
            idx = self.dataset_box.currentIndex()
            ds = self.datasets[idx]
            y = np.array(ds["y"])
            x = np.array(ds["x"])

            ftype = self.filter_box.currentText()
            win = self.param1.value()
            poly = self.param2.value()

            if ftype == "Moving Average":
                y_new = self.moving_average(y, win)
                label = f"T{idx+1}_MA"
            elif ftype == "Cosine":
                y_new = self.cosine_smooth(y, win)
                label = f"T{idx+1}_Cosine"
            elif ftype == "Savitzky-Golay":
                y_new = self.sg_filter(y, win, poly)
                label = f"T{idx+1}_SG"
            else:
                return

            # Check for bad values
            if np.any(np.isnan(y_new)) or np.any(np.isinf(y_new)):
                QMessageBox.warning(self, "Error", "Invalid values in filter result")
                return

            # Add filtered dataset to main plot
            self.parent.add_dataset(x, y_new, label=label)

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def moving_average(self, y, window):
        if window <= 0:
            raise ValueError("Window must be > 0")
        if window > len(y):
            raise ValueError("Window larger than dataset")
        return np.convolve(y, np.ones(window)/window, mode="same")

    def cosine_smooth(self,y, window):
        if window <= 0:
            raise ValueError("Window must be > 0")
        if window > len(y):
            raise ValueError("Window larger than dataset")
        w = np.hanning(window)
        return np.convolve(y, w/w.sum(), mode="same")

    def sg_filter(self,y, window, poly):
        if window % 2 == 0:  # must be odd
            window += 1
        if window > len(y):
            raise ValueError("Window larger than dataset")
        if poly >= window:
            raise ValueError("Polyorder must be less than window size")
        return savgol_filter(y, window, poly)


# -----------------------------
# Data Plot Widget
# -----------------------------
class DataPlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Plot Widget")

        # Main layout
        self.layout = QVBoxLayout(self)

        # Matplotlib Figure + Canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.auto_scale_x = True

        # Add matplotlib toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas, stretch=1)

        # Controls layout
        self.controls_layout = QHBoxLayout()
        self.layout.addLayout(self.controls_layout)

        # Buttons
        self.add_btn = QPushButton("Add Data")
        self.add_btn.clicked.connect(self.add_data)
        self.controls_layout.addWidget(self.add_btn)

        self.math_btn = QPushButton("Math Ops")
        self.math_btn.clicked.connect(self.open_math_dialog)
        self.controls_layout.addWidget(self.math_btn)

        self.logx_btn = QPushButton("Toggle Log X")
        self.logx_btn.setCheckable(True)
        self.logx_btn.toggled.connect(self.toggle_logx)
        self.controls_layout.addWidget(self.logx_btn)

        self.logy_btn = QPushButton("Toggle Log Y")
        self.logy_btn.setCheckable(True)
        self.logy_btn.toggled.connect(self.toggle_logy)
        self.controls_layout.addWidget(self.logy_btn)
        self.filter_btn = QPushButton("Filters")
        self.filter_btn.clicked.connect(self.open_filter_dialog)
        self.controls_layout.addWidget(self.filter_btn)

        self.auto_scale_button = QPushButton("Auto-Scale X")
        self.auto_scale_button.setCheckable(True)
        self.auto_scale_button.setChecked(True)  # default on
        self.auto_scale_button.clicked.connect(self.on_auto_scale_toggle)
        self.controls_layout.addWidget(self.auto_scale_button)

        # Grid controls
        self.grid_checkbox = QPushButton("Toggle Grid")
        self.grid_checkbox.setCheckable(True)
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.toggled.connect(self._toggle_grid)
        self.controls_layout.addWidget(self.grid_checkbox)

        self.grid_style = QComboBox()
        self.grid_style.addItems(["-", "--", ":", "-."])
        self.grid_style.currentTextChanged.connect(self._update_grid_style)
        self.controls_layout.addWidget(self.grid_style)

        # Table toggle button
        self.toggle_table_btn = QPushButton("Hide Table")
        self.toggle_table_btn.setCheckable(True)
        self.toggle_table_btn.toggled.connect(self.toggle_table)
        self.controls_layout.addWidget(self.toggle_table_btn)

        # Dataset table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Points", "Style", "Color", "Visible", "Y-Scale", "Selection"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(
        QAbstractItemView.EditTrigger.DoubleClicked |
        QAbstractItemView.EditTrigger.SelectedClicked    )
        # Connect signal
        self.table.cellChanged.connect(self.on_table_name_changed)
        self.layout.addWidget(self.table, stretch=0)

        # Storage for datasets
        self.datasets = []

        # Enable wheel zoom
        self._connect_zoom()

        # Show grid initially
        self.ax.grid(True, linestyle="-")
        self.canvas.draw()

    # -----------------------------
    # Dataset management
    # -----------------------------
    def add_data(self):
        # Dummy example data
        x = np.linspace(0, 10, 200)
        y = np.sin(x) + np.random.normal(0, 0.1, len(x))
        self.add_dataset(x, y, label=f"Data{len(self.datasets)+1}")

    def add_dataset(self, x, y, label="Data"):
        line, = self.ax.plot(x, y, label=label)
        ds = {"x": x, "y": y, "line": line, "label": label}
        self.datasets.append(ds)

        row = self.table.rowCount()
        self.table.insertRow(row)

        # Name
        self.table.setItem(row, 0, QTableWidgetItem(label))
        
        # Points
        self.table.setItem(row, 1, QTableWidgetItem(str(len(x))))
        
        # Style (combo box)
        style_combo = QComboBox()
        style_combo.addItems(['-', '--', '-.', ':'])
        style_combo.setCurrentText(line.get_linestyle())
        style_combo.currentTextChanged.connect(lambda text, r=row: self.on_style_changed(r, text))
        self.table.setCellWidget(row, 2, style_combo)
        
        # Color
        color_item = QTableWidgetItem()
        mcolor = line.get_color()
        try:
            qcolor = QColor(mcolor)  # works for hex strings and names
        except Exception:
            # fallback: assume RGBA tuple
            rgba = np.array(line.get_color())
            qcolor = QColor(int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255))
        color_item.setBackground(qcolor)
        self.table.setItem(row, 3, color_item)
        self.table.itemDoubleClicked.connect(self.change_color)
        
        # Visible
        visible_item = QTableWidgetItem()
        visible_item.setCheckState(Qt.CheckState.Checked)
        self.table.setItem(row, 4, visible_item)
        self.table.itemChanged.connect(self.on_table_item_changed)

        # Y-Scale
        yscale_item = QTableWidgetItem("1.0")
        self.table.setItem(row, 5, yscale_item)
        print("DEBUG line color:", line.get_color())
        self.update_plot()

        # Y-Scale
        self.table.setItem(row, 6, QTableWidgetItem("1.0"))

        # Range sliders
        slider_widget = QWidget()
        layout = QHBoxLayout(slider_widget)
        layout.setContentsMargins(0,0,0,0)

        min_slider = QSlider(Qt.Orientation.Horizontal)
        min_slider.setMinimum(0)
        min_slider.setMaximum(len(x)-1)
        min_slider.setValue(0)

        max_slider = QSlider(Qt.Orientation.Horizontal)
        max_slider.setMinimum(0)
        max_slider.setMaximum(len(x)-1)
        max_slider.setValue(len(x)-1)

        layout.addWidget(min_slider)
        layout.addWidget(max_slider)
        self.table.setCellWidget(row, 6, slider_widget)

        # Connect sliders
        min_slider.valueChanged.connect(lambda val, r=row, s_min=min_slider, s_max=max_slider: self.on_range_changed(r, s_min.value(), s_max.value()))
        max_slider.valueChanged.connect(lambda val, r=row, s_min=min_slider, s_max=max_slider: self.on_range_changed(r, s_min.value(), s_max.value()))

    def open_filter_dialog(self):
        dlg = FilterDialog(self, self.datasets)
        dlg.exec()

    def change_color(self, item):
        if item.column() == 3:
            color = QColorDialog.getColor()
            if color.isValid():
                row = item.row()
                self.datasets[row]["line"].set_color(color.name())
                item.setBackground(color)
                self.canvas.draw_idle()

    def update_plot_old(self):
        for row, ds in enumerate(self.datasets):
            vis = self.table.item(row, 4).checkState() == 2
            scale = float(self.table.item(row, 5).text())
            ds["line"].set_visible(vis)
            ds["line"].set_ydata(ds["y"] * scale)
        self.ax.relim()
        self.ax.autoscale()
        self.canvas.draw_idle()

    def update_plot(self):
        auto_scale_x = getattr(self, "auto_scale_x", False)
        x_min, x_max = float('inf'), float('-inf')

        for row, ds in enumerate(self.datasets):
            line = ds["line"]

            # --- Visibility ---
            visible_item = self.table.item(row, 4)
            visible = True
            if visible_item is not None:
                visible = visible_item.checkState() == Qt.CheckState.Checked
            line.set_visible(visible)
            ds["visible"] = visible

            # --- Y scaling ---
            yscale_item = self.table.item(row, 5)
            try:
                scale = float(yscale_item.text()) if yscale_item else 1.0
            except ValueError:
                scale = 1.0

            # --- Range selection (slider) ---
            idx_min = ds.get("range_min", 0)
            idx_max = ds.get("range_max", len(ds["x"]))
            x_data = np.array(ds["x"][idx_min:idx_max])
            y_data = np.array(ds["y"][idx_min:idx_max]) * scale
            line.set_data(x_data, y_data)

            # --- Auto-scale X uses full dataset, not slider-trimmed ---
            if auto_scale_x and visible:
                full_x = np.array(ds["x"])
                x_min = min(x_min, np.min(full_x))
                x_max = max(x_max, np.max(full_x))

        # --- Apply auto-scale X using full dataset ---
        if auto_scale_x and x_max > x_min:
            self.ax.set_xlim(x_min, x_max)

        # Recompute limits for Y and redraw
        self.ax.relim()
        self.ax.autoscale_view(scaley=True)  # autoscale only Y
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw_idle()



    def update_plotold(self):
        for row, ds in enumerate(self.datasets):
            line = ds["line"]

            # Visibility
            visible_item = self.table.item(row, 4)
            visible = True
            if visible_item is not None:
                visible = visible_item.checkState() == Qt.CheckState.Checked
            line.set_visible(visible)

            # Y scaling
            yscale_item = self.table.item(row, 5)
            try:
                scale = float(yscale_item.text()) if yscale_item else 1.0
            except ValueError:
                scale = 1.0

            line.set_ydata(np.array(ds["y"]) * scale)  # ensure numpy array

        self.ax.relim()
        self.ax.autoscale_view()
        self.ax.legend()
        self.canvas.draw_idle()

    def on_auto_scale_toggle(self):
        self.auto_scale_x = self.auto_scale_button.isChecked()
        if self.auto_scale_x:
            self.auto_scale_button.setStyleSheet("background-color: lightgreen")
            self.update_plot()  # immediately apply auto-scaling
        else:
            self.auto_scale_button.setStyleSheet("background-color: None")  # default

    def on_style_changed(self, row, style):
        line = self.datasets[row]['line']
        line.set_linestyle(style)
        self.canvas.draw()
    
    #to display the range 
    def on_range_changed(self, row, min_idx, max_idx):
        ds = self.datasets[row]
        x = ds["x"]
        y = ds["y"]

        # Clip to valid indices
        if min_idx >= max_idx:
            return

        new_x = x[min_idx:max_idx+1]
        new_y = y[min_idx:max_idx+1]
        ds["line"].set_data(new_x, new_y)
        self.canvas.draw()
    # -----------------------------
    # Math operations
    # -----------------------------
    def open_math_dialog(self):
        dialog = MathOpsDialog(self)
        if dialog.exec():
            expr = dialog.get_expression()
            self.apply_math_expr(expr)

    def apply_math_expr(self, expr):
        env = {}
        for i, ds in enumerate(self.datasets, 1):
            env[f"T{i}"] = {"x": ds["x"], "y": ds["y"]}

        safe_expr = expr.replace(".x", "['x']").replace(".y", "['y']")

        ref_x = self.datasets[0]["x"]
        interp_env = {}
        for key, val in env.items():
            if len(val["x"]) != len(ref_x) or not np.allclose(val["x"], ref_x):
                interp_y = np.interp(ref_x, val["x"], val["y"])
                interp_env[key] = {"x": ref_x, "y": interp_y}
            else:
                interp_env[key] = val

        safe_env = {
            "np": np,
            "exp": np.exp,
            "ln": np.log,
            "log": np.log,
            "power": np.power,
            "fft": np.fft.fft,
            "fftfreq": np.fft.fftfreq,
            "abs": np.abs
        }
        safe_env.update(interp_env)

        try:
            result_y = eval(safe_expr, safe_env, {})
            if isinstance(result_y, tuple) and len(result_y) == 2:
                result_x, result_y = result_y
            elif "fft" in safe_expr:
                n = len(ref_x)
                dx = ref_x[1] - ref_x[0]
                result_x = np.fft.fftfreq(n, d=dx)
            else:
                result_x = ref_x

            if not isinstance(result_y, np.ndarray):
                raise ValueError("Expression did not return array")
            if np.any(~np.isfinite(result_y)):
                raise ValueError("Result contains NaN/Inf values")
        except Exception as e:
            QMessageBox.critical(self, "Math Error", str(e))
            return

        self.add_dataset(result_x, result_y, label=expr)

    # -----------------------------
    # Axis scaling & grid
    # -----------------------------
    def toggle_logx(self, state):
        self.ax.set_xscale("log" if state else "linear")
        self.canvas.draw_idle()

    def toggle_logy(self, state):
        self.ax.set_yscale("log" if state else "linear")
        self.canvas.draw_idle()

    def _toggle_grid(self, state):
        self.ax.grid(state, linestyle=self.grid_style.currentText())
        self.canvas.draw_idle()

    def _update_grid_style(self, style):
        self.ax.grid(self.grid_checkbox.isChecked(), linestyle=style)
        self.canvas.draw_idle()

    def update_range(self, row):
        ds = self.datasets[row]
        min_idx = self.table.cellWidget(row, 6).min_slider.value()
        max_idx = self.table.cellWidget(row, 6).max_slider.value()
        min_idx = min(min_idx, len(ds['x'])-1)
        max_idx = max(max_idx, min_idx)
        
        new_x = ds['x'][min_idx:max_idx+1]
        new_y = ds['y'][min_idx:max_idx+1]
        ds['line'].set_data(new_x, new_y)

        if self.auto_scale_x:
            self.ax.set_xlim(new_x[0], new_x[-1])  # adjust x-axis automatically

        self.ax.relim()
        self.ax.autoscale_view(scalex=not self.auto_scale_x, scaley=True)
        self.canvas.draw()


    # -----------------------------
    # Wheel zoom
    # -----------------------------
    def _connect_zoom(self):
        def zoom(event):
            if event.inaxes is None:
                return
            ax = event.inaxes
            scale_factor = 1.2 if event.button == 'up' else 0.8
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            xdata, ydata = event.xdata, event.ydata
            new_width = (xlim[1] - xlim[0]) * scale_factor
            new_height = (ylim[1] - ylim[0]) * scale_factor
            ax.set_xlim([xdata - new_width/2, xdata + new_width/2])
            ax.set_ylim([ydata - new_height/2, ydata + new_height/2])
            self.canvas.draw_idle()
        self.canvas.mpl_connect("scroll_event", zoom)

    # -----------------------------
    # Table toggle
    # -----------------------------
    def toggle_table(self, state):
        if state:
            self.table.hide()
            self.toggle_table_btn.setText("Show Table")
        else:
            self.table.show()
            self.toggle_table_btn.setText("Hide Table")


    def on_table_item_changed(self, item):
        row = item.row()
        col = item.column()

        # Visibility toggle
        if col == 4:
            line = self.datasets[row]['line']
            line.set_visible(item.checkState() == Qt.CheckState.Checked)
            self.canvas.draw()
        
    # Method to handle renaming
    def on_table_name_changed(self, row, column):
        if column == 0:  # Name column
            new_name = self.table.item(row, column).text()
            # Update internal dataset name
            self.datasets[row]['name'] = new_name
            
            # Update the line's label in the plot
            self.datasets[row]['line'].set_label(new_name)
            
            # Refresh the legend
            self.ax.legend()
            self.canvas.draw()  

# -----------------------------
# Main entry
# -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DataPlotWidget()
    win.resize(1200, 800)
    win.show()
    sys.exit(app.exec())
