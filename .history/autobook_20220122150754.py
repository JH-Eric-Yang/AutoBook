##web function
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep

def court_book(user_name,pass_word,sports = "Badminton"):
    ##initiate browser
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--start-maximized");
    chrome_options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
    driver.get("https://sportwarwick.leisurecloud.net/Connect/mrmlogin.aspx")
    print(driver.title)

    driver.implicitly_wait(0.5)

    ##log in
    driver.find_element(By.ID, "ctl00_MainContent_InputLogin").send_keys(user_name)
    driver.find_element(By.ID, "ctl00_MainContent_InputPassword").send_keys(pass_word)
    driver.find_element(By.ID, "ctl00_MainContent_btnLogin").click()
    if (driver.current_url != "https://sportwarwick.leisurecloud.net/Connect/memberHomePage.aspx"):
        assert "Invalid User Name and Pass Word"
    else:
        print("Log in successuflly")

    ##
    driver.implicitly_wait(10)
    driver.find_element(By.ID, "ctl00_ctl11_Li1").click()
    print("Start Booking")

    ##now select sports
    if (sports == "Badminton"):
        activity_list = driver.find_elements(By.TAG_NAME, "input")
        for items in activity_list:
            if items.get_attribute("value") == "Racquet Sports":
                items.click()
                break

        ##

sports = "Badminton"
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--start-maximized");
chrome_options.add_experimental_option("detach", True)

driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
driver.get("https://sportwarwick.leisurecloud.net/Connect/mrmlogin.aspx")
print(driver.title)

driver.implicitly_wait(0.5)

##log in
driver.find_element(By.ID, "ctl00_MainContent_InputLogin").send_keys("jiahao.yang@warwick.ac.uk")
driver.find_element(By.ID, "ctl00_MainContent_InputPassword").send_keys("Ericegg251314.")
driver.find_element(By.ID, "ctl00_MainContent_btnLogin").click()
if (driver.current_url != "https://sportwarwick.leisurecloud.net/Connect/memberHomePage.aspx"):
    assert "Invalid User Name and Pass Word"
else:
    print("Log in successuflly")

##
driver.implicitly_wait(10)
driver.find_element(By.ID, "ctl00_ctl11_Li1").click()
print("Start Booking")

##now select sports
if (sports == "Badminton"):
    activity_list = driver.find_elements(By.TAG_NAME, "input")
    for items in activity_list:
        if items.get_attribute("value") == "Racquet Sports":
            items.click()
            break

    ##
    activity_list_2 = driver.find_elements(By.TAG_NAME, "input")
    for items in activity_list_2:
        print(items.get_attribute("value"))
