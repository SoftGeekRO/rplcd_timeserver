import subprocess
import re
import time
from RPLCD.i2c import CharLCD

# Define digit pairs from 00 to 61 (yes 61 because of leap seconds)
digits = [
    [24341, 25351], [24120, 25120], [24161, 25370], [24161, 25171], [24301, 25141],
    [24360, 25171], [24360, 25371], [24141, 25101], [24361, 25371], [24341, 25141],
    [2241, 2251], [2020, 2020], [2061, 2270], [2061, 2071], [2201, 2041],
    [2260, 2071], [2260, 2271], [2041, 2001], [2261, 2271], [2241, 2041],
    [6341, 27251], [6120, 27020], [6161, 27270], [6161, 27071], [6301, 27041],
    [6360, 27071], [6360, 27271], [6141, 27001], [6361, 27271], [6341, 27041],
    [6341, 7351], [6120, 7120], [6161, 7370], [6161, 7171], [6301, 7141],
    [6360, 7171], [6360, 7371], [6141, 7101], [6361, 7371], [6341, 7141],
    [20341, 4351], [20120, 4120], [20161, 4370], [20161, 4171], [20301, 4141],
    [20360, 4171], [20360, 4371], [20141, 4101], [20361, 4371], [20341, 4141],
    [26241, 7351], [26020, 7120], [26061, 7370], [26061, 7171], [26201, 7141],
    [26260, 7171], [26260, 7371], [26041, 7101], [26261, 7371], [26241, 7141],
    [26241, 27351], [26020, 27120]]


# TODO: Don't forget to add the rplcd user to i2c group
class LCDScreen(object):

    def __init__(self, welcome_text):
        self.lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
                           cols=16, rows=2, dotsize=8,
                           charmap='A02',
                           auto_linebreaks=True,
                           backlight_enabled=True)

        self.lcd.backlight_enabled = True
        self.lcd.clear()
        self.lcd.write_string(welcome_text)

        # Create some custom characters
        self.lcd.create_char(0, (0, 0, 0, 0, 0, 0, 0, 0))
        self.lcd.create_char(1, (16, 24, 24, 24, 24, 24, 24, 16))
        self.lcd.create_char(2, (1, 3, 3, 3, 3, 3, 3, 1))
        self.lcd.create_char(3, (17, 27, 27, 27, 27, 27, 27, 17))
        self.lcd.create_char(4, (31, 31, 0, 0, 0, 0, 0, 0))
        self.lcd.create_char(5, (0, 0, 0, 0, 0, 0, 31, 31))
        self.lcd.create_char(6, (31, 31, 0, 0, 0, 0, 0, 31))
        self.lcd.create_char(7, (31, 0, 0, 0, 0, 0, 31, 31))

        self.lastScreenTime = time.time()  # time since last screen switch
        self.prevStr = ""

        self.screens = (
            (self.big_time_view, 6),
            # Rotating list of views on LCD with how many seconds to display each display. Round robin style.
            #(self.connectedUserView, 4),
            #(self.big_time_view, 6),
            (self.precision_view, 4),
            (self.big_time_view, 6),
            (self.ntptime_info, 5),
            (self.big_time_view, 6),
            (self.clockperf_view, 5),
            (self.get_hostname, 6),
            (self.get_current_ip, 6),
        )  # list of all views for rotation
        self.nrofscreens = len(self.screens)
        self.currentScreen = 0

    def write_lcd(self, s):
        """Checks the string, if different than last call, update screen.

        :param s:
        :return:
        """

        if self.prevStr != s:  # Oh what a shitty way around actually learning the ins and outs of encoding chars...
            # Display string has changed, update LCD
            self.lcd.clear()
            self.lcd.write_string(s)
            self.prevStr = s  # Save so we can test if screen changed between calls, don't update if not needed to reduce LCD flicker

    def big_time_view(self):
        """Shows custom large local time on LCD"""

        now = time.localtime()
        hrs = int(time.strftime("%H"))
        minutes = int(time.strftime("%M"))
        sec = int(time.strftime("%S"))

        # Build string representing top and bottom rows
        L1 = "0" + str(digits[hrs][0]).zfill(5) + str(digits[minutes][0]).zfill(5) + str(digits[sec][0]).zfill(5)
        L2 = "0" + str(digits[hrs][1]).zfill(5) + str(digits[minutes][1]).zfill(5) + str(digits[sec][1]).zfill(5)

        # Convert strings from digits into pointers to custom character
        i = 0
        XL1 = ""
        XL2 = ""
        while i < len(L1):
            XL1 = XL1 + chr(int(L1[i]))
            XL2 = XL2 + chr(int(L2[i]))
            i += 1
        self.write_lcd(XL1 + "\r" + XL2)
        # return XL1 + "\r" + XL2

    def precision_view(self):
        """Calculate and display the NTPD accuracy"""
        try:
            output = subprocess.check_output("ntpq -c rv", shell=True)
            returncode = 0
        except subprocess.CalledProcessError as e:
            output = e.output
            returncode = e.returncode
            print(returncode)
            exit(1)

        precision = ""
        clkjitter = ""
        clkwander = ""
        theStr = ""
        searchResult = re.search(r'precision=(.*?),', output.decode('utf-8'), re.S)
        precision = searchResult.group(1)
        searchResult = re.search(r'.*clk_jitter=(.*?),', output.decode('utf-8'), re.S)
        clk_jitter = searchResult.group(1)
        if precision and clk_jitter:
            precision = (1 / 2.0 ** abs(float(precision))) * 1000000.0
            theStr = "Prec: {:.5f} {}s\r".format(precision, chr(0xE4))
            theStr += "ClkJit: {:>4} ms".format(clk_jitter)
        else:
            theStr = "Error: No\rPrecision data"
        self.write_lcd(theStr)
        # return theStr

    def ntptime_info(self):
        """Statistics from ntptime command"""
        try:
            output = subprocess.check_output("ntptime", shell=True)
        except subprocess.CalledProcessError as e:
            output = e.output
            returncode = e.returncode
            print(returncode)
        precision = re.search(r'precision (.* us).*tolerance (.* ppm)', output.decode('utf-8'), re.M | re.S)
        if precision:
            theStr = "Precis: {:>8}\r".format(precision.group(1))
            theStr += "Stabi: {:>9}".format(precision.group(2))
        else:
            theStr = "No info\nError"
        self.write_lcd(theStr)

    def clockperf_view(self):
        """Shows jitter etc"""
        output = subprocess.check_output("ntptime", shell=True)
        search = re.search(r'TAI offset.*offset (.*? us).*jitter (.* us)', output.decode('utf-8'), re.M | re.S)
        if search:
            theStr = "Offset: {:>8}\r".format(search.group(1))
            theStr += "OSjitt: {:>8}".format(search.group(2))
        else:
            theStr = "No offset\rinfo error"
        self.write_lcd(theStr)

    def connectedUserView(self):
        """Shows connected clients to ntpd"""
        highestCount = "NaN"
        try:
            output = subprocess.check_output("ntpdc -n -c monlist | awk '{if(NR>2)print $1}' | uniq | wc -l",
                                             shell=True)  # Gets all the connected clients from ntp
        except subprocess.CalledProcessError as e:
            output = e.output
            returncode = e.returncode
            print(returncode)

        try:
            highestCount = subprocess.check_output(
                "ntpdc -n -c monlist | awk '{if(NR>2)print $4}' | sort -nrk1,1 | line",
                shell=True)  # Gets the highest connections from connected clients
        except subprocess.CalledProcessError as e:
            output = e.output
            returncode = e.returncode
            print(returncode)

        theStr = "Con users: {:>6}".format(output.decode('utf-8'))
        theStr += "Hi cons: {:>8}".format(highestCount)
        self.write_lcd(theStr)

    def get_hostname(self):
        import socket
        hostname = socket.getfqdn()
        if hostname:
            self.write_lcd(hostname)
        else:
            self.write_lcd('No hostname')

    def get_current_ip(self):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('1.1.1.1', 1))  # connect() for UDP doesn't send packets
        local_ip_address = s.getsockname()[0]
        self.write_lcd(local_ip_address)

    def update_lcd(self):
        if time.time() - self.lastScreenTime > self.screens[self.currentScreen][1]:  # Time to switch display
            self.currentScreen = self.currentScreen + 1
            self.lastScreenTime = time.time()  # reset screen timer
            if self.currentScreen > self.nrofscreens - 1:
                self.currentScreen = 0
        self.screens[self.currentScreen][0]()
