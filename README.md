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
1. You can optionally create a virtual environment since we are using python. This will help if we are using additional packages (which we probably won't)

