from .defaults import *

try:
    from .local import *
except ImportError:
    pass
