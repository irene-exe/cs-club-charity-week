import serial

ser = serial.Serial('COM3', 115200)

controls = {}

while True:
    raw = ser.readline()
    try:
        line = raw.decode('utf-8').strip()
    except:
        continue

    if not line:
        continue

    parts = line.split(",")

    for p in parts:
        if "=" in p:
            key, value = p.split("=")
            controls[key] = int(value)

    # Up is 0, down is 1023, right is 0, left is 1023
    # all binary buttons are 0 when pressed, 1 when not pressed
    print(
        controls["J1X"], controls["J1Y"], controls["J1SW"],
        controls["J2X"], controls["J2Y"], controls["J2SW"],
        controls["B1"], controls["B2"], controls["B3"],
        controls["B4"], controls["B5"], controls["B6"]
    )
