class Request():
    #Sent by seeder to tracker with their file list below it in the format of:
    #   add_seeder
    #   <filename1> <size1>
    #   <filename2> <size2>
    ADD_SEEDER = "add_seeder"


    NOTIFY_TRACKER = "notify_tracker"

    #Sent from tracker to seeder when a successfulc connection has been established.
    #Essentially, when the seeder's file list is recieved.
    CON_EST = "con_est"

    #Typically will say:
    #   "request_file video12.zip 12500 "
    #Used to ask seeder for a specific file that they have.
    #Built-in checking for if seeder has the file.
    REQUEST_FILE = "request_file"