from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from json import loads
from datetime import datetime, timedelta
import csv
import re


class BookingCore:
    """
    A class to represent a booking core.

    ...
    Attributes
    ----------
    username : str
        user name for the sports hub
    password : str
        password for the sprts hub
    sports : str
        user target sport, squash/badminton
    date : str
        prefer date in formate "day Month", e.g., "31 Jan"
    time : str
        prefer time in "%H:%M" formate, e.g., "07:00"
    pref_court : str
        prefer cournt, e.g., "C1"
    policy: boolean
        backup policy, booking core will find next available court in later time point if true
    length: int
        The time difference between first time point and the second time point. The unit is hour.

    ...
    Methods
    -------

    init_booking():
        Init the booking core

    """

    def __init__(self, username, password, sports, date, time, pref_court="A1", length=1, policy=True):

        self.username = username  # user name
        self.password = password  # user password for sports hub
        self.sports = sports  # user prefer sports, not only squash/badminton is avialable
        self.date = date  # book court for the specific date
        self.time = datetime.strptime(time, "%H:%M")  # book court for the specific time
        self.pref_court = pref_court  # book specific court, default value is A1
        self.policy = policy  # default is true (false), booking core will find next avialble court in a later(
        # earlier)# time point
        self.num_success_book = 0  # the number of success book
        self.court_success_book = []  # information about the court being book already
        self.refresh_wait_time = 3  # the refresh freqeuncy in the monitoring page
        self.time_start = "23:58:00"  # the monitor process only start after this time
        self.time_end = "00:10:00"  # the booking core will end after this time
        self.length = length # the time difference between time 1 and time 2, set it as zero if you only need 1 slot
        self.reverse = False # whehter the policy has been reversed
        self.onset_time = datetime.now()
        self.attempt_booking_court = ""
        
        if self.sports == "badminton":
            self.timeslot_length = 1
        elif self.sports == "squash":
            self.timeslot_length = 0.75

        self.time2 = self.time + timedelta(hours=self.timeslot_length)  # the second time point

    def init_booking(self):  # init booking core
        description = "Now start booking for " + self.sports + " court on " + self.date + "." + "The preferred court is " + self.pref_court
        print(description)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")  # incognition windows to provide clear cookies
        chrome_options.add_argument("--start-maximized");  # Maximizing the windows to ensure component is not collapsed
        chrome_options.add_experimental_option("detach", True)  # Keep the windows on
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

    def _procedure_start(self):  # start booking
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
            self._procedure_enter_single_day()

        elif current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmProductStatus.aspx":
            self._procedure_court_monit()

        elif current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmConfirmBooking.aspx":
            self._procedure_complete_book()

        elif current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmBookingConfirmed.aspx":
            self._procedure_confirm_book()

        elif current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmViewMyBookings.aspx":
            self.driver.execute_script("window.history.go(-1)")
            self._procedure_monitor()

        elif current_url == "https://sportwarwick.leisurecloud.net/Connect/opInfo.aspx":
            self.driver.execute_script("window.history.go(-1)")
            self._procedure_monitor()

    def _check_data(self):
        current_date = self.driver.find_element(By.ID, "ctl00_MainContent_lblCurrentNavDate").text
        if current_date.find(self.date) != -1:
            print(current_date)
            return True

        else:
            self.driver.find_element(By.ID, "ctl00_MainContent_Button2").click()
            return False

    def _procedure_court_monit(self):
        self._procedure_locate_date()  # locate the correct date
        print("Looking for court for ", self.time, self.time2)
        self.driver.implicitly_wait(0.5)
        available_timeslot = self.driver.find_elements(By.CLASS_NAME,
                                                       "itemavailable")  # check whether the time slot has been released
        if len(available_timeslot) > 0:  # if time slot has ben released
            print("Timeslot available")
            if self._check_times_availablity():  # check whether the courts has been occupied for activities
                print("Both time avialble, now proceed to court selection")
                self._court_booking()
            else:
                print("There is not enought avialble court, now proceed to back up plan")
                self._back_up_timepoint()

        else:
            print("no available time slots, waitng to refresh")
            current_time = datetime.now()
            if current_time < self.onset_time + timedelta(minutes=15):
                sleep(self.refresh_wait_time)
                self.driver.refresh()
                print("refreshing")
                self._procedure_monitor()
            else:
                self.driver.quit()

    def _check_times_availablity(self):
        """
        This function check whether the backup court searching function will be ran

        """
        if self.length != 0:  # check whehter two time points have available courts
            available_timeslot_t1 = []
            available_timeslot_t2 = []

            for items in self.driver.find_elements(By.TAG_NAME, "input"):
                if items.get_attribute("value") == datetime.strftime(self.time, "%H:%M"):
                    available_timeslot_t1.append(items)
                elif items.get_attribute("value") == datetime.strftime(self.time2, "%H:%M"):
                    available_timeslot_t2.append(items)

            if len(available_timeslot_t1) > 0 and len(available_timeslot_t2) > 0:
                return True
            else:
                return False
        else:
            available_timeslot_t1 = []

            for items in self.driver.find_elements(By.TAG_NAME, "input"):
                if items.get_attribute("value") == datetime.strftime(self.time, "%H:%M"):
                    available_timeslot_t1.append(items)

            if len(available_timeslot_t1) > 0:
                return True
            else:
                return False

    def _back_up_timepoint(self):
        """
        This function will be ran if there is no court avialbles for certain period of time, for exmaple, all the courts are booked for certain activitiies during these time.

        """

        if self.policy:
            self.time += timedelta(hours=1)
            self.time2 += timedelta(hours=1)
        else:
            self.time -= timedelta(hours=1)
            self.time2 -= timedelta(hours=1)

        if datetime.strptime("22:00", "%H:%M") > self.time > datetime.strptime("06:00", "%H:%M"):
            self.driver.refresh()
            self._procedure_monitor()
        else:
            if self.reverse:
                print("No time slots avialable for today")
                with open('result.csv', 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow([self.date, "No available court found"])
            else:
                if self.policy:
                    self.policy = False
                else:
                    self.policy = True

                self.reverse = True
                self.time -= timedelta(hours=1)
                self.time2 -= timedelta(hours=1)
                self.driver.refresh()
                self._procedure_monitor()


    def _court_booking(self):
        if self.sports == "badminton":
            self._court_booking_badminton()
        elif self.sports == "squash":
            self._court_booking_squash()

    def _court_booking_squash(self):
        print("booking court for squash")
        valid_time_slot = []
        valid_court_info = []
        # check current progress
        if self.num_success_book == 0:
            target_time = datetime.strftime(self.time, "%H:%M")
        else:
            target_time = datetime.strftime(self.time2, "%H:%M")

        # find all possible options
        for items in self.driver.find_elements(By.TAG_NAME, "input"):
            if items.get_attribute("value") == target_time:
                valid_time_slot.append(items)
                court_info = list()
                courtno_info = re.findall('(Court\s\d)', items.get_attribute("data-qa-id"))[0]
                court_info.append(courtno_info)
                valid_court_info.append(court_info)
                print(court_info)
        # locate the preferred court
        target_index = -5
        for index, items in enumerate(valid_court_info):
            if items[-1] == self.pref_court:
                target_index = index
                print("Preferred court is ", self.pref_court, " Index is", target_index)
                print(valid_court_info)
                break

        if target_index > -1:
            valid_time_slot[target_index].click()
            self.attempt_booking_court = valid_court_info[target_index]
            print("Preferred court available")
            self._procedure_monitor()
        else:  # No preferred court going to backup court
            print("Preferred court is not available")
            backup = ["Court 1", "Court 2","Court 3","Court 4","Court 5","Court 6"]

            def _select_backup_court(Court):
                for index, items in enumerate(valid_court_info):
                    if items[-1] == Court:
                        target_index = index
                        valid_time_slot[target_index].click()
                        self.attempt_booking_court = valid_court_info[target_index]
                        print("Go for back up court")
                        self._procedure_monitor()
                        break

            for court in backup:
                _select_backup_court(court)
                print(court)


    def _court_booking_badminton(self):
        valid_time_slot = []
        valid_court_info = []
        # check current progress
        if self.num_success_book == 0:
            target_time = datetime.strftime(self.time, "%H:%M")
        else:
            target_time = datetime.strftime(self.time2, "%H:%M")

        # find all possible options
        for items in self.driver.find_elements(By.TAG_NAME, "input"):
            if items.get_attribute("value") == target_time:
                valid_time_slot.append(items)
                court_info = list()
                zone_info = re.findall('(Zone\s\w)', items.get_attribute("data-qa-id"))[0][-1]
                courtno_info = re.findall('(Court\s\d)', items.get_attribute("data-qa-id"))[0][-1]
                court_info.append(re.findall('(\d+:\d+)', items.get_attribute("data-qa-id"))[0])
                court_info.append(zone_info)
                court_info.append(courtno_info)
                court_info.append(zone_info + courtno_info)
                valid_court_info.append(court_info)
                print(court_info)
        # locate the preferred court
        target_index = -5
        for index, items in enumerate(valid_court_info):
            if items[-1] == self.pref_court:
                target_index = index
                print("Preferred court is ", self.pref_court, " Index is", target_index)
                print(valid_court_info)
                break

        if target_index > -1:
            valid_time_slot[target_index].click()
            self.attempt_booking_court = valid_court_info[target_index]
            print("Preferred court available")
            self._procedure_monitor()
        else:  # No preferred court going to backup court
            print("Preferred court is not available")
            zonea = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4", "C1", "C2", "C3", "C4", "D1", "D2", "D3", "D4"]
            zoneb = ["B1", "B2", "B3", "B4", "A1", "A2", "A3", "A4", "C1", "C2", "C3", "C4", "D1", "D2", "D3", "D4"]
            zonec = ["C1", "C2", "C3", "C4", "B1", "B2", "B3", "B4", "A1", "A2", "A3", "A4", "D1", "D2", "D3", "D4"]
            zoned = ["D1", "D2", "D3", "D4", "C1", "C2", "C3", "C4", "B1", "B2", "B3", "B4", "A1", "A2", "A3", "A4"]

            def _select_backup_court(Court):
                for index, items in enumerate(valid_court_info):
                    if items[-1] == Court:
                        target_index = index
                        valid_time_slot[target_index].click()
                        self.attempt_booking_court = valid_court_info[target_index]
                        print("Go for back up court")
                        self._procedure_monitor()
                        break

            if self.pref_court[0] == "A":
                for court in zonea:
                    _select_backup_court(court)
                    print(court)

            elif self.pref_court[0] == "B":
                for court in zoneb:
                    _select_backup_court(court)
                    print(court)
            elif self.pref_court[0] == "C":
                for court in zonec:
                    _select_backup_court(court)
                    print(court)
            elif self.pref_court[0] == "D":
                for court in zoned:
                    _select_backup_court(court)
                    print(court)

    def _procedure_select_sport(self):  # Start to select sport
        current_url = self.driver.current_url
        if current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmselectActivityGroup.aspx":
            if self.sports == "badminton" or self.sports == "squash":
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
            elif self.sports == "squash":
                activity_list_2 = self.driver.find_elements(By.TAG_NAME, "input")
                for items in activity_list_2:
                    if items.get_attribute("value") == "Squash":
                        items.click()
                        self._procedure_monitor()
                        break


    def _procedure_locate_date(self):
        while not self._check_data():
            self._check_data()

    def _procedure_enter_single_day(self):
        for items in self.driver.find_elements(By.TAG_NAME, "input"):
            if items.get_attribute("value") == "Available":
                items.click()
                sleep(2)
                self._procedure_monitor()
                break

    def _procedure_complete_book(self):
        self.driver.implicitly_wait(10)
        self.driver.find_element(By.ID,"ctl00_MainContent_btnBasket").click()
        self._procedure_monitor()

    def _procedure_confirm_book(self):
        self.num_success_book += 1
        self.court_success_book.append(self.attempt_booking_court)
        if self.length != 0:  # need to book two courts
            if self.num_success_book == 1: # start to book court 2
                self.driver.execute_script("window.history.go(-1)")
                self._procedure_monitor()
            else:
                print("Booking Complete")
                print(self.court_success_book)
                with open('result.csv','a') as f:
                    writer = csv.writer(f)
                    writer.writerow([self.date, self.court_success_book])
                self.driver.quit()

        else:
            print("Booking Complete")
            print(self.court_success_book)
            with open('result.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow([self.date,self.court_success_book])
            self.driver.quit()

    def _procedure_booking_fail(self):
        self.attempt_booking_court = ""
        self.driver.execute_script("window.history.go(-1)")
        self._procedure_monitor()

if __name__ == '__main__':
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = loads(f.read())

        booking_core = BookingCore(config['username'], config["password"], config["sports"], config["date"],
                                   config["time"],
                                   config['pref_court'], policy=True)
    except Exception as e:
        print(e)
        raise Exception("The booking core fail to initiate, please check the config.json")

    booking_core.init_booking()
