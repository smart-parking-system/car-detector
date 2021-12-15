#!/usr/bin/env python3

import sys
from typing import Dict, Any

from detect import MotionDetector
from server import Server, DEFAULT_URL

VERSION = '0.1'


def parse_args() -> Dict:
    def get_next(i) -> Any:
        if i < len(sys.argv):
            return sys.argv[i]
        else:
            exit('Expected a value after ' + sys.argv[i - 1])

    result, i = {'host': '0.0.0.0', 'port': 5000, 'src': DEFAULT_URL}, 1
    while i < len(sys.argv):
        if sys.argv[i] == '--help':
            print(f'SPS Car Detector v{VERSION}\n'
                  f'Usage: python3 {sys.argv[0]} [OPTIONS] [SOURCE]\n'
                  'Options:\n'
                  '  --help               - Shows this message\n'
                  '  -p PORT, --port PORT - Sets server port\n'
                  '  -h HOST, --host HOST - Sets server host')
            exit(0)
        elif sys.argv[i] in ['-p', '--port']:
            result['port'] = get_next(i := i + 1)
        elif sys.argv[i] in ['-h', '--host']:
            result['host'] = get_next(i := i + 1)
        elif sys.argv[i] in ['-v']:
            result['video'] = get_next(i := i + 1)
        else:
            result['src'] = sys.argv[i]
            i += 1
    return result


if __name__ == '__main__':
    args = parse_args()
    Server(MotionDetector(args['src'])).run(args)
