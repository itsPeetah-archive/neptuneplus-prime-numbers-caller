from locust import HttpUser, task, between, LoadTestShape, events
from random import randint
from time import time_ns, time
import requests


COUNT = 5

PRIME_MIN = 20_000
PRIME_MAX = 20_000

individual_requests_log = []
HOST_SERVER = "http://host.docker.internal:3000"


class PrimeNumbersEnjoter(HttpUser):
    host = "http://dispatcher.default.svc.cluster.local/function/openfaas-fn/pnc-seq-nodeps"

    wait_time = between(0.5, 1.5)

    @task
    def enjoy_prime_numbers(self):
        upperBound = randint(PRIME_MIN, PRIME_MAX)
        r = self.client.get(f"/sequential?count={COUNT}&upperBound={upperBound}")


@events.init.add_listener
def on_locust_init(environment, **kw):
    @environment.web_ui.app.route("/rt_log")
    def rt_log():
        print("received request at /rt_log")
        return "\n".join(individual_requests_log)

    @environment.web_ui.app.route("/clear_rt_log")
    def clear_rt_log():
        print("received request at /clear_rt_log")
        txt = f"CLEARED {len(individual_requests_log)} LINES:\n"
        txt += "\n".join(individual_requests_log)
        individual_requests_log.clear()
        return txt


@events.test_start.add_listener
def on_test_start(environment, **kw):
    print("test started")
    requests.get(HOST_SERVER + "/start")


@events.test_stop.add_listener
def on_test_stop(environment, **kw):
    print("test stopped")
    requests.get(HOST_SERVER + "/stop")


@events.request.add_listener
def my_request_handler(
    request_type,
    name,
    response_time,
    response_length,
    response,  # The raw response object (e.g., requests.Response)
    context,
    exception,
    start_time,  # Time in seconds since the epoch when the request started (float)
    url,
    **kwargs,
):
    # Calculate the timestamp (when the request completed)
    # The 'start_time' is when the request started. 'response_time' is in milliseconds.
    # Time of completion = start_time + (response_time / 1000)
    completion_timestamp = (start_time * 1000) + response_time

    # Get the status code. If there's an exception, the request failed and there's no status code.
    status_code = response.status_code if response is not None else "N/A (Failed)"

    # Check if an exception occurred to determine success/failure
    status_text = "Success" if exception is None else "Failure"

    txt = f"{completion_timestamp};{response_time};{request_type};{status_code};({status_text});{name}"
    individual_requests_log.append(txt)
