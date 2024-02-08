from locust import HttpUser, task, LoadTestShape, TaskSet, constant

class ClientUserTasks(TaskSet):
    #wait_time=constant(1)
    @task
    def client_user(self):
        self.client.get("/")


class User(HttpUser):
    wait_time = constant(1)
    tasks = {ClientUserTasks}


class MyCustomShape(LoadTestShape):
    stages = [ 
        {"duration": 15, "users": 0, "spawn_rate": 10},
        {"duration": 60, "users": 5, "spawn_rate": 10},
        {"duration": 105, "users": 20, "spawn_rate": 10},
        {"duration": 150, "users": 40, "spawn_rate": 10},
        {"duration": 195, "users": 60, "spawn_rate": 10},
        {"duration": 240, "users": 40, "spawn_rate": 10},
        {"duration": 285, "users": 20, "spawn_rate": 10},
        {"duration": 330, "users": 5, "spawn_rate": 10},
        {"duration": 310, "users": 0, "spawn_rate": 10},
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

