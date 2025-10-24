from locust import HttpUser, task, between, LoadTestShape, events
from random import randint
from time import time_ns, time
import requests

COUNT = 2

PRIME_MIN = 10_000
PRIME_MAX = 50_000

individual_requests_log = []

HOST_SERVER = "http://host.docker.internal:3000"
FUNCTION_NAME_DEPS = "prime-numbers-caller-withdeps"
FUNCTION_NAME_NODEPS = "prime-numbers-caller-nodeps"

IS_RUNNING_TEST = False


def get_upper_bound():
    return randint(PRIME_MIN // 1000, PRIME_MAX // 1000) * 1000


class PrimeNumbersEnjoyer_Deps(HttpUser):
    host = f"http://dispatcher.default.svc.cluster.local/function/openfaas-fn/{FUNCTION_NAME_DEPS}"
    weight = 1
    wait_time = between(0.1, 0.6)

    @task
    def enjoy_prime_numbers(self):
        upperBound = get_upper_bound()
        r = self.client.get(f"/sequential?count={COUNT}&upperBound={upperBound}")


# class PrimeNumbersEnjoyer_Nodeps(HttpUser):
#     host = f"http://dispatcher.default.svc.cluster.local/function/openfaas-fn/{FUNCTION_NAME_NODEPS}"
#     weight = 1
#     wait_time = between(0.1, 0.6)

#     @task
#     def enjoy_prime_numbers(self):
#         upperBound = get_upper_bound()
#         r = self.client.get(f"/sequential?count={COUNT}&upperBound={upperBound}")


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

    @environment.web_ui.app.route("/getsettings")
    def getsettings():
        return f"settings:\n- COUNT: {COUNT}\n- PRIME_MIN: {PRIME_MIN}\n- PRIME_MAX: {PRIME_MAX}\n"

    @environment.web_ui.app.route("/is_test_running")
    def is_test_running():
        return "YE" if IS_RUNNING_TEST else "NO"


@events.test_start.add_listener
def on_test_start(environment, **kw):
    print("test started")
    global IS_RUNNING_TEST
    IS_RUNNING_TEST = True
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
