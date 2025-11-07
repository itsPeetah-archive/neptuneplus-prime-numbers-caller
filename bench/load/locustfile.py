from locust import HttpUser, task, between, LoadTestShape, events
import random
from time import time_ns, time
import requests

# ENDPOINT
COUNT = 2
PRIME_MIN = 10_000
PRIME_MAX = 20_000
CALLER_MODE = "sequential"

individual_requests_log = []

HOST_SERVER = "http://host.docker.internal:3000"
FUNCTION_NAME_DEPS = "prime-numbers-caller-withdeps"
FUNCTION_NAME_NODEPS = "prime-numbers-caller-nodeps"

IS_RUNNING_TEST = False
START_TEST_TIME = time()

RANDOM_SEED = 1


def get_upper_bound():
    return random.randint(PRIME_MIN // 1000, PRIME_MAX // 1000) * 1000


class PrimeNumbersEnjoyer(HttpUser):
    host = f"http://dispatcher.default.svc.cluster.local/function/openfaas-fn/{FUNCTION_NAME_DEPS}"
    weight = 1
    wait_time = between(1.0, 1.5)

    @task
    def enjoy_prime_numbers(self):
        upperBound = get_upper_bound()
        r = self.client.get(f"/{CALLER_MODE}?count={COUNT}&upperBound={upperBound}")


class RandomStepLoadShape(LoadTestShape):
    """
    600-second test with 50-second random steps between 20 and 120 users.
    First step always 20 users.
    Changes (up or down) happen immediately at each step.
    Uses a local random instance for isolation.
    """

    step_time = 50
    test_duration = 600
    min_users = 20
    max_users = 120
    spawn_rate = 1

    def __init__(self):
        super().__init__()
        self.local_random = random.Random(RANDOM_SEED)
        self.last_step = None
        self.current_user_count = 0
        self.spawn_rate = 1

    def tick(self):
        run_time = self.get_run_time()
        if run_time > self.test_duration:
            return None  # End test

        if self.step_time > 0:
            step = int(run_time // self.step_time)
        else:
            step = 0

        if step != self.last_step:
            if step == 0:
                self.local_random = random.Random(RANDOM_SEED)
                new_user_count = self.min_users
            else:
                new_user_count = self.local_random.randint(
                    self.min_users, self.max_users
                )

            # Calculate spawn rate as the absolute delta (instant change)
            self.spawn_rate = abs(new_user_count - self.current_user_count)

            self.current_user_count = new_user_count
            self.last_step = step

        return (self.current_user_count, self.spawn_rate)


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

    @environment.web_ui.app.route("/setcount/<count>")
    def setcount(count):
        global COUNT
        print("setting count to", count)
        COUNT = int(count)
        return f"count is now {COUNT}\n"

    @environment.web_ui.app.route("/setmaxp/<maxp>")
    def setmaxp(maxp):
        global PRIME_MAX
        print("setting prime max to", maxp)
        PRIME_MAX = int(maxp)
        return f"prime_max is now {PRIME_MAX}\n"

    @environment.web_ui.app.route("/setminp/<minp>")
    def setminp(minp):
        global PRIME_MIN
        print("setting prime min to", minp)
        PRIME_MIN = int(minp)
        return f"prime_min is now {PRIME_MIN}\n"

    @environment.web_ui.app.route("/setmode/<mode>")
    def set_caller_mode(mode):
        global CALLER_MODE
        print("setting caller mode to", mode)
        CALLER_MODE = mode if mode == "concurrent" else "sequential"
        return f"caller_mode is now {CALLER_MODE}\n"

    @environment.web_ui.app.route("/getsettings")
    def getsettings():
        return f"settings:\n- CALLER MODE: {CALLER_MODE}\n- COUNT: {COUNT}\n- PRIME_MIN: {PRIME_MIN}\n- PRIME_MAX: {PRIME_MAX}\n-RANDOM_SEED: {RANDOM_SEED}\n"

    @environment.web_ui.app.route("/is_test_running")
    def is_test_running():
        return "YE" if IS_RUNNING_TEST else "NO"

    @environment.web_ui.app.route("/getstarttime")
    def getstarttime():
        return f"{START_TEST_TIME}"

    @environment.web_ui.app.route("/setseed/seedp")
    def setseed(seedp):
        global RANDOM_SEED
        print("setting seed min to", seedp)
        RANDOM_SEED = int(seedp)
        return f"random seed is now {RANDOM_SEED}\n"


@events.test_start.add_listener
def on_test_start(environment, **kw):
    print("test started")
    global IS_RUNNING_TEST, START_TEST_TIME
    IS_RUNNING_TEST = True
    START_TEST_TIME = time()
    requests.get(HOST_SERVER + "/start")


@events.test_stop.add_listener
def on_test_stop(environment, **kw):
    print("test stopped")
    global IS_RUNNING_TEST
    IS_RUNNING_TEST = False
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
