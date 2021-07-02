import sys
import os

sys.path.insert(0, '{}/'.format(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.postgres import base
