from os import supports_bytes_environ
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from json import loads
from datetime import datetime, timedelta
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
        self.time = datetime.strptime(time, "%H:%M") # book court for the specific time
        self.pref_court = pref_court # book specific court, default value is A1
        self.policy = policy  # default is true (false), booking core will find next avialble court in a later(
        # earlier)# time point
        self.num_success_book = 0   # the number of success book
        self.court_success_book = []  # information about the court being book already
        self.refresh_wait_time = 10  # the refresh freqeuncy in the monitoring page
        self.time_start = "23:58:00"  # the monitor process only start after this time
        self.time_end = "00:10:00"  # the booking core will end after this time
        self.length = length  # the time difference between time 1 and time 2, set it as zero if you only need 1 slot
        self.time2 = self.time + timedelta(hours=self.length)  # the second time point


    def init_booking(self):  # init booking core
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--incognito")  # incognition windows to provide clear cookies
        chrome_options.add_argument("--start-maximized");  # Maximizing the windows to ensure component is not collapsed
        chrome_options.add_experimental_option("detach", True) # Keep the windows on
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

    def _check_data(self):
        current_date = self.driver.find_element(By.ID, "ctl00_MainContent_lblCurrentNavDate").text
        if current_date.find(self.date) != -1:
            print(current_date)
            return True

        else:
            self.driver.find_element(By.ID,"ctl00_MainContent_Button2").click()
            return False

    def _procedure_court_monit(self):
        self._procedure_locate_date()

        #Check length
        available_timeslot = self.driver.find_elements(By.CLASS_NAME, "itemavailable")


        if len(available_timeslot)>0:
            print("Timeslot available")
            if self._check_times_availablity():
                print("Both time avialble, now proceed to court selection")
            else:
                print("There is not enought avialble court, now proceed to back up plan")
                
            valid_time_slot = []
            valid_court_info = []
            for items in self.driver.find_elements(By.TAG_NAME,"input"):
                if items.get_attribute("value") == datetime.strftime(self.time,"%H:%M"):
                    valid_time_slot.append(items)
                    court_info = list()
                    court_info.append(re.findall('(\d+:\d+)',items.get_attribute("data-qa-id"))[0])
                    court_info.append(re.findall('(Zone\s\w)', items.get_attribute("data-qa-id"))[0][-1])
                    court_info.append(re.findall('(Court\s\d)', items.get_attribute("data-qa-id"))[0][-1])
                    valid_court_info.append(court_info)
                    print(court_info)

            if len(valid_time_slot) >0:
                print("court avialble for booking")
                print(valid_court_info)
            else:
                # insert backup logic
                print("Can't find preferred time")
                print("initiate back up logic")
                #sleep(self.refresh_wait_time)
                #self.driver.refresh()
                #self._procedure_monitor()
        else:
            print("no available time slot")
            sleep(self.refresh_wait_time)
            self.driver.refresh()
            self._procedure_monitor()

    def _check_times_availablity(self):
        """
        This function check whether the backup court searching function will be ran

        """
        if self.length !=0: # check whehter two time points have available courts
            available_timeslot_t1 = []
            available_timeslot_t2 = []
            
            for items in self.driver.find_elements(By.TAG_NAME,"input"):
                if items.get_attribute("value") == datetime.strftime(self.time,"%H:%M"):
                    available_timeslot_t1.append(items)
                elif items.get_attribute("value") == datetime.strftime(self.time2,"%H:%M"):
                    available_timeslot_t2.append(items)
            
            if len(available_timeslot_t1) > 0 and len(available_timeslot_t2)>0:
                return True
            else:
                return False
        else:
            available_timeslot_t1 = []
            
            for items in self.driver.find_elements(By.TAG_NAME,"input"):
                if items.get_attribute("value") == datetime.strftime(self.time,"%H:%M"):
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
            self.time += self.time + timedelta(hours=1)
            self.time2 += self.time + timedelta(hours=1)
        else:
            self.time += self.time - timedelta(hours=1)
            self.time2 += self.time - timedelta(hours=1)

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
        while not self._check_data():
            self._check_data()

    def _procedure_enter_single_day(self):
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
                                   config['pref_court'],policy=True)
    except Exception as e:
        print(e)
        raise Exception("The booking core fail to initiate, please check the config.json")

    booking_core.init_booking()
