# OTUServer

Example simple HTTP server written around sockets. Spawns requested number of workers in separate threads ('pool of threads' was not 100% implemented). Serves "HEAD" and "GET" HTTP-requests.

Tests (httptest.py and httptest dir): https://github.com/s-stupnikov/http-test-suite

## Table of contents
1. [Usage](#usage)
2. [Benchmark](#benchmark)


## Usage

Run:

`$ (sudo) python3 httpd.py [host, positional argument (default - localhost)] [-p, --port (default: 8080)] [-r, --root (defaults to CWD)] [-w, --workers  (default: 3)] [-t, --timeout (default: 3.0)] [-l, --log (defaults to None)] [-v, --level , int from 0 to 40 (defaults to INFO)]`

* Running on port 80 may ask a super user privileges
* if a logfile provided with -l (--log), log messages would go into it instead of stdout

Test page:

http://localhost/httptest/wikipedia_russia.html

All tests of httptest.py completed successfully.


## Benchmark

`$ ab -n 50000 -c 100 -r http://localhost:8080/`

This is ApacheBench, Version 2.3 <$Revision: 1879490 $>
<...>

Server Software:        OTUServer
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        365 bytes

Concurrency Level:      100
Time taken for tests:   23.643 seconds
Complete requests:      50000
Failed requests:        0
Total transferred:      25700000 bytes
HTML transferred:       18250000 bytes
Requests per second:    2114.79 [#/sec] (mean)
Time per request:       47.286 [ms] (mean)
Time per request:       0.473 [ms] (mean, across all concurrent requests)
Transfer rate:          1061.53 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    2  46.3      0    1032
Processing:     2   45   5.8     45     465
Waiting:        1   45   5.7     45     465
Total:          7   47  48.0     45    1492

Percentage of the requests served within a certain time (ms)
  50%     45
  66%     46
  75%     47
  80%     47
  90%     49
  95%     52
  98%     57
  99%     61
 100%   1492 (longest request)
