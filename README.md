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

## Utility container
```
$ docker compose run --rm dbtools
```

## Generate a map tile
```bash
$ wget https://download.geofabrik.de/europe/britain-and-ireland-latest.osm.pbf
$ osmosis --read-pbf united_kingdom.osm.pbf --bounding-box top=51.5709 left=-3.3062 bottom=51.4159 right=-3.0580 --write-xml cardiff.osm
$ python3 render.py cardiff.osm --output cardiff.png
```

## Get coastlines
https://osmdata.openstreetmap.de/download/land-polygons-split-3857.zip
https://osmdata.openstreetmap.de/download/simplified-land-polygons-complete-3857.zip

## Notes

Create public network first!
docker network create -d bridge public

wget https://download.geofabrik.de/asia/azerbaijan-latest.osm.pbf
psql "host=$POSTGRES_HOST password=$POSTGRES_PASSWORD user=$POSTGRES_USER dbname=$POSTGRES_DB" -c "create extension hstore;"
osm2pgsql -d "host=$POSTGRES_HOST password=$POSTGRES_PASSWORD user=$POSTGRES_USER dbname=$POSTGRES_DB" --create --slim  -G --hstore -C 2500 --number-processes 8 azerbaijan-latest.osm.pbf
