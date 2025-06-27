#!/usr/bin/env python
import os
import sys

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, src_path)

if __name__ == "__main__":
    from write_a_book_with_flows.main import kickoff
    kickoff() 