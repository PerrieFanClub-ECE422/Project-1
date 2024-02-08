from locust import HttpUser, task, LoadTestShape, TaskSet, constant

class ClientUserTasks(TaskSet):
    #wait_time=constant(1)
    @task
    def client_user(self):
        self.client.get("/")


class User(HttpUser):
    wait_time = constant(1)
    tasks = {ClientUserTasks}
    host= "http://10.2.8.10:8000/"

class MyCustomShape(LoadTestShape):
    stages = [ 
        {"duration": 45, "users": 0, "spawn_rate": 10},
        {"duration": 90, "users": 5, "spawn_rate": 10},
        {"duration": 135, "users": 20, "spawn_rate": 10},
        {"duration": 180, "users": 40, "spawn_rate": 10},
        {"duration": 225, "users": 60, "spawn_rate": 10},
        {"duration": 270, "users": 40, "spawn_rate": 10},
        {"duration": 315, "users": 20, "spawn_rate": 10},
        {"duration": 360, "users": 5, "spawn_rate": 10},
        {"duration": 405, "users": 0, "spawn_rate": 10},
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                try:
                    tick_data = (stage["users"], stage["spawn_rate"])
                except KeyError:
                    tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data

