class Request():
    ADD_SEEDER = "add_seeder"
    NOTIFY_TRACKER = "notify_tracker"
    REQUEST_METADATA = "request_meta"

    #Typically will say:
    #   "request_file video12.zip 12500 "

    #Used to ask seeder for a specific file that they have.
    #Built-in checking for if seeder has the file.
    REQUEST_FILE = "request_file"


    #Many use cases for success.
    #Such as:
    #   "success request_file"
    SUCCESS = "success"
    FAIL = "fail"
