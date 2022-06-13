#For this code to work, you need a file named 'water_log.txt' in the SD card
#The algorithm reformats the file so it doesn't matter what is on it prior

#Importing necessary libraries
import time
import adafruit_dht
import board
import analogio
import pulseio
from adafruit_motor import servo
import busio
from adafruit_seesaw.seesaw import Seesaw
import digitalio
import adafruit_sdcard
import storage
import adafruit_pcf8523

#Calculating voltage of daylight sensor
def analog_voltage(adc):
    return adc.value/65535*adc.reference_voltage

#Watering plant function
def water_plant():
    print('watering plant')
    my_servo.throttle=1
    time.sleep(5)
    my_servo.throttle = 0
    time.sleep(3)

#Recording data in SD card function
def record_data(n, moisture, val):
    with open("/sd/water_log.txt", "a") as fp:
        fp.write('{}:\n'.format(n))
        if val < 40000 and moisture < moist_min:
            fp.write('WATERED\nMoisture: {}\tVal: {}\n'.format(moisture, val))
            water_plant()
        else:
            fp.write('NO ACTION TAKEN\nMoisture: {}\tVal: {}\n'.format(moisture, val))
        fp.write("Time: %d:%02d:%02d\n" % (t.tm_hour, t.tm_min, t.tm_sec))
        fp.write("Date: %d/%d/%d\n\n" % (t.tm_mon, t.tm_mday, t.tm_year))

#Main code block
if __name__ == "__main__":
    #RTC
    myI2C = busio.I2C(board.SCL, board.SDA)
    rtc = adafruit_pcf8523.PCF8523(myI2C)

    #Moisture Sensor
    ss = Seesaw(myI2C, addr=0x36)

    #Daylight
    photocell = analogio.AnalogIn(board.A1)

    #Servo Motor
    pwm = pulseio.PWMOut(board.D11, frequency=50)
    my_servo = servo.ContinuousServo(pwm)

    #SD Card
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    cs = digitalio.DigitalInOut(board.D10)
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")

    #Plant Presets
    plants = [ ['Cherry Tomato', 500], ['Grape Tomato', 700] ]

    #Record counting index
    n=0

    #FIXME: ALLOW USER TO SPECIFY RTC FOR FINAL CODE
    #User setting RTC date and time
    print('\n\nSet date and time for recording purposes')
    #user_time = input('Enter Real Time Clock info in this format: yyyy/mm/dd/hh/mm or 2021/12/25/09/30\n')
    #time_vals = user_time.split('/')
    #t = time.struct_time((time_vals[0],time_vals[1], time_vals[2], time_vals[3], time_vals[4], 0, 0, -1, -1))
    t = time.struct_time((2021, 01, 24, 09, 30, 0, 0, -1, -1))
    rtc.datetime = t

    #Printing current list of stored plant values
    print('\n\n')
    for n in range(len(plants)):
        print('{}: {}, healthy moisture minimum: {}'.format(n, plants[n][0], plants[n][1]))

    #Plant preset selection
    plant_index = int(input('\nSelect plant number:\nor type \'a\' to add a new plant\n'))
    if plant_index != 'a':
        moist_min = plants[plant_index][1]
        print('\n{} plant selected'.format(plants[plant_index][0]))

    #Custom plant preset creation
    if plant_index == 'a':
        user_plant_name = input('\nEnter plant name:\n')
        user_moist_min = input('\nEnter plant\'s lower moisture bound:\n')
        plants.append( [user_plant_name, user_moist_min] )
        moist_min = user_moist_min

    #Formatting SD card for data recording
    with open('/sd/water_log.txt', 'w') as file:
        file.write('Group 9 Plant Watering System Data Log:\n\n')

    while True:
        try:
            #initializing sensor data readings
            moisture = ss.moisture_read()
            val = photocell.value

            #Maybe temporary. Displaying current sensor reading and desired minimum for testing
            print('\nMoisture minimum: {}'.format(moist_min))
            print("Moisture: {} \t Light: {}\n".format(moisture, val))

            #Recording Data and making decision to water or not
            t = rtc.datetime
            record_data(n, moisture, val)
            n+=1
            time.sleep(5)

        except RuntimeError as e:
    # Reading doesn't always work! Just print error and we'll try again
            print("Reading from DHT failure: ", e.args)
        time.sleep(1)

