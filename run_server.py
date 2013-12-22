#!/usr/bin/env python

import subprocess
import os.path

SCRIPT_DIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))

def run_server():
  startserver_cwd = os.path.join(SCRIPT_DIR, 'server')
  startserver_args = ['npm', 'test']

  # Run the server!
  startserver_cmd = subprocess.Popen(startserver_args, cwd=startserver_cwd)

  return startserver_cmd

def hg_download_latest():
  """Update the tree to the latest state, and return whether or not a new revision is available"""

  # Update the tree
  hgfetch_args = ['hg', 'pull']
  hgfetch_cmd = subprocess.Popen(hgfetch_args, cwd=SCRIPT_DIR)
  hgfetch_cmd.check_call()


  # TODO(from yuzisee): hg id -i -r <branchname> <repourl> # gives the hash of the revision on that server
  #                     If there's a version different than the one currently in your working copy, get it
  

if __name__ == "__main__":
  
  while True:
    running_server = run_server()

    # TODO(from yuzisee): if hg_download_latest(): running_server.terminate(), time.sleep(5.0), running_server.kill()
    
