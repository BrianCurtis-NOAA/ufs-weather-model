import machine
import os

machineID = machine.detect_machine()
print(os.environ["MACHINE_ID"])
print(machineID)