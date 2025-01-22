# map-experiments
Experiments with OpenStreetMap

## Prerequisites

You will need a python venv with "drawsvg" and "lxml" installed.

## Install guide
```bash
# install the required system packages
$ sudo apt install osmosis

# clone the repo
$ git clone https://github.com/owoalex/map-experiments.git
$ cd map-experiments

# install the required python packages
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install drawsvg[all]
$ pip3 install lxml
```

## Generate a map tile
```bash
$ wget https://download.geofabrik.de/europe/britain-and-ireland-latest.osm.pbf
$ ./extract-area.sh
$ python3 render.py cardiff.osm --output cardiff.png
```
