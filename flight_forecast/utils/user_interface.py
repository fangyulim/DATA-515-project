"""
This module constructs a two page user interface, links api calls and produce predictions.

The first page allows users to selection airport code, date, and if they want
a prediction of delay severity, or just delay prediction.

The second page allows admin to upload more data and retrain the model.
Comments: I ended up not putting state and airport name in option because
not all airports have a name.
"""
import csv
import sys
from datetime import datetime
from PyQt5 import uic   # , QtWidgets. This prevents errors
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
#  QHBoxLayout, QWidget, QPushButton, QVBoxLayout, QStackedWidget, QLabel,
from PyQt5.QtCore import Qt
from ..utils.weather import (get_weather_forecast)

# GUI file
QT_CREATOR_FILE = '../../resources/flight_delay_multi_page.ui'
ui_main_window, QtBaseClass = uic.loadUiType(QT_CREATOR_FILE)


class Milestone2V2(QMainWindow):
    """
    This class initializes the GUI and the widgets.
    """

    def __init__(self):
        """
        function documentation: This function sets up the windows and actions for specific changes
        """
        # super(Milestone2V2, self).__init__()
        super().__init__()
        self.user_int = ui_main_window()
        self.user_int.setupUi(self)
        self.setup_ui()

        self.user_int.admin_login_btn.clicked.connect(
            lambda: self.stacked_widget_pages.setCurrentIndex(1))
        self.user_int.main_page_btn.clicked.connect(
            lambda: self.stacked_widget_pages.setCurrentIndex(0))

        # Setting labels to be centered
        label_main_page = self.user_int.main_page_lb
        label_main_page.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        label_login_page = self.user_int.login_page_lb
        label_login_page.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        label_admin_page = self.user_int.admin_page_lb
        label_admin_page.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Instantiating widgets and functions used on main page.
        self.load_airport_list()
        # self.user_int.AirportSelection.currentTextChanged.connect(self.airport_changed)
        self.user_int.PredictButton.clicked.connect(self.prediction)

        # Authentication
        self.user_int.error_msg_lb.setVisible(False)
        self.user_int.login_btn.clicked.connect(self.authenticate)

        # Upload
        self.user_int.file_lb.setVisible(False)
        self.user_int.upload_btn.clicked.connect(self.upload_files)
        self.user_int.new_mod_lb.setVisible(False)
        self.user_int.mod_title_lb.setVisible(False)
        self.user_int.option_btn.setVisible(False)
        self.user_int.retrain_optionlb.setVisible(False)
        self.user_int.refit_lb.setVisible(False)

    def setup_ui(self):
        """
        This function sets up the UI.
        """
        width = 1200
        height = 750
        self.setFixedWidth(width)
        self.setFixedHeight(height)
        # Instantiated stacked widget and set default page to be main page(user).
        self.stacked_widget_pages = self.user_int.stacked_widget
        self.stacked_widget_pages.setCurrentIndex(0)
        self.user_int.avg_delay_result.setVisible(False)
        self.user_int.label_6.setVisible(False)
        self.user_int.prob_delay_result.setVisible(False)
        self.user_int.label_5.setVisible(False)

    def load_airport_list(self):
        """
        This function displays the list of airports in the dropdown bar.
        Currently, we are only using the list of airports in the pacific northwest.
        """
        # Couldn't figure out path.
        with open("../../resources/airport_codes.csv", "r", encoding="utf-8") as file:
            next(file)  # skips the header.
            airport_codes = [row[0] for row in csv.reader(file)]

        # Clear the existing items in AirportSelection widget
        self.user_int.AirportSelection.clear()

        # Adding airport names to the widget.
        self.user_int.AirportSelection.addItems(airport_codes)

    # def airport_changed(self):
    #     """
    #     This function is what happens when airport selection is changed.
    #     Here it should obtain data for the relative airport.
    #     Returns: airport code
    #     """
    #     # I'm just printing this out for now.
    #     # Thinking afterwards this might not be necessary.
    #     airport_selected =self.user_int.AirportSelection.currentText()
    #     print(airport_selected)
    #     return airport_selected

    def prediction(self):
        """
        This function processes input information and displays prediction
        """
        airport_selection = self.user_int.AirportSelection.currentText()

        date_selection = self.user_int.DateSelection.date().toString("yy.MM.dd")
        time_selection = self.user_int.TimeSelection.time().toString("HH:mm:ss")

        datetime_info = [
            date_selection.split(".")[0],  # year
            date_selection.split(".")[1],  # month
            date_selection.split(".")[2],  # day_of_month
            time_selection.split(":")[0],  # hour
            time_selection.split(":")[1],  # minute
            time_selection.split(":")[2]   # second
        ]

        # Weather needs time in seconds as integer.
        # Include airline.
        # temp print to test pylint
        print(datetime_info)
        # If selected day is within 15 days, then we are able to give a prediction

        current_date = datetime.now()
        qdate = self.user_int.DateSelection.date()
        date_selected = datetime(qdate.year(), qdate.month(), qdate.day())
        difference = current_date - date_selected
        if difference.days < 15:
            delay_prediction = airport_selection + date_selection + time_selection \
                               + " including the forecast weather"
        else:
            delay_prediction = airport_selection + date_selection + time_selection \
                               + " without the forecast weather"

        self.user_int.prob_delay_result.setVisible(True)
        self.user_int.label_5.setVisible(True)
        self.user_int.prob_delay_result.setText(delay_prediction)

        if self.user_int.EstimateCheckBox.isChecked():

            severity_prediction = airport_selection + date_selection + time_selection
            self.user_int.avg_delay_result.setText(severity_prediction)
            self.user_int.avg_delay_result.setVisible(True)
            self.user_int.label_6.setVisible(True)

        else:
            self.user_int.avg_delay_result.setVisible(False)
            self.user_int.label_6.setVisible(False)

    # Admin Page
    def authenticate(self):
        """
        This function checks if user is actually an admin and redirects to admin page
        if user is an admin.
        """
        password = self.user_int.password_input.text()
        if password == "pw123":
            self.stacked_widget_pages.setCurrentIndex(2)
        else:
            print("fail")
            self.user_int.error_msg_lb.setVisible(True)

    def upload_files(self):
        """
        This function allows users to upload files and triggers pipeline
        for data cleaning and model retraining.
        """
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        # Open the file dialog and get the selected file paths
        files, _ = file_dialog.getOpenFileNames(self, "Select Files", "", "All Files (*)")
        if files:
            folder_path = "/".join(files[0].split("/")[:-1])
            # temp print to test pylint
            print(folder_path)
            num_uploaded = len(files)
            self.user_int.file_lb.setText("You have uploaded " + str(num_uploaded) + " file(s).")
            self.user_int.file_lb.setVisible(True)

            # Call data collection + cleaning pipeline

            # Asking if user would like to refit the model.
            self.user_int.retrain_optionlb.setText("Would you like to replace the model? ")
            self.user_int.retrain_optionlb.setVisible(True)
            self.user_int.option_btn.setVisible(True)
            # Call model
            # Mock display
            self.user_int.new_mod_lb.setText("The new model training and testing accuracy is: \n")
            self.user_int.new_mod_lb.setVisible(True)
            self.user_int.mod_title_lb.setVisible(True)

            self.user_int.option_btn.accepted.connect \
                (lambda: self.user_int.refit_lb.setText("Replace model..."))
            self.user_int.option_btn.rejected.connect \
                (lambda: self.user_int.refit_lb.setText("Not replacing model."))
            # Refit
            # Can add a progress bar. When it hits 100% Display "Successfully retrained".

        else:
            self.user_int.file_lb.setText("No files have been uploaded.")
            self.user_int.file_lb.setVisible(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Milestone2V2()
    window.show()
    sys.exit(app.exec_())