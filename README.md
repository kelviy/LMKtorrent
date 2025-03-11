# LMKtorrent
CSC3002 – Networks Assignment 1 – 2025 Socket programming project. Due 17 March 2025

# PROPOSED OVERVIEW
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
0. Has 3 states to send to leacher (states names are currently outdated. Need to update)
    1. Available    (sent if not occupied)
    2. Connected    (sent to connected leecher)
    3. Unavailable  (sent if connected and another leecher requests download)
1. One Thread to listen for connections and send a response on state 
2. Another thread should also sends pings to tracker
3. Another thread to send file chunk to leechers (single / fixed size threads)

1. Separate request to update and upload file name list over tcp. UDP to request the server to make a tcp request ready to receive

Note: Currently no queue system available for seeder
Note: Selecter in progress for faster multithreading

TRACKER 
1. Be single threaded program
2. UDP Requests are only a single receive, execute and send cycle

Note: File_Name size list limitation can be solved by implementing -> sent and received over another TCP connection
