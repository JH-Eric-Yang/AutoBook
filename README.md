# AutoBook

This is the new version of autobook.js - the autobook.py.

You can find the socure code in the source folder.

An excutable file is provided in init folder. To use the autobook script, you need to following step:

1. Input your username and password for the sportshub system in the *config.json*. Make sure that the username and password could be used to log in via https://sportwarwick.leisurecloud.net/Connect/mrmlogin.aspx

2. Input the date that you would like to book a court in the *scedule.xlsx* file. Please follow the same format as provided.

3. Use task scheduler to the *init.exe* at 11:57 pm every night. The script will auoto check the court and complet the booking.

4. (optional) You can also use the task scheduler to schedule an auto-shutodown after the booking. The booking usually ends at 12:02 every day. 


Feel free to contact the author if there is any problem.


