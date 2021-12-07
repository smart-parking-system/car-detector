#!/usr/bin/env python3

from typing import List, Dict, Any
from detect import MotionDetector
from server import Server, DEFAULT_URL
# from pathlib import Path
import sys

VERSION='0.1'

def parse_args() -> Dict:
    def get_next(i) -> Any:
        if i < len(sys.argv):
            return sys.argv[i]
        else:
            exit('Expected a value after ' + sys.argv[i-1])

    result, i = {'host': '0.0.0.0', 'port': 5000, 'src': DEFAULT_URL}, 1
    while (i < len(sys.argv)):
        if sys.argv[i] == '--help':
            print('SPS Car Detector v')
        elif sys.argv[i] in ['-p', '--port']:
            result['port'] = get_next(i:=i+1)
        elif sys.argv[i] in ['-h', '--host']:
            result['host'] = get_next(i:=i+1)
        else:
            result['src'] = sys.argv[i]
            i+=1
    return result

if __name__ == '__main__':
    # Path("data").mkdir(exist_ok=True)
    args = parse_args()
    Server(MotionDetector(args['src'])).run(args)
