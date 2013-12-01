#!/bin/sh

SCRIPTDIR=$(cd $(dirname $0); pwd -P)

cd $SCRIPTDIR/pokerai

# Build it!
if which node-gyp; then
  echo 'node-gyp found OK'
else
  echo "You must have node-gyp installed: sudo npm install -g node-gyp" 1>&2
  exit 70 # EX_SOFTWARE
fi

node-gyp rebuild

