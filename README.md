# OTUServer

Example simple HTTP server written around sockets. Spawns requested number of workers in separate threads ('pool of threads' was not 100% implemented). Serves "HEAD" and "GET" HTTP-requests.

Tests (httptest.py and httptest dir): https://github.com/s-stupnikov/http-test-suite

## Table of contents
1. [Usage](#usage)
2. [Benchmark](#benchmark)


## Usage

Run:

`$ (sudo) python3 httpd.py [host, positional argument (default - localhost)] [-p, --port (default: 8080)] [-r, --root (defaults to CWD)] [-w, --workers  (default: 3)] [-t, --timeout (default: 3.0)] [-l, --log (defaults to None)]`

* Running on port 80 may ask a super user privileges
* if a logfile provided with -l (--log), log messages would go into it instead of stdout

Test page:

http://localhost/httptest/wikipedia_russia.html

All tests of httptest.py completed successfully.


## Benchmark

Results (with -w 12):

`$ ab -n 50000 -c 100 -r http://localhost:8080/`

https://github.com/dexpiper/otus_hw4/blob/main/benchmark.txt
