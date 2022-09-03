echo "1" > /home/pi/log.txt
sleep 60
echo "2" >> /home/pi/log.txt 
python3 /home/pi/respawn.py  2>&1 >> log.txt
echo "3" >> /home/pi/log.txt

