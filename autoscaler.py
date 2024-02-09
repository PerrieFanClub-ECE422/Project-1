import docker
import requests
import time
from datetime import datetime
import matplotlib.pyplot as plt


application_size_data = []
response_time_data=[]
time_data_size = []
time_data_response = []

UPPER_RESPONSE_THRESHOLD = 3
LOWER_RESPONSE_THRESHOLD = 2
SCALE_IN_FACTOR = 0.5
SCALE_OUT_FACTOR = 2
MONITOR_PERIOD = 20
MAX_CONTAINERS = 128
MIN_CONTAINERS = 1
scaling_enabled = False

# docker client
try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
except Exception as exc:
    print("client error = ", exc)
    exit()

# get swarm metric output
def get_metrics():
    try:
        metric_response = requests.get(current_ip)
        if metric_response.status_code == 200:
            return metric_response.text
        else:
            print("status code error")
            return None
    except Exception as e:
        print("Get Metrics Error:", e)


# time the get_metrics() func
def get_metrics_time():
    start_response_time = time.time()
    get_metrics()
    end_response_time = time.time() - start_response_time
    return end_response_time
    

def get_current_containers():
    app_name_web_service = client.services.get("app_name_web")
    app_name_web_tasks = app_name_web_service.tasks(filters={"service": app_name_web_service.id})
    running_web_tasks = [task for task in app_name_web_tasks if task["Status"]["State"] == "running"]
    return len(running_web_tasks)

def wait_until_container_count(target_count):
    while True:
        current_count = get_current_containers()
        if current_count == target_count:
            print("Target container count reached:", target_count)
            break
        print("Waiting for container count to reach", target_count, "Current count:", current_count)
        time.sleep(5)

def scale_service(scale_amount):
    try:
        service = client.services.get("app_name_web")
        service.scale(scale_amount)
        print("*** Service Scale Amount = ", scale_amount, " ***")
        wait_until_container_count(scale_amount)
    except Exception as err:
        print("Error Scaling: ", err)


def update_size_plot():
    print("Updating application size plot")
    application_size_data.append(get_current_containers())
    time_data_size.append(datetime.now())
    plt.plot(time_data_size, application_size_data, 'b-')
    plt.title('Number of Containers over Time')
    plt.xlabel('Time')
    plt.ylabel('# of Containers')
    plt.savefig("application_size_plot.png")

# autoscale func
def autoscale():

    while True:
        total_response_time = 0
        num_samples = 0
        start_response_time = time.time()
        # get metric time across a span of 20 seconds
        while time.time() - start_response_time < MONITOR_PERIOD:

            metric_time = get_metrics_time()

            if metric_time:
                update_size_plot()
                num_samples += 1
                print("\tSample #", num_samples)
                total_response_time += metric_time
                print("\tMetric = ", metric_time, "\tTotal = ", total_response_time)
            else:
                print(">>> ERROR - Could not get metric time")

            print("\tCurrent Containers: ", get_current_containers())

        # check to see if there are any samples
        if num_samples > 0:
            average_response_time = total_response_time / num_samples
            print("*** Average Response time: ", average_response_time, " ***")     

            if scaling_enabled and average_response_time > UPPER_RESPONSE_THRESHOLD:
                print("*** Average Response Time > Upper Response Threshold= ", UPPER_RESPONSE_THRESHOLD, " ***")
                print("*** Scaling Enabled therefore Scale out! ***")
                print("*** Current Containers: ", get_current_containers(), "    Scale out Factor: ", SCALE_OUT_FACTOR, " ***")
                scale_service(min(MAX_CONTAINERS,get_current_containers() * SCALE_OUT_FACTOR))
            
            elif scaling_enabled and average_response_time < LOWER_RESPONSE_THRESHOLD:
                print("*** Average Response Time < Lower Response Threshold= ", LOWER_RESPONSE_THRESHOLD, " ***")
                print("*** Scaling Enabled therefore Scale in! ***")
                print("Current Containers: ", get_current_containers(), "    Scale in Factor: ", SCALE_IN_FACTOR)
                scale_service(max(MIN_CONTAINERS, int(get_current_containers() * SCALE_IN_FACTOR)))


if __name__ == "__main__":
    global current_ip
    userIp = input("Enter swarm manager IP: ")
    current_ip = "http://"+ userIp + ":8000"
    initContainers = int(input("Enter the amount of Docker Containers you want to start with: "))
    userInput = input("Run with autoscaling? [y/n]  > ")
    
    scale_service(initContainers)

    if userInput.lower() == "y":
        print("SCALING HAS BEEN ENABLED")
        scaling_enabled = True
    else:
        scaling_enabled = False
        print("SCALING HAS BEEN DISABLED")

    print("Connecting to IP: ", current_ip)
    autoscale()