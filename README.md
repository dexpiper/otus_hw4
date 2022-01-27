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

Results (with -w 3):

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
Time taken for tests:   20.618 seconds
Complete requests:      50000
Failed requests:        0
Total transferred:      25700000 bytes
HTML transferred:       18250000 bytes
Requests per second:    2425.02 [#/sec] (mean)
Time per request:       41.237 [ms] (mean)
Time per request:       0.412 [ms] (mean, across all concurrent requests)
Transfer rate:          1217.24 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    3  54.6      0    1035
Processing:     2   38  12.7     39     873
Waiting:        2   38  12.7     39     873
Total:          8   41  61.3     39    1885

Percentage of the requests served within a certain time (ms)
  50%     39
  66%     39
  75%     40
  80%     40
  90%     42
  95%     44
  98%     49
  99%     55
 100%   1885 (longest request)