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

This is ApacheBench, Version 2.3 <$Revision: 1879490 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 5000 requests
Completed 10000 requests
Completed 15000 requests
Completed 20000 requests
Completed 25000 requests
Completed 30000 requests
Completed 35000 requests
Completed 40000 requests
Completed 45000 requests
Completed 50000 requests
Finished 50000 requests


Server Software:        OTUServer
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        365 bytes

Concurrency Level:      100
Time taken for tests:   34.430 seconds
Complete requests:      50000
Failed requests:        36
   (Connect: 0, Receive: 0, Length: 36, Exceptions: 0)
Total transferred:      25681496 bytes
HTML transferred:       18236860 bytes
Requests per second:    1452.21 [#/sec] (mean)
Time per request:       68.860 [ms] (mean)
Time per request:       0.689 [ms] (mean, across all concurrent requests)
Transfer rate:          728.42 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0   21 168.5      0    3051
Processing:     1   17 463.2      4   33401
Waiting:        1   12 422.5      4   33401
Total:          1   38 512.3      4   34425

Percentage of the requests served within a certain time (ms)
  50%      4
  66%      5
  75%      5
  80%      5
  90%      5
  95%      6
  98%     13
  99%   1027
 100%  34425 (longest request)