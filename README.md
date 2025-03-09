# LMKtorrent
CSC3002 – Networks Assignment 1 – 2025 Socket programming project. Due 17 March 2025

# Specifications (so far - simplied)
- Interested in sending a single file (Zipped)
- Run all three components on the loop back interface (127.0.0.1) as seperate processes
- Print status on command line

## Proposed Rough Protocol
### Leacher
1. Contact Tracker for Seeder and File Information
2. Attempt to connect to seeder. Go to next seeder if time-out
3. Seeder sends files as parts
4. Rebuild parts

### Seeder
1. Contacts the Tracker to inform that it's still up
2. Can ask to join the list of seeders
3. Listens for Leecher Connections
4. Will only connect to 1 peer. (let's say no queue for now)
5. Opens file in binary to send desired bytes. (use file pointer to go to desired location - I think seek() method)
6. Finish, and start listening again

### Tracker
1. Capable of adding seeders that ask to join. AKA listens for seeders
2. Has a seeder expire timer. Seeder has to contact the tracker before the timer expires, else it is removed
3. Listens for leechers and sends meta data.

## General Notes:
1. You can optionally create a virtual environment since we are using python. This will help if we are using additional packages 
2. Need to add a checker to see if all data was sent correctly


-------
# REQUEST_FILE
What I understand: leecher requests (file information + seeder list) for each file from the tracker. 
1.  The seeder list received from tracker does not correspond to if the leecher can actually download from the seeder. 
    Unless the seeder constantly updates it status to send files to the tracker. Extra complexity and wasted bandwidth

If two leechers and the first seeder is sending to the first leecher. The second leecher will block on the first seeder instead skipping 
checking other seeders. 

I think because seeder should ping tracker regardless of if it is connected or not. Only stops pinging if seeder server is stopped
Tracker keeps a list of potential active seeders. Frequency of seeder changing states can be too fast. So responsibility of actually
trying to connect falls on leecher

2. File not found check should be done on the seeder side as thats there the file is. 
3. The same seeder address will be stored and sent multiple times unnecessarily

# PROPOSE INSTEAD
LEACHER \
0. TCP file list info from tracker
1. Leacher gets a list potential active seeders from tracker
2. Leacher initiates a connection with multiple seeders. Effectively blocking other leachers from connecting to the seeder
3. Once all seeders or up till desired seeders (predetermined fixed amount) is connected:
    1. Calculate the file chunks needed from each seeder
    2. Request and Download file chunks (hashing and resending here) + (parallel downloading on different threads)
    3. Close the connection after file chunk is downloaded
4. Now a single file is downloaded. Repeat from step 1 or 2 for each requested file
* allows not only one leecher to hog all the resources at once (prob implement a new queue request for better implementation)

SEEDER \
0. Has 3 states to send to leacher
    1. Available    (sent if not occupied)
    2. Connected    (sent to connected leecher)
    3. Unavailable  (sent if connected and another leecher requests download)
1. One Thread to listen for connections and send a response on state 
2. Another thread should also sends pings to tracker
3. Another thread to send file chunk to leechers (single / fixed size threads)

1. Separate request to update and upload file name list over tcp. UDP to request the server to make a tcp request ready to receive

TRACKER 
1. Be single threaded program
2. UDP Requests are only a single receive, execute and send cycle
3. File_Name is sent and received over another TCP connection

