from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from json import loads
import re


class BookingCore:
    def __init__(self, username, password, sports, date, time, length=2, policy=True):

        self.username = username  # user name
        self.password = password  # user password for sports hub
        self.sports = sports  # user prefer sports, not only squash/badminton is avialable
        self.date = date  # book court for the specific date
        self.time = time  # book court for the specific time
        self.policy = policy  # default is true (false), booking core will find next avialble court in a later(earlier)# time point
        self.num_success_book = 0   # the number of success book
        self.court_success_book = []  # information about the court being book already
        self.refresh_wait_time = 10  # the refresh freqeuncy in the monitoring page
        self.time_start = "23:58:00"  # the monitor process only start after this time
        self.time_end = "00:10:00" # the booking core will end after this time
        self.length = 2 # how many hours do the user want to book

    def init_booking(self):  # init booking core
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--start-maximized");
        chrome_options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
        self.driver.get("https://sportwarwick.leisurecloud.net/Connect/mrmlogin.aspx")
        self._procedure_monitor()

    def _procedure_login(self):  # login
        self.driver.implicitly_wait(0.5)
        self.driver.find_element(By.ID, "ctl00_MainContent_InputLogin").send_keys(self.username)
        self.driver.find_element(By.ID, "ctl00_MainContent_InputPassword").send_keys(self.password)
        self.driver.find_element(By.ID, "ctl00_MainContent_btnLogin").click()
        if self.driver.current_url != "https://sportwarwick.leisurecloud.net/Connect/memberHomePage.aspx":
            assert "Invalid User Name and Pass Word"
        else:
            print("Log in successfully")
            self._procedure_monitor()

    def _procedure_start(self):  #start booking
        self.driver.implicitly_wait(10)
        self.driver.find_element(By.ID, "ctl00_ctl11_Li1").click()
        print("Start Booking")
        self._procedure_monitor()

    def _procedure_monitor(self):
        current_url = self.driver.current_url
        if current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmlogin.aspx":
            self._procedure_login()

        elif current_url == "https://sportwarwick.leisurecloud.net/Connect/memberHomePage.aspx":
            self._procedure_start()

        elif (current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmselectActivityGroup.aspx" or 
              current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmSelectActivity.aspx"):
            self._procedure_select_sport()

        elif current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmResourceStatus.aspx":
            self.procedure_enter_single_day()

        elif current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmProductStatus.aspx":
            self._procedure_monitoring()

    def _check_date(self):
        current_date = self.driver.find_element(By.ID, "ctl00_MainContent_lblCurrentNavDate").text
        if current_date.find(self.date) != -1:
            print(current_date)
            return True

        else:
            self.driver.find_element(By.ID,"ctl00_MainContent_Button2").click()
            return False

    def _procedure_monitoring(self):
        self._procedure_locate_date()
        available_timeslot = self.driver.find_elements(By.TAG_NAME, "input")
        print(available_timeslot)
        if len(available_timeslot)>0:
            print("Timeslot available")
            for items in available_timeslot:
                if items.get_attribute("value") == self.time:
                    items.click()
                    self._procedure_monitor()
                    break

            # insert backup logic
            print("Can't find preferred time")
            sleep(self.refresh_wait_time)
            self.driver.refresh()
            self._procedure_monitor()
        else:
            print("no available time slot")
            sleep(self.refresh_wait_time)
            self.driver.refresh()
            self._procedure_monitor()

    def _procedure_select_sport(self): # Start to select sport
        current_url = self.driver.current_url
        if current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmselectActivityGroup.aspx":
            if self.sports == "badminton":
                activity_list = self.driver.find_elements(By.TAG_NAME, "input")
                for items in activity_list:
                    if items.get_attribute("value") == "Racquet Sports":
                        items.click()
                        self._procedure_monitor()
                        break
        else:
            if self.sports == "badminton":
                activity_list_2 = self.driver.find_elements(By.TAG_NAME, "input")
                for items in activity_list_2:
                    if items.get_attribute("value") == "Badminton - Hub":
                        items.click()
                        self._procedure_monitor()
                        break

    def _procedure_locate_date(self):
        while not self._check_date():
            self._check_date()

    def procedure_enter_single_day(self):
        for items in self.driver.find_elements(By.TAG_NAME, "input"):
            if items.get_attribute("value") == "Available":
                items.click()
                sleep(2)
                self._procedure_monitor()
                break


if __name__ == '__main__':
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = loads(f.read())

        booking_core = BookingCore(config['username'],config["password"],config["sports"], config["date"], config["time"],
                                   policy=True)
    except Exception as e:
        print(e)
        raise Exception("The booking core fail to initiate, please check the config.json")

    booking_core.init_booking()
