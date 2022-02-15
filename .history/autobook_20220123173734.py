from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import re

def init_court_booking():

    def check_date(date):
        current_date = driver.find_element(By.ID, "ctl00_MainContent_lblCurrentNavDate").text
        if(current_date.find(date)!=-1):
            print(current_date)
            return True

        else:
            driver.find_element(By.ID,"ctl00_MainContent_Button2").click()
            return False

    def procedure_monitoring(Time):
        procedure_locatedate(Time)
        available_timeslot = driver.find_elements(By.TAG_NAME, "input")
        print(available_timeslot)
        if len(available_timeslot)>0:
            print("Timeslot available")
            for items in available_timeslot:
                if (items.get_attribute("value") == Time):
                    items.click()
                    procedure_monitor()
                    break

            ## insert backup logic
            print("Can't find preferred time")
            sleep(10)
            driver.refresh()
            procedure_monitor()
        else:
            print("no available time slot")
            sleep(10)
            driver.refresh()
            procedure_monitor()


    def procedure_monitor():
        current_url = driver.current_url
        if (current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmlogin.aspx"):
            procedure_login()
        elif (current_url == "https://sportwarwick.leisurecloud.net/Connect/memberHomePage.aspx"):
                procedure_start()
        elif (current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmselectActivityGroup.aspx" or
              current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmSelectActivity.aspx"):
            procedure_selectsport("Badminton", current_url)
        elif (current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmResourceStatus.aspx"):
            procedure_entersingleday()
        elif (current_url == "https://sportwarwick.leisurecloud.net/Connect/mrmProductStatus.aspx"):
            procedure_monitoring("30 Jan")



    def procedure_login():
        driver.implicitly_wait(0.5)

        ##log in
        driver.find_element(By.ID, "ctl00_MainContent_InputLogin").send_keys("jiahao.yang@warwick.ac.u")
        driver.find_element(By.ID, "ctl00_MainContent_InputPassword").send_keys(".")
        driver.find_element(By.ID, "ctl00_MainContent_btnLogin").click()
        if (driver.current_url != "https://sportwarwick.leisurecloud.net/Connect/memberHomePage.aspx"):
            assert "Invalid User Name and Pass Word"
        else:
            print("Log in successuflly")
            procedure_monitor()


    def procedure_start():
        driver.implicitly_wait(10)
        driver.find_element(By.ID, "ctl00_ctl11_Li1").click()
        print("Start Booking")
        procedure_monitor()


    def procedure_selectsport(Sport,currentUrl):
        if (currentUrl == "https://sportwarwick.leisurecloud.net/Connect/mrmselectActivityGroup.aspx"):
            if (Sport == "Badminton"):
                activity_list = driver.find_elements(By.TAG_NAME, "input")
                for items in activity_list:
                    if items.get_attribute("value") == "Racquet Sports":
                        items.click()
                        procedure_monitor()
                        break
        else:
            if (Sport == "Badminton"):
                activity_list_2 = driver.find_elements(By.TAG_NAME, "input")
                for items in activity_list_2:
                    if items.get_attribute("value") == "Badminton - Hub":
                        items.click()
                        procedure_monitor()
                        break

    def procedure_locatedate(time):
        while check_date(time) != True:
            check_date(time)

    def procedure_entersingleday():
        for items in driver.find_elements(By.TAG_NAME, "input"):
            if items.get_attribute("value") == "Available":
                items.click()
                sleep(2)
                procedure_monitor()
                break


    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--start-maximized");
    chrome_options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
    driver.get("https://sportwarwick.leisurecloud.net/Connect/mrmlogin.aspx")
    procedure_monitor()


init_court_booking()
