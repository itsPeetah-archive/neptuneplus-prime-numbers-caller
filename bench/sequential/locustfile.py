from locust import HttpUser, task
from random import randint

COUNT = 2


class PrimeNumbersEnjoyer(HttpUser):
    host = "http://localhost:8080/function/openfaas-fn/pnc-seq-deps"
    min_wait = 0.1
    max_wait = 0.6

    @task
    def enjoy_prime_numbers(self):
        upperBound = randint(1_000, 100_000)
        self.client.get(f"/sequential?count={COUNT}&upperBound={upperBound}")
