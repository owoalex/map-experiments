# map-experiments
Experiments with OpenStreetMap

## Prerequisites

You will need a python venv with "drawsvg" and "lxml" installed.

## Generate a map tile
```
$ wget https://download.geofabrik.de/europe/britain-and-ireland-latest.osm.pbf
$ ./extract-area.sh
$ python3 render.py cardiff.osm --output cardiff.png
```
