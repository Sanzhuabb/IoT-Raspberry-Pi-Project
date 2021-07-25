import RPi.GPIO as GPIO
import dht11
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
from datetime import date, datetime
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD

# initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)   # Set ledPin's mode is output
GPIO.output(12, GPIO.LOW)  # Set ledPin low to off led

#AWS IoT certificate based connection
myMQTTClient= AWSIoTMQTTClient("123afhlss456")
myMQTTClient.configureEndpoint("a2qltcok4pbs9j-ats.iot.us-west-2.amazonaws.com", 8883)
myMQTTClient.configureCredentials("/home/pi/certs/AmazonRootCA1.pem", "/home/pi/certs/e38bc20b51-private.pem.key", "/home/pi/certs/e38bc20b51-certificate.pem.crt")
myMQTTClient.configureOfflinePublishQueueing(-1) # Infinite offline Publish queueing
myMQTTClient.configureDrainingFrequency(2) # Draining: 2 Hz
myMQTTClient.configureConnectDisconnectTimeout(10) # 10 sec
myMQTTClient.configureMQTTOperationTimeout(5) # 5 sec
#connect and publish
myMQTTClient.connect()
myMQTTClient.publish("my_piTopic", "connected", 0)

PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.

# Create PCF8574 GPIO adapter.
try:
    mcp = PCF8574_GPIO(PCF8574_address)
except:
    try:
        mcp = PCF8574_GPIO(PCF8574A_address)
    except:
        exit(1)

# Create LCD, passing in MCP GPIO adapter.
lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)

mcp.output(3,1)     # turn on LCD backlight
lcd.begin(16,2)     # set number of LCD lines and columns
lcd.setCursor(0,0)  # set cursor position

#loop and publish sensor reading
try:
    while 1:
        now = datetime.utcnow()
        now_str= now.strftime('%Y-%m-%dT%H:%M:%SZ') #e.g. 2016-04-18T06:12:25.877Z
        instance = dht11.DHT11(pin = 11) #BCM GPIO04
        result = instance.read()
        if result.is_valid():
            payload = '{ "timestamp": "' + now_str+ '","temperature": ' + str(result.temperature) + ',"humidity": '+ str(result.humidity) + ' }'
            print payload
            myMQTTClient.publish("my_piTopic", payload, 0)

            lcd.message('Temp: ' + str(result.temperature) +'\n')# display temperature
            lcd.message('Humi: ' + str(result.humidity))         # display humidity

            if result.humidity > 70:
                GPIO.output(12, GPIO.HIGH)  # led on
            else:
                GPIO.output(12, GPIO.LOW) # led off
        
            sleep(4)
        else:
            print (".")
            lcd.clear()
            sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
    exit() 