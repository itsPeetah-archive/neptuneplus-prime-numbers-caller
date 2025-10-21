from locust import HttpUser, task, between, LoadTestShape, events
from random import randint
from time import time_ns, time
import requests


COUNT = 2

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


# --- Custom Load Shape Definition ---


class PaddedLinearRampShape(LoadTestShape):
    """
    A custom load shape that implements a flat padding, a linear ramp, and then another flat padding.
    """

    start_users = 10  # Users during the initial padding
    peak_users = 100  # Peak number of users during the ramp
    end_users = 100  # Users during the final padding (can be 0)

    # Define your test parameters here
    initial_padding_duration = 60  # seconds at the start
    ramp_duration = peak_users - start_users  # seconds for the linear ramp
    final_padding_duration = 120  # seconds at the end

    # Calculate total test time
    total_time = initial_padding_duration + ramp_duration + final_padding_duration

    # Calculate the change in users per second during the ramp
    user_change_per_sec = (peak_users - start_users) / ramp_duration

    # Set a base spawn rate for the ramp-up/down
    # A higher spawn rate will make the ramp faster to reach the target users per tick
    ramp_spawn_rate = 1

    def tick(self):
        run_time = self.get_run_time()

        if run_time < self.initial_padding_duration:
            # 1. Initial Padding Phase: Hold at 'start_users'
            user_count = self.start_users
            spawn_rate = (
                self.ramp_spawn_rate
            )  # Spawn rate can be high initially to quickly hit 'start_users'

        elif run_time < self.initial_padding_duration + self.ramp_duration:
            # 2. Linear Ramp Phase
            # Time spent in the ramp phase
            time_in_ramp = run_time - self.initial_padding_duration

            # Calculate current target user count for the linear ramp
            user_count = round(
                self.start_users + (self.user_change_per_sec * time_in_ramp)
            )

            # Ensure user count does not exceed peak_users (for ramp-up) or go below start_users (for ramp-down) if your logic is complex
            user_count = max(0, min(user_count, self.peak_users))  # Basic safeguard

            spawn_rate = self.ramp_spawn_rate

        elif run_time < self.total_time:
            # 3. Final Padding Phase: Hold at 'end_users'
            user_count = self.end_users
            spawn_rate = (
                self.ramp_spawn_rate
            )  # Use a spawn rate to maintain the target user count

        else:
            # Stop the test
            return None

        # Return the desired user count and spawn rate
        # spawn_rate determines how fast Locust tries to reach the user_count
        return (user_count, spawn_rate)


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
