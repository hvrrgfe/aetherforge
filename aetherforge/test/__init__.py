import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aetherforge.api.tools import ToolResult

def run_tests(engine, runtime=None):
  from aetherforge.test.test_runner import TestRunner
  tr = TestRunner(engine, runtime)
  return tr.run_all()
