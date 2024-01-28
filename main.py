import machine
from machine import Pin
from machine import ADC
import time
from time import sleep
import dht
import network
from CONFIG import SSID, PASSWORD, USER, GITHUB_URL, GITHUB_RAW_URL, REPOSITORY, BRANCH, FILES, REMOTE_UPDATE
#print('Before import of senko')
import senko
#print('After import of senko')

def wifi_setup():  #Exit of Routine: wifi_status() = 1 means connected, 0 mean not connected
    wifi_status.off()  #Wifi LED is put OFF
    print('Trying to connect to Wifi . . . . . ')

    station = network.WLAN(network.STA_IF)

    station.active(True)
    
    station.connect(SSID, PASSWORD)
    start_time = time.time()

    stop_time = time.time()
    duration = stop_time - start_time
    while duration < 18:  #Must be connected within ~20 sec
        stop_time = time.time()
        duration = stop_time - start_time
              
        if duration > 15:
            print('Not connected, 15 sec time-out passed')
            wifi_status.off()  #Wifi LED is put OFF
            break
        if station.isconnected() == True:
            wifi_status.on()  #Wifi LED is put ON
            print('Wifi connection successfully to:',SSID,' with IP, Mask, Gateway, DNS:')
            print(station.ifconfig())
            break
    return(wifi_status)

def wifi_check():
    station = network.WLAN(network.STA_IF)
    print("Check if connected to Wifi")
    if station.isconnected() == True:
        print('Still connected to:',ssid)
        wifi_status.on()  #Wifi LED is put ON
    else:
        print('Reconnect to Wifi')
        wifi_setup()
        #wifi_status updated from wifi_setup() routine
        # Needs WORK HERE
        #IF wifi_status = 1 continue program with Blynk Connected
        #IF Wifi_status = 0 continue without Wifi and Blynk
    print('Test wifi_check status:',wifi_status())
    return(wifi_status)

def read_dht():   #From DHT-11 temp/humidity module
    global temp, hum
#    dht_pin = dht.DHT22(Pin(4))  # Comment it if you are using DHT22 and uncomment the next line
    dht_pin = dht.DHT11(Pin(4)) # Uncomment it if you are using DHT11 and comment the above line
    temp = hum = 0
    try:
        sleep(1.25) # Sample period is 1 sec
        dht_pin.measure()
        temp = dht_pin.temperature()
        hum = dht_pin.humidity()
        if (isinstance(temp, float) and isinstance(hum, float)) or (isinstance(temp, int) and isinstance(hum, int)):
            msg = (b'{0:3.1f},{1:3.1f}'.format(temp, hum))
            hum = round(hum, 2)
            return(msg, temp, hum)
        else:
            return('Invalid DHT sensor readings.')
    except OSError as e:
        return('Failed to read DHT sensor.')

def read_moist():  #From FC-28 moisture sensor module
    global moi
    moi = 0
    moisture = ADC(0)
    sleep(1.25)
    moi = moisture.read()
    moi = round((100*((1024 - moi)/556)))  #Moisture in %, Must be calibrated !!!
    return(moi) 


########################################################################################
###                          MAIN PROGRAM STARTS HERE                                ###
########################################################################################
###           Check if new Files are available, if YES, upload in NodeMCU            ###
########################################################################################
url = GITHUB_RAW_URL
user = USER
repo = REPOSITORY
branch = BRANCH
files = FILES

OTA = senko.Senko(
  url = GITHUB_RAW_URL,
  user = USER, # Required
  repo = REPOSITORY, # Required
  branch = BRANCH, # Optional: Defaults to "master"
#  working_dir="app", # Optional: Defaults to "app"
  files = FILES  #["test1.py", "test2.py"]
)

power_status = Pin(13, Pin.OUT)
wifi_status = Pin(12, Pin.OUT)
pump = Pin(14, Pin.OUT)
pump_status = Pin(16, Pin.IN)

power_status.on()  # Power is ON
wifi_status.off()  # Wifi is OFF
pump.off()  # Pump set to OFF
pump_status = pump


start = 1   # Start and keep running

# Setup Wifi 1st time after fresh start
wifi_setup()

# Wifi ON: Status=1 or OFF: Status=0
# Blue LED is ON when connected
    
######################################################################################
########  When Wifi is ON, check for update via OTA on Github repository
########  CONFIG.py contains the configuration parameters, e.g. REPOSITORY on Github
######################################################################################
    
if wifi_status() == 1:
    print('Wifi is ON, Check for Updates, if REMOTE_UPDATE = YES in CONFIG.py file')

####################################################
###  ONLY check for new Versions, NO Updates     ###
####################################################
#     if OTA.fetch():
#         print("A newer version is available!")
#     else:
#         print("Up to date! Ready for the rest of the program")
    
###########################################################
###  Check for new Versions, Update and Reboot NodeMCU  ###
###########################################################
    if REMOTE_UPDATE == "YES":        
#        print('UPDATE')
        if OTA.update():
            print("Updated to the latest file versions ! Rebooting...")
            machine.reset()
        else:    
            print('NO updates available, keep as is !!!')

else:
    print('Wifi is OFF, continue without Wifi.')
#######################################################################################################
########  Start rest of program, when Wifi was ON, check for update via OTA on Github repository done
#######################################################################################################
while start == 1:
    pump.on()
    sleep(0.75)
    pump.off()
    sleep(0.75)
    
#################################################################################
#################################################################################


while start == 1:
    while wifi_status() == 1:  #Wifi is ON, use Blynk 

        import BlynkLib   #Verson 0.2.1
        from BlynkTimer import BlynkTimer

        BLYNK_AUTH = 'WzwPm0yo_PHlPSBsatpPka7d0PoastDp'
        print("Connecting to Blynk . . . . .")
        blynk = BlynkLib.Blynk(BLYNK_AUTH)

        timer = BlynkTimer()

        @blynk.on("connected")
        def blynk_connected(ping):
            print('Blynk ready, Ping:', ping, 'mS')
            return

        # Blynk Virtual pins:
        # V16 = Output, switch Pump status: ON or OFF = D5 (input GPIO14)
        # V0  = Input, Status, Power is ON LED = D7 (output GPIO13)
        # V1  = Input, Status, Wifi is ON LED = D6 (ouput GPIO12)
        # V2  = Input, Status, Pump is set ON or OFF = D0 (output, GPIO16 Connect to D5 GPIO14)
        # V10 = Input, Air Temperature (temp) = D2 (input GPIO4)
        # V11 = Input, Air Humidity (hum) = D2 (input GPIO4)
        # V12 = Input, Soil Moisture (moi) = A0 (input ADC0)
        # V20 = Output, Master RESET, when Password is given on phone

        # Register virtual pin handler
        @blynk.on("readV12")
        def v12_read_handler():
            read_moist()
            blynk.virtual_write(12, moi)
            read_dht()
            blynk.virtual_write(10, temp)
            blynk.virtual_write(11, hum)
            
            if power_status.value() == 1:
                blynk.virtual_write(0, 255)   # LED is full on when 255, OFF when 0
            else:
                blynk.virtual_write(0, 0)

            if wifi_status.value() == 1:
                blynk.virtual_write(1, 255)
            else:
                blynk.virtual_write(1, 0)

            if pump_status.value() == 1:
                blynk.virtual_write(2, 255)
        #        print('Pump LED is ON')
            else:
                blynk.virtual_write(2, 0)
        #        print('Pump LED is OFF')
            return   

        ####  Read Pump ON/OFF  from phone, and switch ON/OFF the pump and LED on phone
        # Register virtual pin handler
        @blynk.on("V16")
        def v16_write_handler(value):
        #    print('Pump Switch Value: {}'.format(value[0]))
            pump_status = value[0]
        #    print('V16: ',value[0])
            if pump_status == str(0):
        #        print('Pump OFF: ' ,pump_status)
                pump.off()     # Switch pump OFF when ON
                blynk.virtual_write(2, 0)   # Pump status LED OFF
            else:
        #        print('Pump ON: ' ,pump_status)
                pump.on()     # Switch pump ON when OFF
                blynk.virtual_write(2, 255)   # Pump status LED ON
            pump_status = pump
        #    print('Pump_status ', pump_status())
            return

        ####  Reset the system when a password on the phone is entered
        # Register virtual pin handler
        @blynk.on("V20")
        def v20_write_handler(value):
            print('RESET: ',value)
            reset_value = value[0]
            print('V20: ',reset_value)
        #    input('Wait here')
            if reset_value == 'tomato':
        #        print('Reset Machine: ' ,reset_value)
                blynk.virtual_write(20,'')
                pump.off()     # Switch pump OFF when ON
        #        blynk.virtual_write(2, 0)   # Pump status LED OFF
                print('Reset the Machine')
                machine.reset()
        #    blynk.virtual_write(20,'')
            value[0] = ''
            print('Leave RST Routine, NO Reset')
            return

        x=0
        while x < 2:
            sensor_readings = read_dht()
            print('Air Temperature: ',temp)
            print('Air Humidity: ',hum)
            moi = read_moist()
            print('Soil Moisture: ',moi)
            x = x+1

        pump.off()   #Make sure pump is OFF - initialising

        # Add Timers
#        timer.set_timeout(2, hello_world) #Print 'hello_world' after 2 seconds
        timer.set_interval(45, wifi_check)  #Check every 45sec if Wifi is still connected

        while True:
            blynk.run()
            timer.run()
            if wifi_status() == 0:
                break

    while wifi_status() == 0:  #Wifi is OFF, loop till wifi back ON
        x=0
        while x < 2:
            sensor_readings = read_dht()
            print('Air Temperature: ',temp)
            print('Air Humidity: ',hum)
            moi = read_moist()
            print('Soil Moisture: ',moi)
            x = x+1

#Test routine blinking LEDs       
        y=0
        while y < 20:
            pump.on()
            sleep(0.5)
            pump.off()
            sleep(0.5)
            y = y +1
        
        wifi_check()    
        print('Wifi status():',wifi_status())
        
    continue

print('Done, but not expected to be here.')
