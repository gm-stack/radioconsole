from .rooter_webif import RooterBackend
from .test import TestBackend

backends = {
    'test': TestBackend,
    'rooter': RooterBackend
}