import docker
import requests
import time
import sys
from datetime import datetime
import matplotlib.pyplot as plt


application_size_data = []
response_time_data=[]
time_data_size = []
time_data_response = []
# current user's swarm endpoint
current_ip = "http://"+ sys.argv[1] + ":8000"

UPPER_RESPONSE_THRESHOLD = 3
LOWER_RESPONSE_THRESHOLD = 2
SCALE_IN_FACTOR = 0.5
SCALE_OUT_FACTOR = 2
MONITOR_PERIOD = 20
MAX_CONTAINERS = 75
MIN_CONTAINERS = 4
scaling_enabled = False

# docker client
try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
except Exception as exc:
    print("client error = ", exc)

# get swarm metric output
def get_metrics():
    try:
        metric_response = requests.get(current_ip)
        if metric_response.status_code == 200:
            # print(metric_response.text)
            return metric_response.text
        else:
            print("status code error")
            return None
    except Exception as e:
        print("Error:", e)


# time the get_metrics() func
def get_metrics_time():
    start_response_time = time.time()
    get_metrics()
    end_response_time = time.time() - start_response_time
    return end_response_time
    

def get_current_containers():
    return len( client.services.get("/app_name_web").tasks() ) - 2


def scale_service(scale_amount):
    try:
        service = client.services.get("app_name_web")
        service.scale(scale_amount)
        print("******* service scale amount === ", scale_amount)
    except Exception as err:
        print("error scaling: ", err)


def update_size_plot():
    print("Updating application size plot")
    application_size_data.append(get_current_containers())
    time_data_size.append(datetime.now())
    plt.plot(time_data_size, application_size_data, 'b-')
    plt.title('Application Size')
    plt.xlabel('Time')
    plt.ylabel('# of Containers')
    plt.savefig("application_size_plot.png")

def update_response_plot(avg_rsp_time):
    print("Updating response size plot")
    response_time_data.append(avg_rsp_time)
    time_data_response.append(datetime.now())
    plt.plot(time_data_response,response_time_data,'b-')
    plt.title('Average Response Time')
    plt.xlabel('Time')
    plt.ylabel('Average Response Time')
    plt.savefig("response_time_plot.png")

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
                print("\tsample #", num_samples)
                total_response_time += metric_time
                print("\tmetric = ", metric_time, "\ttotal = ", total_response_time)
            else:
                print(">>> ERROR - could not get metric time")

            print("\tcurr containers: ", get_current_containers())
            print("")
            time.sleep(1)


        # check to see if there are any samples
        if num_samples > 0:

            average_response_time = total_response_time / num_samples
            print("******* avgresp time: ", average_response_time)
            
            #update_response_plot(average_response_time)
            if average_response_time > UPPER_RESPONSE_THRESHOLD and scaling_enabled:
                print("getcurrcon ", get_current_containers(), "    calcscaleout ", SCALE_OUT_FACTOR)
                scale_service( min(MAX_CONTAINERS, int( get_current_containers() * SCALE_OUT_FACTOR) ) )
            
            elif average_response_time < LOWER_RESPONSE_THRESHOLD and scaling_enabled:
                print("getcurrcon ", get_current_containers(), "    calcscalein ", SCALE_IN_FACTOR)
                scale_service( max(MIN_CONTAINERS, int( get_current_containers() * SCALE_IN_FACTOR )) )

        print("!!!!!!! sleeping")
        time.sleep(1)
        print("!!!!!!! done sleeping")
        print("")



if __name__ == "__main__":
    userInput = input("Run with autoscaling? [y/n]  > ")

    service = client.services.get("app_name_web")
    service.scale(MIN_CONTAINERS)

    if userInput.lower() == "y":
        print("SCALING HAS BEEN ENABLED")
        scaling_enabled = True
    else:
        scaling_enabled = False
        print("SCALING HAS BEEN DISABLED")

    autoscale()