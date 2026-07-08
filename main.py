import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QRadioButton, QButtonGroup, QPushButton, QLineEdit
from PyQt5.QtWidgets import QBoxLayout, QVBoxLayout, QGridLayout, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5 import QtTest

from time import sleep;


# Selenium Imports

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import *
import undetected_chromedriver as uc
# Json Imports
import json

#URl Parser
from urllib.parse import urlparse


# Regex
import re

class MainWindow(QMainWindow):

    def __init__(self, targets, browser):
        super().__init__()
        
        self.browser : webdriver.Firefox = browser;
        self.targets = targets;
        self.prospects = {};
        self.protocols = {
            "www.hotdeals.com" : self._hotdeals,
            "simplycodes.com" : self._simplycodes
        }
        central_widget = QWidget()

        self.setCentralWidget(central_widget)
        self.setWindowTitle("Coupon Finder")
        self.setGeometry(700, 300, 500, 500)

        self.counter = 0;
        self.label1 = QLabel("Enter a search term and submit to find codes!", self)

        self.label1.setFont(QFont("Arial", 20))

        self.label1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.searchQuery = QLineEdit(self)

        self.searchQuery.setGeometry(0, 0, 100, 50)


        button1 = QPushButton("Initiate Search!", self)
        button1.clicked.connect(self.handle_click)

        vbox = QVBoxLayout()

        vbox.addWidget(self.label1)
        vbox.addWidget(self.searchQuery)
        vbox.addWidget(button1)

        central_widget.setLayout(vbox)

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
        self.label1.setText("Searching...")
        # initiate the search
        search_query = self._process_query(self.searchQuery.text())
        self.browser.get("https://duckduckgo.com/" + search_query + "+coupon+codes")

        # Go through the first few links on the page
        self._search_for_targets();
        

    def _find_percentage(self, dealTitle):
        
        # Very complex regex expression, this just finds any digit percentages in text
        return re.findall(r'([0-9]*\.?[0-9]*)\s*%', dealTitle)

    def _search_for_codes(self, target):
        possible_codes = self.protocols[target]()
        discovered_codes = {}
        for i in range(len(possible_codes[0])):
            discount = self._find_percentage(possible_codes[1][i]);
            codeContent = possible_codes[0][i]
            for disc in discount:
                print("possible discount amount for code [" + str(codeContent) + "]: " + str(disc) + "%")
                discovered_codes[codeContent] = int(disc)
        return discovered_codes

    def _sort_dict_by_value(self, oldDict):
        newDict = dict(sorted(oldDict.items(), key=lambda item: item[1]))
        newDict = dict(reversed(newDict.items()))
        print(newDict)
        return newDict

    def _search_for_targets(self):
        elements = self.browser.find_elements(By.CSS_SELECTOR, "a")
        count = 0;
        foundCodes = {}
        for element in elements:
            if (count < 10):
                content = element.text
                link = element.get_attribute("href")
                root = urlparse(link).netloc
                if (content == "" or root=="duckduckgo.com"):
                    continue
                    
                print("This link (" + content + ") was rooted at " + str(root))
                if (root in self.targets):
                    self.prospects[link] = [element, element.text]
        
        self.label1.setText("Found sites: " + str(len(self.prospects)))
        for prospect in self.prospects:
            root = urlparse(prospect).netloc
            foundCodes[root] = {}
            print(str(prospect) + " : " + self.prospects[prospect][1])
            self.browser.get(prospect)
            codes = self._search_for_codes(root);

            for code in codes.keys():
                foundCodes[root][code] = codes[code]
            QtTest.QTest.qWait(1000)
            oldData = foundCodes[root]
            foundCodes[root] = self._sort_dict_by_value(oldData)
            # Need to sort the codes now though
            


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
                print("found all visible codes")
                break
    
            self.browser.switch_to.new_window("tab")
            self.browser.get(original_url)
            print("executed script")
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

    with open ('targets.json', 'r') as f:
        data = json.load(f)


    for target in data["targets"]:
        print("Target Found: " + target)
    


    driver.get("https://google.com/search?q=rubber+ducks")

    # Initialize UI
    app = QApplication(sys.argv)
    app.setStyleSheet(Path("styles.qss").read_text())
    window = MainWindow(data["targets"], driver);
    window.show();
    sys.exit(app.exec_());


if __name__ == "__main__":
    main();