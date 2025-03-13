#! /bin/bash
if [[ "$1" == "kill" ]]; then
    echo "Killing seeder and tracker"
    kill $(ps -eaf | grep -E "src/tracker.py|src/seeder.py" | grep -v grep | awk '{print $2}')
else
    echo "Running seeder and tracker and leacher"
    python3 src/tracker.py &
    python3 src/seeder.py &

    echo 'proccess will redirect output to tracker and seeder log textfiles'
    sleep 1
    echo "Proccess IDs:"
    echo $(ps -eaf | grep -E "src/tracker.py|src/seeder.py" | grep -v grep | awk '{print $9, $2}')

    python3 src/leacher.py
fi
