from m5stack import *
from m5ui import *
from uiflow import *
from easyIO import *
import time
from flow import ezdata
import wifiCfg
import time

SCREEN_MAIN = 0
SCREEN_STEPS = 1
SCREEN_UV = 2
SCREEN_WEATHER = 3

# Current screen variable
current_screen = SCREEN_MAIN

setScreenColor(0x000000)

# Initialize the last activity time
last_activity_time = time.time()

battery = (str((map_value((axp.getBatVoltage()), 3.7, 4.1, 0, 100))) + str('%'))
# Get the current date and time as ISO format
# date = ezdata.getCurrentISODateTime()
date = rtc.now()

# Extract the time components
# time_components = date.split("T")[1].split(":")
hour = int(time_components[0])
minute = int(time_components[1])

# Format the time string as "HH:MM"
time_string = "{:02d}:{:02d}".format(hour, minute)

# Extract the date components
# date_components = date.split("T")[0].split("-")
year = int(date_components[0])
month = int(date_components[1])
day = int(date_components[2])

# Format the date string as "Mon dd"
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
date_string = "{} {:02d}".format(month_names[month - 1], day)

def main_screen():
  lcd.clear()
  axp.setLcdBrightness(100)
  Date = M5TextBox(7, 12, date_string, lcd.FONT_DefaultSmall, 0x94b5b1, rotate=0)
  Time = M5TextBox(7, 90, time_string, lcd.FONT_DejaVu40, 0xedef6e, rotate=0)
  Battery = M5TextBox(100, 12, battery, lcd.FONT_DefaultSmall, 0x94b5b1, rotate=0)
  Steps = M5Rect(7, 140, 120, 25, 0x707070, 0x707070)
  Weather = M5Rect(7, 175, 120, 25, 0x707070, 0x707070)
  rectangle0 = M5Rect(7, 210, 120, 25, 0x707070, 0x707070)
  StepImage = M5Img(30, 143, "res/footprint.png", True)
  TempImage = M5Img(30, 178, "res/weather.png", True)
  UVImage = M5Img(30, 213, "res/beach.png", True)
  StepCounter = M5TextBox(54, 144, "1500", lcd.FONT_DejaVu18, 0x000000, rotate=0)
  Temperature = M5TextBox(54, 180, '{}°C'.format(22), lcd.FONT_DejaVu18, 0x000000, rotate=0)
  label1 = M5TextBox(55, 215, "High", lcd.FONT_DejaVu18, 0x000000, rotate=0)

def steps_screen():
  lcd.clear()
  axp.setLcdBrightness(100)
  Frame = M5Rect(7, 60, 120, 120, 0x707070, 0x707070)
  StepImage = M5Img(60, 70, "res/footprint.png", True)
  label0 = M5TextBox(25, 100, "Today's count:", lcd.FONT_DefaultSmall, 0x000000, rotate=0)
  StepCounter = M5TextBox(43, 120, "1500", lcd.FONT_DejaVu18, 0x000000, rotate=0)

def uv_screen():
  lcd.clear()
  axp.setLcdBrightness(100)
  Frame = M5Rect(7, 60, 120, 120, 0x707070, 0x707070)
  UVImage = M5Img(60, 70, "res/beach.png", True)
  label0 = M5TextBox(47, 100, "UV index:", lcd.FONT_DefaultSmall, 0x000000, rotate=0)
  UVIndex = M5TextBox(35, 120, "6 HIGH", lcd.FONT_DejaVu18, 0x000000, rotate=0)
  label2 = M5TextBox(12, 145, "Protection needed!", lcd.FONT_DefaultSmall, 0x000000, rotate=0)

def weather_screen():
  lcd.clear()
  axp.setLcdBrightness(100)
  Frame = M5Rect(7, 60, 120, 120, 0x707070, 0x707070)
  WeatherImage = M5Img(60, 70, "res/weather.png", True)
  label0 = M5TextBox(30, 100, "Temperature:", lcd.FONT_DefaultSmall, 0x000000, rotate=0)
  Temperature = M5TextBox(45, 120, "22 \u00B0C", lcd.FONT_DejaVu18, 0x000000, rotate=0)
  label2 = M5TextBox(20, 145, "High: 24 Low: 13", lcd.FONT_DefaultSmall, 0x000000, rotate=0)


def alert_screen():
  lcd.clear()
  axp.setLcdBrightness(100)
  setScreenColor(0xffffff)
  Frame = M5Rect(7, 60, 120, 120, 0xffffff, 0xffffff)
  StepImage = M5Img(60, 70, "res/warning.png", True)
  label0 = M5TextBox(20, 114, "Emergency Alert!", lcd.FONT_DefaultSmall, 0x000000, rotate=0)
  label2 = M5TextBox(49, 130, "From", lcd.FONT_Default, 0x000000, rotate=0)
  label3 = M5TextBox(33, 149, "DEVICE 1", lcd.FONT_Default, 0x000000, rotate=0)
  PWM0 = machine.PWM(2, freq=500, duty=50, timer=0)
  wait_ms(90)
  PWM0 = machine.PWM(2, freq=200, duty=0, timer=0)
  M5Led.on()
  wait_ms(90)
  M5Led.off()
  wait_ms(2)
  
  if btnA.isPressed():
    setScreenColor(0x000000)
    last_activity_time = time.time()
    main_screen()
  
def notification(text):
  wait(1)
  axp.setLcdBrightness(100)
  Frame = M5Rect(7, 30, 120, 50, 0x707070, 0xedef6e)
  label0 = M5TextBox(20, 40, text, lcd.FONT_Default, 0x000000, rotate=0)
  wait(2)
  Frame.hide()
  label0.hide()
  
    
def handle_button_b_press():
  global current_screen, last_activity_time
  
  last_activity_time = time.time()
  # Increment the current screen
  current_screen += 1
  
  # Wrap around if the current screen exceeds the maximum screen ID
  if current_screen > SCREEN_WEATHER:
      current_screen = SCREEN_MAIN
  
  # Clear the screen
  lcd.clear()
  
  # Display the appropriate screen based on the current screen ID
  if current_screen == SCREEN_MAIN:
      main_screen()
  elif current_screen == SCREEN_STEPS:
      steps_screen()
  elif current_screen == SCREEN_UV:
      uv_screen()
  elif current_screen == SCREEN_WEATHER:
      weather_screen()
        


while True:
  elapsed_time = time.time() - last_activity_time
  
  if elapsed_time >= 2:
    alert_screen()
    
  wait(0.1)

  if btnB.isPressed():
    handle_button_b_press()
  wait(0.1)
  if btnA.isPressed():
    setScreenColor(0x000000)
    last_activity_time = time.time()
    main_screen()
