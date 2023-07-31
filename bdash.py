import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
    QPlainTextEdit,
    QWidget,
    QCheckBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pd.options.mode.chained_assignment = None  # default='warn'
pd.options.display.max_rows = 4000


class BudgetAnalysisApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Check Yo Budget, Fool!")
        self.setGeometry(100, 100, 1000, 1000)

        # Load and clean the data from the CSV file
        self.load_data()
        self.clean_data()

        # Default to showing income data
        self.show_income = True

        self.create_widgets()

    def load_data(self):
        # Load the data from 'budget.csv' into a pandas DataFrame
        self.df = pd.read_csv(
            "budget.csv", sep=";", usecols=["Date", "Party", "Amount"]
        )

    def clean_data(self):
        # Clean and format the data in the DataFrame
        # change numbering format to english standard
        self.df["Amount"] = [
            x.strip().replace(".", "") for x in self.df["Amount"]
        ]
        self.df["Amount"] = [
            x.strip().replace(",", ".") for x in self.df["Amount"]
        ]

        # change from string to datetime
        self.df["Date"] = pd.to_datetime(self.df["Date"], format="%d.%m.%Y")
        # change from string to number in 5th column
        self.df[["Amount"]] = self.df[["Amount"]].apply(pd.to_numeric)
        # strip whitespace in 2nd column
        self.df["Party"] = self.df["Party"].str.strip()
        self.df["Party"] = self.df["Party"].fillna("data missing")

    def create_widgets(self):
        # Create QDateEdit widgets
        self.start_date_edit = QDateEdit()
        self.end_date_edit = QDateEdit()

        # Set the European date format for the QDateEdit widgets
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")

        # Set the default values for the QDateEdit widgets
        self.start_date_edit.setDate(self.df["Date"].min())
        self.end_date_edit.setDate(self.df["Date"].max())

        # Create a checkbox to toggle between income and expenses
        self.toggle_checkbox = QCheckBox("Show Income")
        self.toggle_checkbox.setChecked(self.show_income)
        self.toggle_checkbox.stateChanged.connect(self.toggle_show_income)

        # Create a button to trigger the slicing
        self.update_button = QPushButton("Update Data")
        self.update_button.clicked.connect(self.display_data)

        # Create a QPlainTextEdit widget to display output
        self.output_text_edit = QPlainTextEdit()
        self.output_text_edit.setReadOnly(True)

        # Layout for the widgets
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Start Date:"))
        layout.addWidget(self.start_date_edit)
        layout.addWidget(QLabel("End Date:"))
        layout.addWidget(self.end_date_edit)
        layout.addWidget(self.toggle_checkbox)
        layout.addWidget(self.update_button)
        layout.addWidget(QLabel("Output:"))
        layout.addWidget(self.output_text_edit)

        # Set the font for the QPlainTextEdit to a fixed-width font
        font = QFont("Courier")
        font.setPointSize(10)
        self.output_text_edit.setFont(font)

        # Create the 'Graphs' section
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(QLabel("Graphs:"))
        monthly_button = QPushButton("Monthly Gross")
        graph_layout.addWidget(monthly_button)
        monthly_button.clicked.connect(self.plot_monthly)

        # Add the 'Graphs' section to the main layout
        layout.addLayout(graph_layout)

        # Set the layout for the main window
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def display_data(self):
        # Display the data in the QPlainTextEdit
        self.output_text_edit.clear()

        sliced_df = self.slice_data()

        income_sliced, outgo_sliced = self.split_df(sliced_df)

        # Filter data based on the toggle (income or expenses)
        if self.show_income:
            filtered_df = income_sliced
        else:
            filtered_df = outgo_sliced

        # Get the DataFrame as a formatted string with fixed column widths
        formatted_text = filtered_df.to_string(
            index=False,
            col_space=12,
            justify="center",
        )

        # Display the formatted text in the QPlainTextEdit
        self.output_text_edit.setPlainText(formatted_text)
        self.output_text_edit.setPlainText(formatted_text)

    def slice_data(self):
        # Get the user-selected start and end dates as datetime64[ns] dtype
        start_date = pd.to_datetime(self.start_date_edit.date().toPyDate())
        end_date = pd.to_datetime(self.end_date_edit.date().toPyDate())

        # Call the slice_by_date function to filter the data within the date range
        sliced_df = self.slice_by_date(self.df, start_date, end_date)

        return sliced_df

    def slice_by_date(self, df, start_date, end_date):
        """returns a DataFrame subset in the range specified"""
        mask = (df["Date"] >= start_date) & (df["Date"] <= end_date)
        return df.loc[mask]

    def toggle_show_income(self, state):
        # Toggle the value of show_income based on checkbox state
        self.show_income = state == Qt.Checked
        if self.show_income:
            self.toggle_checkbox.setText("Show Income")
        else:
            self.toggle_checkbox.setText("Show Expenses")

    def split_df(self, df):
        """splits dataframe into income and outgo dataframes"""

        # income values are positive
        income_df = df[df["Amount"] > 0]

        # outgo values are negative
        outgo_df = df[df["Amount"] < 0]

        return income_df, outgo_df

    def list_months(self, df):
        """creates list of dataframes grouped by month"""

        # set index
        df = df.set_index("Date")

        # creates list of dataframes grouped by month
        list_of_months = [g for n, g in df.groupby(pd.Grouper(freq="M"))]

        return list_of_months

    def split_months(self, list_of_months):
        """splits each month in list into income and outgo"""

        months_income = []
        months_outgo = []

        for month in list_of_months:
            income, outgo = self.split_df(month)
            months_income.append(income)
            months_outgo.append(outgo)

        return months_income, months_outgo

    def plot_months(self, month_list):
        l = len(month_list)

        # Create a list of all available months in the month_list
        months = [
            month.strftime("%b")
            for month in pd.date_range(start="2023-01-01", periods=l, freq="M")
        ]

        expenditures = []

        for month in month_list:
            try:
                expenditures.append(month["Amount"].sum())
            except:
                expenditures.append(0)

        index = np.arange(l)

        # Adjust the bar width based on the number of available months
        bar_width = 0.8 / l

        plt.bar(index, [abs(i) for i in expenditures], width=bar_width)
        plt.xlabel("Months", fontsize=10)
        plt.ylabel("Euros (€) Spent", fontsize=10)
        plt.xticks(index, months, fontsize=8, rotation=30, ha="right")
        plt.title("Euro per Month")
        plt.tight_layout()
        plt.show()

    def plot_monthly(self):
        sliced_df = self.slice_data()

        month_list = self.list_months(sliced_df)

        # Call the plot_months function
        try:
            self.plot_months(month_list)
        except:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BudgetAnalysisApp()
    window.show()
    sys.exit(app.exec_())
