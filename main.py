import time

import network
import rp2
import ubinascii
from machine import Pin, unique_id
from umqtt.simple import MQTTClient

import config

led = Pin("LED", Pin.OUT)

# Every device on a broker needs its own name.
CLIENT_ID = b"pico-" + ubinascii.hexlify(unique_id())

ALL_ROCRAIL_TOPICS = b"rocrail/service/#"   # the '#' here is a wildcard (meaning every topic under rocrail/service/)
SENSOR_TOPIC = b"rocrail/service/field"     # Rocrail listens here for sensor events
STATUS_TOPIC = b"pico/status"               # our own topic for "online" / "offline" events
SENSOR_ADDR = 1                             # sensor address for this test


def attr(xml, name):
    """Return the value of name="..." in an RCP XML snippet, or None if it isn't there."""
    key = ' %s="' % name
    start = xml.find(key)
    if start < 0:
        return None
    start += len(key)
    return xml[start:xml.find('"', start)]


def on_message(topic, msg):
    """Called by the MQTT library for every message that arrives."""
    led.on()
    text = msg.decode()
    print("<-", topic.decode(), text)
    if text.startswith("<lc"):
        print("   loco command: addr=%s speed V=%s dir=%s" % (attr(text, "addr"), attr(text, "V"), attr(text, "dir")))
    time.sleep_ms(50)  # keep the LED on long enough to see
    led.off()


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return
    print("Joining Wi-Fi", config.WIFI_SSID, end="")
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    for _ in range(40):  # wait up to 20 seconds
        if wlan.isconnected():
            break
        led.toggle()
        print(".", end="")
        time.sleep(0.5)
    led.off()
    if not wlan.isconnected():
        reasons = {-1: "connection failed", -2: "network not found (the Pico W only sees 2.4 GHz)", -3: "wrong password"}
        raise OSError("Wi-Fi: " + reasons.get(wlan.status(), "status %d" % wlan.status()))
    print("\nWi-Fi OK, my IP is", wlan.ifconfig()[0])


def send_sensor(client, state):
    msg = '<fb iid="pico" addr="%d" state="%s"/>' % (SENSOR_ADDR, "true" if state else "false")
    client.publish(SENSOR_TOPIC, msg.encode(), qos=1)
    print("->", SENSOR_TOPIC.decode(), msg)


def run():
    connect_wifi()

    client = MQTTClient(CLIENT_ID, config.BROKER, port=1883, keepalive=30)
    # The "last will" is a message the broker sends for us if we vanish without saying goodbye.
    client.set_last_will(STATUS_TOPIC, b"offline", retain=True)
    client.set_callback(on_message)
    client.connect()
    client.publish(STATUS_TOPIC, b"online", retain=True)
    client.subscribe(ALL_ROCRAIL_TOPICS, qos=1) # QoS 1 means that the broker resends until the Pico confirms, so no command is lost
    print("MQTT OK: connected to", config.BROKER, "as", CLIENT_ID.decode())
    print("Listening on", ALL_ROCRAIL_TOPICS.decode())

    sensor_on = False
    last_ping = time.ticks_ms()
    while True:
        client.check_msg()  # handle a waiting message, if any (does not wait for one)

        if rp2.bootsel_button():
            sensor_on = not sensor_on
            send_sensor(client, sensor_on)
            while rp2.bootsel_button():  # wait for release
                time.sleep_ms(10)

        # Tell the broker we are still here, or it drops us after the keepalive time.
        if time.ticks_diff(time.ticks_ms(), last_ping) > 20000:
            client.ping()
            last_ping = time.ticks_ms()

        time.sleep_ms(20)


while True:
    try:
        run()
    except OSError as e:
        print("Connection problem:", e, "- retrying in 5s")
        time.sleep(5)