import pytest
import os
import sys

# Inject backend path
sys.path.insert(0, os.path.abspath('backend'))

if __name__ == '__main__':
    pytest.main(['tests/', '-v'])
