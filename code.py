"""roar-tag

A MagTag program to trigger a Home Assistant webhook.

This mainly connects to internet and waits for a button press. When a button
press is received, it sends a POST request to a Home Assistant webhook.
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
        print('Lost connection. Reconnecting...')
        connect()
    pool = socketpool.SocketPool(wifi.radio)
    print('Sending request to: %s' % url)
    requests = adafruit_requests.Session(pool, ssl.create_default_context()) 
    response = requests.post(url)
    if response.status_code == 200:
        return True
    else:
        print(response)
        return False

def main():
    set_image('/images/pleasewait.bmp')
    if connect():
        set_image('/images/roarbg.bmp')
        btn = digitalio.DigitalInOut(board.BUTTON_A)
        btn.direction = digitalio.Direction.INPUT
        btn.pull = digitalio.Pull.UP
        while True:
            if not btn.value:
                # pressed
                print('BTN pressed')
                if send_post('http://home.box:8123/api/webhook/roar-trigger'):
                    print('Successfully sent POST request')
                    time.sleep(5)
                else:
                    print('Error: Failed to send POST request') 
            time.sleep(0.1)  # sleep for debounce

main()
