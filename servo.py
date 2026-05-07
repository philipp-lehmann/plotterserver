import serial, time

ebb = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
time.sleep(1)

for pos in [6000, 12000, 18000]:
    cmd = f"S2,{pos},4,500\r"
    print("Sending:", cmd.strip())
    ebb.write(cmd.encode())
    time.sleep(1)
    print("Response:", ebb.read_all())

ebb.close()


# def test_serial_raw(self):
#     """Raw serial test - bypass everything."""
print("Testing raw serial access...")
try:
    ebb = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    print(f"Port open: {ebb.is_open}")
    
    # Send a simple query first - ask EBB for its version
    ebb.write(b"V\r")
    time.sleep(0.3)
    response = ebb.read_all()
    print(f"EBB version response: {response}")
    
    # Now send S2
    ebb.write(b"S2,6000,4,500\r")
    time.sleep(1.0)
    response = ebb.read_all()
    print(f"S2 response: {response}")
    
    ebb.close()
    print("Port closed.")
except serial.SerialException as e:
    print(f"Serial error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")