# LMKtorrent
CSC3002 – Networks Assignment 1 – 2025 Socket programming project. Due 17 March 2025

# QUICK RUN
1. Create a virtual environment and install PyQt6 for GUI
2. Run auto_run.sh script. This will start seeder and tracker instances on loop back interface (127.0.0.1) on port 12500 nd 12501 respectively. Seeder will default to seeding ./data/ folder
3. Run GUI and type in tracker information. Typing in nothing will default to 127.0.0.1:12500
4. You are now able to download files. By default it will download to ./tmp/ folder

# Manual Run

Running seeder.py or tracker.py with no command line argument will start the script with default parameters. 

To change these parameters add a random command line argument and the script will prompt for required information. 

E.g: `python3 seeder.py adsf`

> NOTE: Typing in nothing for manual input for seeder.py and tracker.py will not default to defualt option - it will crash. This is only on GUI for typing in tracker. 

> NOTE: There is also a CLI GUI provided in peer.py (very barebones)

# OVERVIEW
LEACHER 
1. UDP file list info from tracker
2. Leacher gets a list potential active seeders from tracker (UDP)
3. Leacher initiates a connection with multiple seeders. Effectively blocking other leachers from connecting to the seeder. Has a max parallel connection number setting
4. Once all seeders or up till desired seeders (predetermined fixed amount) is connected:
    1. Calculate the file chunks needed from each seeder
    2. Request and Download file chunks (hashing and resending here) + (parallel downloading on different threads)
    3. Close the connection after file chunk is downloaded
5. Now a single file is downloaded. Repeat from step 1 or 2 for each requested file
* allows not only one leecher to hog all the resources at once (prob implement a new queue request for better implementation)

SEEDER 
1. Has 3 states to send to leacher (states names are currently outdated. Need to update)
    1. Available    (sent if not occupied)
    2. Connected    (sent to connected leecher)
    3. Unavailable  (sent if connected and another leecher requests download)
2. One Thread to listen for connections and send a response on state 
3. Another thread should also sends pings to tracker
4. Another thread to send file chunk to leechers (single / fixed size threads)

Note: Currently no queue system available for seeder

TRACKER 
1. Be single threaded program
2. UDP Requests are only a single receive, execute and send cycle

Note: Have a File_Name size list limitation and can be solved by implementing sending and receiving over another TCP connection (more complex)
