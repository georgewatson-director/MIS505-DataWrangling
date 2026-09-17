"""
Prompt:
The application [pandas_dataframe_gui.py] needs a help feature.  Add a main menu bar drop down menu to provide instructions
using the features you included.  Menu selections for each tab in the tab frame would work well.

Author: George Keith Watson
Date Started:   August 9, 2026
Code Generator: Claude.ai

"""
import sys
import traceback

import pandas as pd
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, QSortFilterProxyModel
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTableView, QTabWidget, QPushButton, QLabel, QLineEdit, QComboBox,
    QFileDialog, QMessageBox, QListWidget, QAbstractItemView, QGroupBox,
    QSpinBox, QCheckBox, QSplitter, QTextEdit, QToolBar, QAction, QStatusBar,
    QHeaderView, QDialog, QDialogButtonBox
)


# --------------------------------------------------------------------------- #
# Table model that lets a pandas DataFrame back a QTableView
# --------------------------------------------------------------------------- #
class PandasModel(QAbstractTableModel):
    """A read-only Qt table model wrapping a pandas DataFrame."""

    def __init__(self, df: pd.DataFrame = None, parent=None):
        super().__init__(parent)
        self._df = df if df is not None else pd.DataFrame()

    def set_dataframe(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def dataframe(self) -> pd.DataFrame:
        return self._df

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._df.index)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role in (Qt.DisplayRole, Qt.EditRole):
            value = self._df.iat[index.row(), index.column()]
            if pd.isna(value):
                return ""
            return str(value)
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return str(self._df.index[section])

    def sort(self, column, order=Qt.AscendingOrder):
        if self._df.empty or column >= len(self._df.columns):
            return
        colname = self._df.columns[column]
        self.layoutAboutToBeChanged.emit()
        self._df = self._df.sort_values(
            by=colname, ascending=(order == Qt.AscendingOrder), kind="mergesort"
        )
        self.layoutChanged.emit()


# --------------------------------------------------------------------------- #
# Matplotlib canvas widget
# --------------------------------------------------------------------------- #
class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 4), tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

    def clear(self):
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)


# --------------------------------------------------------------------------- #
# Simple scrollable help dialog
# --------------------------------------------------------------------------- #
class HelpDialog(QDialog):
    def __init__(self, title, body_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(560, 480)

        layout = QVBoxLayout(self)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(body_html)
        layout.addWidget(text)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


# --------------------------------------------------------------------------- #
# Main window
# --------------------------------------------------------------------------- #
class DataFrameExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pandas DataFrame Explorer")
        self.resize(1300, 850)

        self.df_original: pd.DataFrame = pd.DataFrame()   # data as loaded
        self.df_current: pd.DataFrame = pd.DataFrame()    # after filtering

        self._build_toolbar()
        self._build_central_widget()
        self._build_statusbar()
        self._build_menubar()

    # ---------------------------------------------------------------- UI --
    def _build_toolbar(self):
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        open_action = QAction("Open File...", self)
        open_action.triggered.connect(self.load_file)
        toolbar.addAction(open_action)

        save_action = QAction("Export Current View...", self)
        save_action.triggered.connect(self.export_file)
        toolbar.addAction(save_action)

        reset_action = QAction("Reset Filter", self)
        reset_action.triggered.connect(self.reset_filter)
        toolbar.addAction(reset_action)

    def _build_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("No data loaded.")

    def _build_central_widget(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(self._build_data_tab(), "Data / Sort / Filter")
        self.tabs.addTab(self._build_stats_tab(), "Descriptive Statistics")
        self.tabs.addTab(self._build_groupby_tab(), "GroupBy / Aggregate")
        self.tabs.addTab(self._build_pivot_tab(), "Pivot Table")
        self.tabs.addTab(self._build_viz_tab(), "Visualization")

    # ---- Menu bar / Help --------------------------------------------------
    def _build_menubar(self):
        menubar = self.menuBar()

        # --- File menu (mirrors the toolbar so everything is discoverable
        # from the menu bar too) --------------------------------------
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open File...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_file)
        file_menu.addAction(open_action)

        export_action = QAction("&Export Current View...", self)
        export_action.setShortcut("Ctrl+S")
        export_action.triggered.connect(self.export_file)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # --- Help menu ---------------------------------------------------
        help_menu = menubar.addMenu("&Help")

        overview_action = QAction("Getting Started", self)
        overview_action.triggered.connect(self.show_help_overview)
        help_menu.addAction(overview_action)

        help_menu.addSeparator()

        data_action = QAction("Data / Sort / Filter tab", self)
        data_action.triggered.connect(lambda: self.show_help("data"))
        help_menu.addAction(data_action)

        stats_action = QAction("Descriptive Statistics tab", self)
        stats_action.triggered.connect(lambda: self.show_help("stats"))
        help_menu.addAction(stats_action)

        groupby_action = QAction("GroupBy / Aggregate tab", self)
        groupby_action.triggered.connect(lambda: self.show_help("groupby"))
        help_menu.addAction(groupby_action)

        pivot_action = QAction("Pivot Table tab", self)
        pivot_action.triggered.connect(lambda: self.show_help("pivot"))
        help_menu.addAction(pivot_action)

        viz_action = QAction("Visualization tab", self)
        viz_action.triggered.connect(lambda: self.show_help("viz"))
        help_menu.addAction(viz_action)

        help_menu.addSeparator()

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # ---- help content -------------------------------------------------
    HELP_TEXT = {
        "overview": """
            <h2>Pandas DataFrame Explorer &mdash; Getting Started</h2>
            <p>This application puts most of pandas' <code>DataFrame</code> functionality
            behind a graphical interface. The general workflow is:</p>
            <ol>
                <li><b>File &rarr; Open File...</b> (or the toolbar button) to load a
                    CSV, Excel (.xlsx/.xls), or JSON file.</li>
                <li>Use the <b>Data / Sort / Filter</b> tab to inspect and narrow down
                    your data.</li>
                <li>Switch between the other tabs to compute statistics, group and
                    aggregate, build pivot tables, or create charts &mdash; each tab
                    works off of whatever rows are currently showing (i.e. your
                    active filter, if any).</li>
                <li><b>File &rarr; Export Current View...</b> saves the currently
                    filtered data back out to CSV or Excel.</li>
            </ol>
            <p>Open the <b>Help</b> menu and pick a tab name at any time for
            instructions specific to that tab.</p>
        """,
        "data": """
            <h2>Data / Sort / Filter</h2>
            <p>This is the main table view of your data.</p>
            <h3>Sorting</h3>
            <p>Click any column header to sort by that column. Click it again to
            reverse the sort order.</p>
            <h3>Filtering</h3>
            <p>Type a pandas <code>DataFrame.query()</code> expression into the
            filter box and click <b>Apply Filter</b> (or press Enter). Examples:</p>
            <ul>
                <li><code>age &gt; 30</code></li>
                <li><code>city == 'New York'</code></li>
                <li><code>age &gt; 30 and city == 'New York'</code></li>
                <li><code>sales &gt;= 1000 or region == 'West'</code></li>
            </ul>
            <p>Column names with spaces or special characters need backticks,
            e.g. <code>`unit price` &gt; 5</code>.</p>
            <p>Click <b>Clear</b> (or the toolbar's <b>Reset Filter</b> button) to
            go back to the full, unfiltered dataset.</p>
            <p><i>Every other tab operates on the currently filtered data, so
            filter first if you want statistics, groupings, pivots, or charts to
            reflect a subset of rows.</i></p>
        """,
        "stats": """
            <h2>Descriptive Statistics</h2>
            <p>Computes summary statistics for the current data, equivalent to
            pandas' <code>DataFrame.describe()</code>.</p>
            <p>Choose what to include from the dropdown:</p>
            <ul>
                <li><b>numeric columns only</b> &mdash; count, mean, std, min,
                    quartiles, max</li>
                <li><b>all columns</b> &mdash; numeric stats plus counts/unique/top/
                    freq for text columns</li>
                <li><b>object (text) columns only</b> &mdash; count, unique, top,
                    freq for text/categorical columns</li>
            </ul>
            <p>Click <b>Compute describe()</b> to run it. The panel below the table
            also shows the DataFrame's shape, each column's dtype, and how many
            missing (null) values each column has.</p>
        """,
        "groupby": """
            <h2>GroupBy / Aggregate</h2>
            <p>Equivalent to pandas' <code>DataFrame.groupby(...).agg(...)</code>.</p>
            <ol>
                <li>In <b>Group by column(s)</b>, select one or more columns to
                    group on (Ctrl+Click or Shift+Click to select multiple).</li>
                <li>In <b>Aggregate column(s)</b>, select the column(s) you want
                    to summarize. If you leave this empty, every remaining column
                    is aggregated.</li>
                <li>Pick an <b>aggregation function</b>: mean, sum, count, median,
                    min, max, std, var, nunique, first, or last.</li>
                <li>Click <b>Run GroupBy</b>. The result table shows one row per
                    group.</li>
            </ol>
        """,
        "pivot": """
            <h2>Pivot Table</h2>
            <p>Equivalent to pandas' <code>pd.pivot_table()</code>.</p>
            <ul>
                <li><b>Index (rows)</b> &mdash; the column whose unique values
                    become the pivot table's rows.</li>
                <li><b>Columns</b> &mdash; (optional) the column whose unique
                    values are spread across new columns.</li>
                <li><b>Values</b> &mdash; the column being summarized in the
                    table's cells.</li>
                <li><b>Aggregation</b> &mdash; how values are combined for each
                    index/column combination (mean, sum, count, etc.).</li>
                <li><b>Show totals (margins)</b> &mdash; adds row/column totals,
                    similar to Excel's grand totals.</li>
            </ul>
            <p>Click <b>Build Pivot Table</b> to generate it.</p>
        """,
        "viz": """
            <h2>Visualization</h2>
            <p>Creates a chart from the current data using pandas' built-in
            plotting (backed by matplotlib).</p>
            <ul>
                <li><b>Chart type</b> &mdash; line, bar, barh, hist, box, scatter,
                    area, pie, or kde.</li>
                <li><b>X column</b> / <b>Y column</b> &mdash; which columns to
                    plot. Some chart types only need one of the two:
                    <ul>
                        <li><b>hist</b> / <b>kde</b> &mdash; uses Y if set,
                            otherwise X.</li>
                        <li><b>box</b> &mdash; uses Y as the column to summarize.</li>
                        <li><b>pie</b> &mdash; groups by X and sums Y (or, if Y is
                            blank, shows value counts of X).</li>
                        <li><b>scatter</b> &mdash; needs both X and Y (numeric).</li>
                    </ul>
                </li>
                <li><b>Bins</b> &mdash; number of histogram bins (histogram only).</li>
            </ul>
            <p>Click <b>Plot</b> to draw the chart. Use the toolbar above the chart
            to pan, zoom, or save the image to a file.</p>
        """,
    }

    def show_help_overview(self):
        dlg = HelpDialog("Getting Started", self.HELP_TEXT["overview"], self)
        dlg.exec_()

    def show_help(self, key):
        titles = {
            "data": "Help \u2014 Data / Sort / Filter",
            "stats": "Help \u2014 Descriptive Statistics",
            "groupby": "Help \u2014 GroupBy / Aggregate",
            "pivot": "Help \u2014 Pivot Table",
            "viz": "Help \u2014 Visualization",
        }
        dlg = HelpDialog(titles[key], self.HELP_TEXT[key], self)
        dlg.exec_()

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "Pandas DataFrame Explorer\n\n"
            "A PyQt5 GUI exposing common pandas DataFrame operations: "
            "sorting, filtering, descriptive statistics, group-by/aggregate, "
            "pivot tables, and charting.",
        )

    # ---- Tab 1: Data / Sort / Filter -------------------------------------
    def _build_data_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        filter_box = QGroupBox("Filter (pandas DataFrame.query() syntax, e.g.  age > 30 and city == 'NY')")
        filter_layout = QHBoxLayout(filter_box)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Enter a query expression and press Apply...")
        self.filter_edit.returnPressed.connect(self.apply_filter)
        apply_btn = QPushButton("Apply Filter")
        apply_btn.clicked.connect(self.apply_filter)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.reset_filter)
        filter_layout.addWidget(self.filter_edit)
        filter_layout.addWidget(apply_btn)
        filter_layout.addWidget(clear_btn)
        layout.addWidget(filter_box)

        self.data_table = QTableView()
        self.data_model = PandasModel()
        self.data_table.setModel(self.data_model)
        self.data_table.setSortingEnabled(True)  # click header to sort
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.data_table.setAlternatingRowColors(True)
        layout.addWidget(self.data_table)

        return w

    # ---- Tab 2: Descriptive statistics -----------------------------------
    def _build_stats_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        controls = QHBoxLayout()
        self.stats_include_combo = QComboBox()
        self.stats_include_combo.addItems(["numeric columns only", "all columns", "object (text) columns only"])
        refresh_btn = QPushButton("Compute describe()")
        refresh_btn.clicked.connect(self.compute_stats)
        controls.addWidget(QLabel("Include:"))
        controls.addWidget(self.stats_include_combo)
        controls.addWidget(refresh_btn)
        controls.addStretch()
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Vertical)

        self.stats_table = QTableView()
        self.stats_model = PandasModel()
        self.stats_table.setModel(self.stats_model)
        splitter.addWidget(self.stats_table)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlaceholderText("Shape, dtypes and null counts will appear here.")
        splitter.addWidget(self.info_text)

        layout.addWidget(splitter)
        return w

    # ---- Tab 3: GroupBy / Aggregate --------------------------------------
    def _build_groupby_tab(self):
        w = QWidget()
        layout = QHBoxLayout(w)

        controls = QGroupBox("GroupBy settings")
        controls.setMaximumWidth(320)
        form = QVBoxLayout(controls)

        form.addWidget(QLabel("Group by column(s):"))
        self.gb_group_list = QListWidget()
        self.gb_group_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        form.addWidget(self.gb_group_list)

        form.addWidget(QLabel("Aggregate column(s):"))
        self.gb_agg_list = QListWidget()
        self.gb_agg_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        form.addWidget(self.gb_agg_list)

        form.addWidget(QLabel("Aggregation function:"))
        self.gb_func_combo = QComboBox()
        self.gb_func_combo.addItems(
            ["mean", "sum", "count", "median", "min", "max", "std", "var", "nunique", "first", "last"]
        )
        form.addWidget(self.gb_func_combo)

        run_btn = QPushButton("Run GroupBy")
        run_btn.clicked.connect(self.run_groupby)
        form.addWidget(run_btn)
        form.addStretch()

        layout.addWidget(controls)

        self.gb_table = QTableView()
        self.gb_model = PandasModel()
        self.gb_table.setModel(self.gb_model)
        layout.addWidget(self.gb_table)

        return w

    # ---- Tab 4: Pivot table ----------------------------------------------
    def _build_pivot_tab(self):
        w = QWidget()
        layout = QHBoxLayout(w)

        controls = QGroupBox("Pivot table settings (DataFrame.pivot_table)")
        controls.setMaximumWidth(320)
        form = QFormLayout(controls)

        self.pv_index_combo = QComboBox()
        self.pv_columns_combo = QComboBox()
        self.pv_values_combo = QComboBox()
        self.pv_aggfunc_combo = QComboBox()
        self.pv_aggfunc_combo.addItems(["mean", "sum", "count", "median", "min", "max", "std", "var"])
        self.pv_margins_check = QCheckBox("Show totals (margins)")

        form.addRow("Index (rows):", self.pv_index_combo)
        form.addRow("Columns:", self.pv_columns_combo)
        form.addRow("Values:", self.pv_values_combo)
        form.addRow("Aggregation:", self.pv_aggfunc_combo)
        form.addRow(self.pv_margins_check)

        run_btn = QPushButton("Build Pivot Table")
        run_btn.clicked.connect(self.run_pivot)
        form.addRow(run_btn)

        layout.addWidget(controls)

        self.pivot_table_view = QTableView()
        self.pivot_model = PandasModel()
        self.pivot_table_view.setModel(self.pivot_model)
        layout.addWidget(self.pivot_table_view)

        return w

    # ---- Tab 5: Visualization ---------------------------------------------
    def _build_viz_tab(self):
        w = QWidget()
        layout = QHBoxLayout(w)

        controls = QGroupBox("Chart settings")
        controls.setMaximumWidth(320)
        form = QFormLayout(controls)

        self.viz_kind_combo = QComboBox()
        self.viz_kind_combo.addItems(
            ["line", "bar", "barh", "hist", "box", "scatter", "area", "pie", "kde"]
        )
        self.viz_x_combo = QComboBox()
        self.viz_y_combo = QComboBox()
        self.viz_y_combo.setEditable(False)
        self.viz_bins_spin = QSpinBox()
        self.viz_bins_spin.setRange(2, 200)
        self.viz_bins_spin.setValue(20)

        form.addRow("Chart type:", self.viz_kind_combo)
        form.addRow("X column:", self.viz_x_combo)
        form.addRow("Y column (numeric):", self.viz_y_combo)
        form.addRow("Bins (for histogram):", self.viz_bins_spin)

        plot_btn = QPushButton("Plot")
        plot_btn.clicked.connect(self.run_plot)
        form.addRow(plot_btn)
        form.addRow(QLabel("Tip: for pie/hist/kde/box only\none column is generally needed."))

        layout.addWidget(controls)

        plot_area = QVBoxLayout()
        self.canvas = PlotCanvas(self)
        self.nav_toolbar = NavigationToolbar(self.canvas, self)
        plot_area.addWidget(self.nav_toolbar)
        plot_area.addWidget(self.canvas)
        plot_widget = QWidget()
        plot_widget.setLayout(plot_area)
        layout.addWidget(plot_widget)

        return w

    # ------------------------------------------------------------ actions --
    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open data file", "", "Data files (*.csv *.xlsx *.xls *.json);;All files (*)"
        )
        if not path:
            return
        try:
            if path.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(path)
            elif path.lower().endswith(".json"):
                df = pd.read_json(path)
            else:
                df = pd.read_csv(path)
        except Exception as exc:
            QMessageBox.critical(self, "Error loading file", f"{exc}\n\n{traceback.format_exc()}")
            return

        self.df_original = df
        self.df_current = df.copy()
        self.filter_edit.clear()
        self._refresh_all_views()
        self.status.showMessage(f"Loaded '{path}'  —  shape={df.shape}")

    def export_file(self):
        if self.df_current.empty:
            QMessageBox.information(self, "Nothing to export", "Load some data first.")
            return
        path, filt = QFileDialog.getSaveFileName(
            self, "Export current data view", "", "CSV (*.csv);;Excel (*.xlsx)"
        )
        if not path:
            return
        try:
            if path.lower().endswith(".xlsx") or "Excel" in filt:
                if not path.lower().endswith(".xlsx"):
                    path += ".xlsx"
                self.df_current.to_excel(path, index=False)
            else:
                if not path.lower().endswith(".csv"):
                    path += ".csv"
                self.df_current.to_csv(path, index=False)
            self.status.showMessage(f"Exported to {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    def apply_filter(self):
        if self.df_original.empty:
            return
        expr = self.filter_edit.text().strip()
        if not expr:
            self.reset_filter()
            return
        try:
            filtered = self.df_original.query(expr)
        except Exception as exc:
            QMessageBox.warning(self, "Invalid filter expression", str(exc))
            return
        self.df_current = filtered
        self.data_model.set_dataframe(self.df_current)
        self.status.showMessage(f"Filter applied — {len(filtered)} rows match out of {len(self.df_original)}")

    def reset_filter(self):
        if self.df_original.empty:
            return
        self.filter_edit.clear()
        self.df_current = self.df_original.copy()
        self.data_model.set_dataframe(self.df_current)
        self.status.showMessage(f"Filter cleared — {len(self.df_current)} rows")

    def _refresh_all_views(self):
        df = self.df_current
        self.data_model.set_dataframe(df)

        cols = list(df.columns)
        for combo in (self.pv_index_combo, self.pv_columns_combo, self.pv_values_combo,
                      self.viz_x_combo, self.viz_y_combo):
            combo.clear()
            combo.addItems(cols)

        self.gb_group_list.clear()
        self.gb_group_list.addItems(cols)
        self.gb_agg_list.clear()
        self.gb_agg_list.addItems(cols)

        self.stats_model.set_dataframe(pd.DataFrame())
        self.info_text.clear()
        self.gb_model.set_dataframe(pd.DataFrame())
        self.pivot_model.set_dataframe(pd.DataFrame())
        self.canvas.clear()
        self.canvas.draw()

        self.compute_stats()

    # ---- statistics --------------------------------------------------
    def compute_stats(self):
        df = self.df_current
        if df.empty:
            return
        choice = self.stats_include_combo.currentText()
        try:
            if choice == "numeric columns only":
                desc = df.describe()
            elif choice == "object (text) columns only":
                desc = df.describe(include=["object", "category"])
            else:
                desc = df.describe(include="all")
        except Exception as exc:
            QMessageBox.warning(self, "describe() failed", str(exc))
            return

        desc = desc.reset_index().rename(columns={"index": "statistic"})
        self.stats_model.set_dataframe(desc)

        info_lines = [
            f"Shape: {df.shape[0]} rows x {df.shape[1]} columns",
            "",
            "Dtypes:",
        ]
        for col, dt in df.dtypes.items():
            info_lines.append(f"  {col}: {dt}")
        info_lines.append("")
        info_lines.append("Null value counts:")
        for col, n in df.isna().sum().items():
            info_lines.append(f"  {col}: {n}")
        self.info_text.setPlainText("\n".join(info_lines))

    # ---- groupby -------------------------------------------------------
    def run_groupby(self):
        df = self.df_current
        if df.empty:
            return
        group_cols = [item.text() for item in self.gb_group_list.selectedItems()]
        agg_cols = [item.text() for item in self.gb_agg_list.selectedItems()]
        func = self.gb_func_combo.currentText()

        if not group_cols:
            QMessageBox.information(self, "Select group column(s)", "Pick at least one column to group by.")
            return
        if not agg_cols:
            agg_cols = [c for c in df.columns if c not in group_cols]

        try:
            result = df.groupby(group_cols)[agg_cols].agg(func).reset_index()
        except Exception as exc:
            QMessageBox.warning(self, "GroupBy failed", str(exc))
            return

        self.gb_model.set_dataframe(result)
        self.status.showMessage(f"GroupBy complete — {len(result)} groups")

    # ---- pivot -----------------------------------------------------------
    def run_pivot(self):
        df = self.df_current
        if df.empty:
            return
        index = self.pv_index_combo.currentText()
        columns = self.pv_columns_combo.currentText()
        values = self.pv_values_combo.currentText()
        aggfunc = self.pv_aggfunc_combo.currentText()
        margins = self.pv_margins_check.isChecked()

        if not index or not values:
            QMessageBox.information(self, "Missing selection", "Choose at least an index and a values column.")
            return
        try:
            pivot = pd.pivot_table(
                df,
                index=index,
                columns=columns if columns and columns != index else None,
                values=values,
                aggfunc=aggfunc,
                margins=margins,
            )
            pivot = pivot.reset_index()
        except Exception as exc:
            QMessageBox.warning(self, "Pivot failed", str(exc))
            return

        self.pivot_model.set_dataframe(pivot)
        self.status.showMessage("Pivot table built.")

    # ---- visualization -----------------------------------------------
    def run_plot(self):
        df = self.df_current
        if df.empty:
            return
        kind = self.viz_kind_combo.currentText()
        x = self.viz_x_combo.currentText()
        y = self.viz_y_combo.currentText()
        bins = self.viz_bins_spin.value()

        self.canvas.clear()
        ax = self.canvas.ax
        try:
            if kind == "hist":
                df[y if y else x].plot(kind="hist", bins=bins, ax=ax)
            elif kind == "kde":
                df[y if y else x].plot(kind="kde", ax=ax)
            elif kind == "box":
                df.boxplot(column=[y] if y else None, ax=ax)
            elif kind == "pie":
                series = df.groupby(x)[y].sum() if y else df[x].value_counts()
                series.plot(kind="pie", ax=ax, autopct="%1.1f%%")
            elif kind == "scatter":
                df.plot(kind="scatter", x=x, y=y, ax=ax)
            else:  # line, bar, barh, area
                df.plot(kind=kind, x=x if x else None, y=y if y else None, ax=ax)
            ax.set_title(f"{kind} chart")
            self.canvas.fig.tight_layout()
            self.canvas.draw()
        except Exception as exc:
            QMessageBox.warning(self, "Plot failed", str(exc))


def main():
    app = QApplication(sys.argv)
    win = DataFrameExplorer()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
