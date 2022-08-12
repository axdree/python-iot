import requests
from ast import literal_eval

USERNAME="pythoniot"
PASSWORD="P@$$w0rd"

timeSchedule={}
configResp = requests.get("http://development.andreyap.com:7631/retrconfig", auth=(USERNAME,PASSWORD))
configuration = literal_eval(configResp.json()['data'])

for config in configuration:
    print(config)
    for time in config['timings']:
        if time in timeSchedule:
            print("time")
            timeSchedule[time].append({"cylinder":config['cylinderNum'],"dose":config['dosage']})
        else:
            print("no time")
            timeSchedule[time] = [{"cylinder":config['cylinderNum'],"dose":config['dosage']}]

print(timeSchedule)
# print(configuration)
for i in timeSchedule:
    print(i)