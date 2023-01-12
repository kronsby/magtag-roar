"""roar-tag

A MagTag program to trigger a Home Assistant webhook.

This mainly connects to internet and waits for a button press. Each of the 4
buttons on the MagTag do something different.

1. Plays Roar by Katy Perry
2. Plays Think of What You've Done by Christina Vane
3. Turns on the lights
4. Turns off the lights

If 1 or 2 are pressed while any song is playing it will stop.
"""
import adafruit_requests
import board
import digitalio
import displayio
import socketpool
import ssl
import time
import wifi

from secrets import secrets

# Network setup
pool = socketpool.SocketPool(wifi.radio)
ssl_ctx = ssl.create_default_context()
requests = adafruit_requests.Session(pool, ssl_ctx) 

def check_connection():
    """Checks if we are connected to WiFi.

    Returns:
        True if connected, otherwise False
    """
    if wifi.radio.ap_info:
        return True
    return False

def connect():
    """Connects to the Access Point.

    Returns:
        True if connection was successful, otherwise False
    """
    wifi.radio.connect(secrets['ssid'], secrets['password'])
    for i in range(5):
        if check_connection():
            print('Connected to %s' % secrets['ssid'])
            return True
        time.sleep((i+1) * 10)
    return False

def set_image(file):
    """Displays an image.

    The image needs to be 296x128

    Args:
        file: The path to the 'bmp' to display
    """
    with open(file, 'rb') as f:
        disp = board.DISPLAY
        bitmap = displayio.OnDiskBitmap(f)
        tile_grid = displayio.TileGrid(
            bitmap, pixel_shader=getattr(bitmap, 'pixel_shader', displayio.ColorConverter()))
        group = displayio.Group()
        group.append(tile_grid)
        disp.show(group)
        time.sleep(disp.time_to_refresh + 0.01)
        disp.refresh()

def send_post(url):
    '''Sends a POST to the URL.

    Args:
        url: The URL to send a POST request
    Returns:
        True if 200 status code, otherwise False
    '''
    if not check_connection():
        print('Got disconnected... reconnecting')
        connect()
    print('Sending request to: %s' % url)
    try:
        response = requests.post(url)
        if response.status_code == 200:
            return True
        else:
            print(response)
    except Exception as e:
        print(e)
        print(wifi.radio.ap_info)
    return False

def main():
    set_image('/images/pleasewait.bmp')
    if connect():
        set_image('/images/roarbg.bmp')
        btn1 = digitalio.DigitalInOut(board.BUTTON_A)
        btn1.direction = digitalio.Direction.INPUT
        btn1.pull = digitalio.Pull.UP
        btn2 = digitalio.DigitalInOut(board.BUTTON_B)
        btn2.direction = digitalio.Direction.INPUT
        btn2.pull = digitalio.Pull.UP
        btn3 = digitalio.DigitalInOut(board.BUTTON_C)
        btn3.direction = digitalio.Direction.INPUT
        btn3.pull = digitalio.Pull.UP
        btn4 = digitalio.DigitalInOut(board.BUTTON_D)
        btn4.direction = digitalio.Direction.INPUT
        btn4.pull = digitalio.Pull.UP
        base_url = 'http://home.box:8123/api/webhook/'
        while True:
            if not btn1.value:
                # pressed
                print('Button 1 pressed')
                if send_post(base_url + secrets['roar-trigger']):
                    print('Successfully sent POST request')
                    time.sleep(5)
                else:
                    print('Error: Failed to send POST request') 
            elif not btn2.value:
                print('Button 2 pressed')
                if send_post(base_url + secrets['think-of-what-you-done-trigger']):
                    print('Successfully sent POST request')
                    time.sleep(5)
            elif not btn3.value:
                print('Button 3 pressed')
                if send_post(base_url + secrets['lights-on-trigger']):
                    print('Successfully Sent POST request')
                    time.sleep(5)
            elif not btn4.value:
                print('Button 4 pressed')
                if send_post(base_url + secrets['lights-off-trigger']):
                    print('Successfully Sent POST request')
                    time.sleep(5)
            time.sleep(0.1)  # sleep for debounce

main()
