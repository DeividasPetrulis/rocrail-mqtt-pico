# rocrail-mqtt-pico

A minimal proof of concept showing Rocrail talking to a Raspberry Pi Pico W through an MQTT broker.

## How it works

1. The Pico W joins your Wi-Fi.
2. It connects to the Mosquitto broker running on your computer.
3. It prints every Rocrail message (topics `rocrail/service/...`) and blinks the LED. Loco commands are decoded into address, speed and direction.
4. Each press of the BOOTSEL button switches the sensor with address 1 in Rocrail on or off (topic `rocrail/service/field`).

## Requirements

- Raspberry Pi Pico W and a 2.4 GHz Wi-Fi network
- [Rocrail](https://www.rocrail-wiki.net)
- [Mosquitto](https://mosquitto.org) MQTT broker
- [MicroPython](https://micropython.org/download/RPI_PICO_W/) for the Pico W, with the `umqtt.simple` library
- [mpremote](https://pypi.org/project/mpremote/) to copy files to the Pico

Tested with Mosquitto 2.0.22, MicroPython 1.29.0 and mpremote 1.29.0.

## Setup

1. **Broker:** add these two lines to Mosquitto's config file, so it accepts connections from other devices:
   ```
   listener 1883 0.0.0.0
   allow_anonymous true
   ```
2. **Rocrail:**
   - In Rocrail properties → Service → MQTT, set the host to the broker's address (`localhost` if it runs on the same computer) and the port to `1883`. Then restart Rocrail.
   - You want your track plan to have a loco (any address) and a sensor with address 1. The Rocrail demo plan has both.

   This was tested with Rocrail's built-in virtual command station, which is present by default in the demo plan.
3. **MicroPython:** hold BOOTSEL while plugging in the Pico, then drag the `.uf2` file onto the `RPI-RP2` drive.
4. **Config:** copy `config.example.py` to `config.py` and fill in your Wi-Fi details and the broker's IP address.
5. **Copy the library and files.** Once MicroPython runs, the Pico no longer shows up as a drive, so files go over USB with a tool:
   ```bash
   pip install mpremote
   mpremote mip install umqtt.simple
   mpremote cp main.py config.py :
   mpremote run main.py
   ```

## Try it

Watch all traffic on the broker:

```bash
mosquitto_sub -h localhost -t '#' -v
```

Change a loco's speed in Rocrail and the Pico prints the command. Press BOOTSEL and sensor 1 turns on in Rocrail, press it again and the sensor turns off.