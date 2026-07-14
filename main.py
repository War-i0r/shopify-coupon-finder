import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QRadioButton, QButtonGroup, QPushButton, QLineEdit, QCheckBox, QSpacerItem
from PyQt5.QtWidgets import QBoxLayout, QVBoxLayout, QGridLayout, QHBoxLayout, QFrame, QScrollArea, QSizePolicy, QMessageBox, QErrorMessage
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5 import QtTest
from PyQt5.QtCore import QSize

from time import sleep;


# Selenium Imports

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *
import undetected_chromedriver as uc
# Json Imports
import json

#URl Parser
from urllib.parse import urlparse


# Regex
import re






# Code Colors

COLORS = {
    5 : "color:orange;",
    10 : "color:yellow",
    20 : "color:green;",
}

# Copyright 2026 Thomas Zimmerman #


class MainWindow(QMainWindow):

    def __init__(self, targets, browser):
        super().__init__()
        

        self.firstAutofill = True;
        self.browser : webdriver.Firefox = browser;
        self.targets = targets;
        self.prospects = {};
        self.protocols = {
            "www.hotdeals.com" : self._hotdeals,
            "simplycodes.com" : self._simplycodes
        }
        self.foundCodes = {}
        central_widget = QWidget()



        self.setCentralWidget(central_widget)
        self.setWindowTitle("Coupon Finder")
        self.setGeometry(700, 300, 500, 500)

        self.counter = 0;
        self.label1 = QLabel("Enter a search term and submit to find codes!", self)

        self.label1.setFont(QFont("Arial", 20))

        self.label1.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.searchQuery = QLineEdit(self)

        self.searchQuery.setGeometry(0, 0, 100, 50)

        self.searchQuery.setPlaceholderText("Search here...")

        self.searchFrame = QFrame()
        button1 = QPushButton("Initiate Search!", self.searchFrame)
        button1.clicked.connect(self.handle_click)

        vbox = QVBoxLayout(self.searchFrame)

        vbox.addWidget(self.label1)
        vbox.addWidget(self.searchQuery)
        vbox.addWidget(button1)
        

    

        hbox = QHBoxLayout();    

        central_widget.setLayout(hbox)



        self.results = QLabel("Resulting Codes:", self)
        self.results.setFont(QFont('Arial', 14))
        self.results.setAlignment(Qt.AlignmentFlag.AlignHCenter)

   
        
        self.resultScroll = QScrollArea()
        resultWidget = QWidget()
        self.resultContainer = QVBoxLayout()
        resultWidget.setLayout(self.resultContainer)

        self.resultScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.resultScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.resultScroll.setWidgetResizable(False)
        self.resultScroll.setWidget(resultWidget)

        self.resultFrame = QFrame(self)

        
        innerBoxLayout = QVBoxLayout(self.resultFrame)
        self.resultFrame.setMinimumSize(QSize(400, 100))
     
        innerBoxLayout.addWidget(self.results)
        innerBoxLayout.addWidget(self.resultScroll)

        self.autofillFrame = QFrame(self)
        autoFrameLayout = QHBoxLayout(self.autofillFrame)

        autoFrameLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.autofillFrame.setMinimumSize(QSize(400, 10))

        self.autofillButton = QPushButton("Check Codes", self.autofillFrame)
        self.autofillButton.setEnabled(False)

        self.autofillButton.clicked.connect(self._autofill)

        self.autofillStatus = QLabel("Click 'Check Codes' to check the found codes for their authenticity. (You must have searched for some first)", self.autofillFrame)
        self.autofillStatus.setWordWrap(True)
        self.autofillStatus.setAlignment(Qt.AlignmentFlag.AlignHCenter)


        self.stopOnFirstFrame = QFrame(self)
        stopOnFirstLayout = QVBoxLayout(self.stopOnFirstFrame)
        stopOnFirstLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stopOnFirst = QCheckBox(self.stopOnFirstFrame)


        self.stopOFLabel = QLabel("Stop on first valid code?")

        stopOnFirstLayout.addWidget(self.stopOFLabel)
        stopOnFirstLayout.addWidget(self.stopOnFirst)

        self.stopOnFirstFrame.setLayout(stopOnFirstLayout)



        autoFrameLayout.addWidget(self.autofillStatus)
        autoFrameLayout.addSpacerItem(QSpacerItem(50, 50, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        autoFrameLayout.addWidget(self.autofillButton)
        autoFrameLayout.addSpacerItem(QSpacerItem(50, 50, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        autoFrameLayout.addWidget(self.stopOnFirstFrame)


        innerBoxLayout.addWidget(self.autofillFrame)
        hbox.addWidget(self.searchFrame)
        hbox.addWidget(self.resultFrame)

        # testing the qss system
        self.autofillFrame.setObjectName("autofillFrame")
        self.resultFrame.setObjectName("resultFrame")
        self.autofillButton.setObjectName("autofillButton")
        self.autofillStatus.setObjectName("autofillStats")

    

    def _determine_discount(self):
        # find the old price
        oldPrice = self.browser.find_element(By.CSS_SELECTOR, "div > s").text
        # format old price to a float
        oldPrice = float(oldPrice.replace("$", ""))
        # to find the amount saved, use strong[translate="no"]
        actualSaved = self.browser.find_element(By.CSS_SELECTOR, 'strong[translate="no"]').text
        # format actual saved to a float
        actualSaved = float(actualSaved.replace("$", ""))
        return round((actualSaved/oldPrice)*100.0, 2)
    
    def _clear_element(self, element):
        element.send_keys(Keys.CONTROL, "a");
        element.send_keys(Keys.DELETE)

    def _apply_style(self, element, s):
        self.browser.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, s)
    # Autofill Feature
    def _autofill(self):
        if (self.firstAutofill):
            diag = QMessageBox()
            diag.setWindowTitle("Alert")
            diag.setText("NOTE: This assumes that you have completed the following steps:\n\nOpened the relevant Shopify page for your target company within the popup browser\nAdded any item\nProceeded to the checkout page\nOpened the discount code text box.\nIf this is not done, this will fail. Make sure the only open tab is the shopify page.")
            diag.setIcon(QMessageBox.Icon.Question)
            diag.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel);
            diag.exec()
            self._info_dialog("You must only have ONE tab open, which should have your company's checkout page. Failure to do this will result in a crash.", QMessageBox.Icon.Critical)
            self.firstAutofill = False;
        else:
            # Re-Check to make sure we're on only the first tab
            self.browser.switch_to.window(list(self.browser.window_handles)[0])
            # Highlight the boxes we are targeting
            inputBox = self.browser.find_element(By.CSS_SELECTOR, "[id^='ReductionsInput']:not([id$='label'])")
            self._apply_style(inputBox, 'border:10px solid yellow; background-color:yellow;')
            button = self.browser.find_element(By.CSS_SELECTOR, "[data-event-name='apply_discount']")
            self._apply_style(button, 'border:10px solid yellow; background-color:yellow;')


            # change wait to five seconds to find element, as discounts take a while for Shopify discounts to load on the first go
            self.browser.implicitly_wait(5)
            working_codes = []
            to_remove = []
            for code, discount in self.foundCodes.items():
                QtTest.QTest.qWait(500)
                self._auto_type(inputBox, code)
                codeWorkedNormal = False;
                self._click_button(button)
                if (self._element_exists([By.CSS_SELECTOR, "[aria-label='Remove "+code+"']"])):
                    working_codes.append(code)
                    actualDiscount = self._determine_discount();
           
                    self.foundCodes[code] = actualDiscount

                    # find the "remove" button for the active code
                    removeButton = self.browser.find_element(By.CSS_SELECTOR, "[aria-label='Remove "+code+"']>span>svg>use")
                    self._click_button(removeButton)
                else:
                    # the code did not work, queue it to be removed
                    to_remove.append(code)
                
                

                """
                if (not codeWorkedNormal and self._element_exists([By.CSS_SELECTOR, "div > div > div > span > strong"])):
                    working_codes.append(code)
                    # we must press the button to close this dialog for later, when we're testing other codes
                    closeButton = self._find_element([By.CSS_SELECTOR, "div > div > div > button[aria-label='Close']"])
                    self._click_button(closeButton)
                """
                QtTest.QTest.qWait(1000)
                self._clear_element(inputBox)
                
                if (self.stopOnFirst.isChecked() and len(working_codes) == 1):
                    break
                elif(len(working_codes) == 1):
                    # change implicit wait back to 2 seconds, as the first has now loaded
                    self.browser.implicitly_wait(2)


            # remove the bad codes
            for code in to_remove:
                self.foundCodes.pop(code)
            
            # re-sort self.foundCodes
            oldData = self.foundCodes
            self.foundCodes = self._sort_dict_by_value(self.foundCodes)

            alertMessage = "These are the following codes which worked, and the discounts they gave:\n"
            for code, discount in self.foundCodes.items():
                if code in working_codes:
                    alertMessage += code + ", at a " + str(discount) + "% discount!\n" 
            if len(working_codes) == 0:
                alertMessage = "No valid discount codes found... Sorry!"
            self._update_code_ui(self.foundCodes)
            self._info_dialog(alertMessage, QMessageBox.Icon.Information)
            

    def _click_button(self, element):
        try:
            element.click(); 
            return True
        except ElementClickInterceptedException:
            return False

    def _element_exists(self, selectionArray):
        try:
            self.browser.find_element(selectionArray[0], selectionArray[1])
            return True;
        except NoSuchElementException:
            return False;      
    def _find_element(self, selectionArray):
        try:
            return self.browser.find_element(selectionArray[0], selectionArray[1])
        except NoSuchElementException:
            return False;      

    def _info_dialog(self, message, icon : QMessageBox.Icon = QMessageBox.Icon.Information):
        diag = QMessageBox()
        diag.setWindowTitle("Complete!")
        diag.setText(message)
        diag.setIcon(icon)
        diag.setStandardButtons(QMessageBox.StandardButton.Ok);
        diag.exec()

    def _auto_type(self, target, text):
        self._clear_element(target)
        QtTest.QTest.qWait(250)
        target.send_keys(text)




    def _merge_codes(self, foundCodes):
        allCodes = {}
        for prospect in foundCodes.keys():
            for code, item in foundCodes[prospect].items():
                allCodes[code] = item
        return self._sort_dict_by_value(allCodes)


    def _update_code_ui(self, foundCodes : dict):
        self.resultContainer = QVBoxLayout();
        # now empty
        newResultWidget = QWidget()
        newResultWidget.setLayout(self.resultContainer)
        for code, percentOff in foundCodes.items():
            newLabel = QLabel(self)
            newLabel.setFont(QFont('Arial', 10, 100, False))
            newLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            newLabel.setText(f"{code} : {percentOff}")
            newLabel.setGeometry(int((self.resultFrame.rect().width() / 2) - newLabel.rect().width()), 0, newLabel.rect().width(), 80)
            newLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            for value, style in COLORS.items():
                if (percentOff == "unproven"):
                    newLabel.setStyleSheet("color:#FFFFFF;")
                    newLabel.setText(f"{code} : Unknown")
                elif (percentOff >= value):
                    newLabel.setStyleSheet(style)
            newLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.resultContainer.addWidget(newLabel)
        self.resultScroll.setWidget(newResultWidget)
        self.firstAutofill = True;
    

    def _process_query(self, query) -> str:
        newQuery = "?q="
        splitQuery = query.split(" ")
        count = 0
        for fragment in splitQuery:
            count += 1
            newQuery += fragment
            if (count != 0 and count != len(splitQuery)):
                newQuery += "+"

        return newQuery
    
    def handle_click(self):
        self.prospects = {};
        self.foundCodes = {};
        self.label1.setText("Searching...")
        # initiate the search
        search_query = self._process_query(self.searchQuery.text())
        self.browser.get("https://duckduckgo.com/" + search_query + "+coupon+codes")

        # Go through the first few links on the page
        self._search_for_targets();
        self.autofillButton.setEnabled(True)
        

    def _find_percentage(self, dealTitle):
        
        # Very complex regex expression, this just finds any digit percentages in text
        return re.findall(r'([0-9]*\.?[0-9]*)\s*%', dealTitle)

    def _search_for_codes(self, target):
        try:
            possible_codes = self.protocols[target]()
            discovered_codes = {}
            for i in range(len(possible_codes[0])):
                codeContent = possible_codes[0][i]
                discovered_codes[codeContent] = "unproven"

            return discovered_codes
        except:
            return {}
        
        

    def _sort_dict_by_value(self, oldDict):
        newDict = dict(sorted(oldDict.items(), key=lambda item: item[1]))
        newDict = dict(reversed(newDict.items()))
        return newDict

    def _search_for_targets(self):
        elements = self.browser.find_elements(By.CSS_SELECTOR, "a")
        count = 0
        foundCodes = {}

        for element in elements:
            if (count < 10):
                content = element.text
                link = element.get_attribute("href")
                root = urlparse(link).netloc
                if (content == "" or root=="duckduckgo.com"):
                    continue
                    

                if (root in self.targets):
                    self.prospects[link] = [element, element.text]
        
        self.label1.setText("Found sites: " + str(len(self.prospects)))

        for prospect in self.prospects:
            root = urlparse(prospect).netloc
            foundCodes[root] = {}

            self.browser.get(prospect)
            codes = self._search_for_codes(root);

            for code in codes.keys():
                foundCodes[root][code] = codes[code]

            oldData = foundCodes[root]
            # sort all our found codes by value so it's nicer on the user
            foundCodes[root] = self._sort_dict_by_value(oldData)
        # Codes were sorted through
        allCodes  = self._merge_codes(foundCodes)

        self.foundCodes = allCodes
        self._update_code_ui(allCodes)
        self._info_dialog("Actual discounts can be discovered by using the 'Check Codes' button.")

        
            


    # site-specific code finders
    def _hotdeals(self):
        return [[code.text for code in self.browser.find_elements(By.CSS_SELECTOR, ".offer-card-btn-code")], [offer.text for offer in self.browser.find_elements(By.CSS_SELECTOR, ".offer-title")]]
    
    def _simplycodes(self):
        # this requires much more of a methodical approach, the codes are not raw pasted into the site
        results = [[], []]
        # has a "show more" button that repeatedly appears near the bottom, lets click multiple times
        ###
        """
        for i in range(100):
            try:
                click_more = self.browser.find_element(By.ID, "codes-show-more")
                ActionChains(self.browser).scroll_to_element(click_more).perform()
                QtTest.QTest.qWait(2000)
                click_more.click()
            except ElementNotInteractableException:
                print("we found all visible codes")
                break
        """
        # get the original handle so we don't stray too far away
        original_handle = self.browser.current_window_handle
        original_url = self.browser.current_url
        all_code_buttons = self.browser.find_elements(By.CLASS_NAME, "copy-coupon")

        num_buttons = len(all_code_buttons)
        for i in range(num_buttons):
            try:
                button = list(self.browser.find_elements(By.CLASS_NAME, "copy-coupon"))[i]
                ActionChains(self.browser).scroll_to_element(button).perform()
            except ElementNotInteractableException:
                break
    
            self.browser.switch_to.new_window("tab")
            self.browser.get(original_url)
 
            QtTest.QTest.qWait(500)
            handles = list(self.browser.window_handles)
            self.browser.switch_to.window(handles[-1])
            QtTest.QTest.qWait(500)
            # find the new button
            button = list(self.browser.find_elements(By.CLASS_NAME, "copy-coupon"))[i]
            ActionChains(self.browser).scroll_to_element(button).perform()
            button.click()
            QtTest.QTest.qWait(500)

            # delete the new popup tab
            oldIndex = handles.index(self.browser.current_window_handle)
            self.browser.switch_to.window(handles[oldIndex])
            QtTest.QTest.qWait(500)
            self.browser.close()
            #refresh handles
            handles = list(self.browser.window_handles)
            self.browser.switch_to.window(handles[-1])
            QtTest.QTest.qWait(500)
            
            # find the code
            code = self.browser.find_element(By.ID, "sc-modal-code").text
            #find the discount text
            message = self.browser.find_element(By.ID, "sc-modal-title").text
            results[0].append(code)
            results[1].append(message)
            # close this window and return to the original one
            self.browser.close();
            self.browser.switch_to.window(handles[0])
        return results




        
# find resource path for runtime     
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)





def main():
    # Initialize the webdriver
    options = webdriver.ChromeOptions();

    # keep the page open after execution
    #options.add_experimental_option("detach", True)

    # Disable Automation Flags that may throw signals to google
    # adding argument to disable the AutomationControlled flag 
    options.add_argument("--disable-blink-features=AutomationControlled") 
 
    # exclude the collection of enable-automation switches 
    #options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
 
    # turn-off userAutomationExtension 
    #options.add_experimental_option("useAutomationExtension", False) 
 



    driver = uc.Chrome(options=options);


    driver.implicitly_wait(3)

    # Load target sites

    with open (resource_path('targets.json'), 'r') as f:
        data = json.load(f)


 
    


    driver.get("https://google.com")

    # Initialize UI
    app = QApplication(sys.argv)
    stylesheet = open(resource_path("styles.qss"), 'r', encoding='UTF8')
  
    stylesheet.seek(0)
    
    window = MainWindow(data["targets"], driver);
    app.setStyleSheet(stylesheet.read())
   
    window.show();

    sys.exit(app.exec_());


if __name__ == "__main__":
    main();