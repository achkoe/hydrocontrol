import subprocess
import time


while True:
    subprocess.run(["/usr/local/bin/flask", "--app", "hydrocontrol.py", "run", "--host", "0.0.0.0"], cwd="/home/pi")
    time.sleep(10)
