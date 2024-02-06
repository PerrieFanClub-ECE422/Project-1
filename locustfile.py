from locust import HttpUser, task

class ClientUser(HttpUser):
    wait_time=constant(1)
    @task
    def client_user(self):
        self.client.get("/")