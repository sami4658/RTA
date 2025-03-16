# RTA
A robot.txt crawler that finds robot,txt in websites or IP at the chosen depth
use the tool with -h or --help command to list how it can be used
Must know:
when you choose a depth, it doesnt automatically start from that depth, it builds up to MAXIMUM that level
Example:
python rta.py -d 2 https://www.example.com     goes MAXIMUM to depth level 3 

the -h/--help command:
                                                                                                                                                                 
usage: rta.py [-h] [-d DEPTH] [-t TIMEOUT] [-m MAX_THREADS] [-v] target

Find robots.txt files on websites and IP addresses

positional arguments:
  target                Target website or IP address

options:
  -h, --help            show this help message and exit
  -d, --depth DEPTH     Maximum crawl depth (default: 2)
  -t, --timeout TIMEOUT
                        Request timeout in seconds (default: 10)
  -m, --max-threads MAX_THREADS
                        Maximum number of threads (default: 10)
  -v, --verbose         Enable verbose output
