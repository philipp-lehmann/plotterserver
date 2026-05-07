# Bail out if python is less than 3.9
import sys
MIN_VERSION = (3, 9)
if sys.version_info < MIN_VERSION:
    sys.exit("NextDraw software must be run with python 3.9 or greater.")
