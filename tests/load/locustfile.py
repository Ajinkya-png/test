from locust import HttpUser, task, between
import random, json

class VoiceUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task
    def ping_health(self):
        """Check API health endpoint"""
        self.client.get("/api/v1/monitoring/health")

    @task(5)
    def create_intent(self):
        """Simulate payment intent creation (frequent task)"""
        payload = {"amount_cents": random.choice([50, 100, 200, 500]), "currency": "inr"}
        headers = {"Content-Type": "application/json"}
        self.client.post("/api/v1/payments/create-intent", json=payload, headers=headers)
