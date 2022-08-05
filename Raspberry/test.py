import requests
from ast import literal_eval

USERNAME="pythoniot"
PASSWORD="P@$$w0rd"

timeSchedule={}
configResp = requests.get("http://127.0.0.1:1234/retrconfig", auth=(USERNAME,PASSWORD))
configuration = literal_eval(configResp.json()['data'])

for config in configuration:
    for time in config['timings']:
        if time in config:
            timeSchedule[time].append({"cylinder":config['cylinderNum'],"dose":config['dosage']})
        else:
            timeSchedule[time] = [{"cylinder":config['cylinderNum'],"dose":config['dosage']}]

for i in timeSchedule:
    print(i)