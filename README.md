# map-experiments
Experiments with OpenStreetMap

## Generate a map tile
```
$ wget https://download.geofabrik.de/europe/britain-and-ireland-latest.osm.pbf
$ ./extract-area.sh
$ python3 render.py newport.osm
```
