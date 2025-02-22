import os
import json
import math
import couchbeans
from lxml import etree

config_file_loc = os.environ.get("GRIPPY_CONFIG_FILE", "config.json")
sys_config = {}
with open(config_file_loc, "r") as f:
    sys_config = json.load(f)

def try_get_config_prop(property_name, alternate=None):
    if property_name in sys_config:
        return sys_config[property_name]
    return alternate

couch_user = os.environ.get("COUCHDB_USER", try_get_config_prop("couchdb_user"))
couch_password = os.environ.get("COUCHDB_PASSWORD", try_get_config_prop("couchdb_password"))
couch_host = os.environ.get("COUCHDB_HOST", try_get_config_prop("couchdb_host", "localhost"))
couch_port = os.environ.get("COUCHDB_PORT", try_get_config_prop("couchdb_port", 5984))
couch_base_uri = "http://" + couch_user + ":" + couch_password + "@" + couch_host + ":" + str(couch_port) + "/"


print(couch_base_uri)

olc_alpha = "23456789CFGHJMPQRVWX"
olc_inv_alpha = {}
for idx, alph in enumerate(olc_alpha):
    olc_inv_alpha[alph] = idx
    
def olc_to_bounds(olc):
    llb = 0
    lbb = 0
    ebsx = 18 * 20**int(((len(olc) - 2) / 2))
    ebsy = 9 * 20**int(((len(olc) - 2) / 2))
    for level, group in enumerate([olc[i:i+2] for i in range(0, len(olc), 2)]):
        bsx = 18 * 20**int(level)
        bsy = 9 * 20**int(level)
        lbb += olc_inv_alpha[group[0]] / bsy
        llb += olc_inv_alpha[group[1]] / bsx
        
    print(llb)
    
    latb = ((lbb) * 180) - 90
    latt = ((lbb + (1/ebsy)) * 180) - 90
    lonl = ((llb) * 360) - 180
    lonr = ((llb + (1/ebsx)) * 360) - 180
    return (latb, latt, lonl, lonr)

def pos_to_olc(lat, lon, acc=4):
    olc = ["2"] * acc
    lat = (lat + 90) / 180
    lon = (lon + 180) / 360
    lat = lat * 9
    lon = lon * 18
    olc[0] = olc_alpha[math.floor(lat)]
    olc[1] = olc_alpha[math.floor(lon)]
    stp = 2
    while stp < acc:
        lat = (lat % 1) * 20
        lon = (lon % 1) * 20
        olc[stp + 0] = olc_alpha[math.floor(lat)]
        olc[stp + 1] = olc_alpha[math.floor(lon)]
        stp += 2
    return "".join(olc)

def frange(x, y, jump):
    while x < y:
        yield x
        x += jump

def bounds_to_olcs(bounds, olc_resolution=4):
    latres = 180 / (9 * (20**((olc_resolution/2)-1)))
    lonres = 360 / (18 * (20**((olc_resolution/2)-1)))
    olcs = []
    for lat in frange(bounds[0], bounds[1], latres):
        for lon in frange(bounds[2], bounds[3], lonres):
            olcs.append(pos_to_olc(lat, lon, olc_resolution))
    return olcs

class OSMPoint:
    lat = 0
    lon = 0
    area_renderer = None
    
    def __init__(self, lat, lon, area_renderer):
        self.area_renderer = area_renderer
        self.lat = float(lat)
        self.lon = float(lon)
        
    def as_xy_coords(self):
        return self.area_renderer.transform_coords(self.lat, self.lon)
    
    def as_lat_long(self):
        return [self.lat, self.lon]

class OSMWay:
    is_highway = False
    way_type = "path"
    bridge = False
    maxspeed = None
    ref = None
    bounds = None
    olc_codes_list = None
    segments_in_olc_codes = None
    osm_id = None
    
    def __init__(self, osm_id = None):
        self.osm_id = osm_id
        self.points = []
        self.bounds = [90, -90, 180, -180]
        self.segments_in_olc_codes = {}
        self.olc_codes_list = []
        self.point_refs = []
    
    def add_point(self, point):
        self.points.append(point)
        
    def plot_on_path(self, path_object):
        path_object.M(*(self.points[0].as_xy_coords())) # Start
        for pt in self.points[1:]:
            path_object.L(*(pt.as_xy_coords())) # Point
            
    def calc_path_properties(self, olc_resolution=4):
        points = []
        for point in self.points:
            pll = point.as_lat_long()
            points.append(pll)
            if self.bounds[0] > pll[0]:
                self.bounds[0] = pll[0]
            if self.bounds[1] < pll[0]:
                self.bounds[1] = pll[0]
            if self.bounds[2] > pll[1]:
                self.bounds[2] = pll[1]
            if self.bounds[3] < pll[1]:
                self.bounds[3] = pll[1]
                
        for olc in bounds_to_olcs(self.bounds, olc_resolution):
            self.olc_codes_list.append(olc)
        self.olc_codes_list = list(set(self.olc_codes_list))
        self.geo_points = points
        pass
            
    def to_dict(self):
        return {
                "type": self.way_type,
                "id": self.osm_id,
                "is_highway": self.is_highway,
                "max_speed": self.maxspeed,
                "path": self.geo_points,
                "bounds": self.bounds,
                "from": self.geo_points[0],
                "olc_membership": self.olc_codes_list,
                "to": self.geo_points[len(self.geo_points)-1]
            }

class MapImporter:

    point_map = {}
    ways = {}
    olc_map = {}

    bound_top = 51.5709
    bound_left = -3.3062
    bound_bottom = 51.4159
    bound_right = -3.0580

    screen_space_x = 256
    screen_space_y = 256
    
    scale_factors = {}
    


    def load_xml(self, filename, chunk_resolution=4):
        print("XML load start")
        with open(filename, "rb") as f:
            for event, element in etree.iterparse(f):
                #print(f"{event}, {element.tag:>4}, {element.text}")
                element_id = element.get("id")
                if element.tag == "node":
                    self.point_map[element_id] = OSMPoint(element.get("lat"), element.get("lon"), self)
                if element.tag == "way":
                    self.ways[element_id] = OSMWay(element_id)
                    for prop in element.getchildren():
                        if prop.tag == "nd":
                            self.ways[element_id].point_refs.append(prop.get("ref"))
                        if prop.tag == "tag":
                            if prop.get("k") == "highway":
                                self.ways[element_id].way_type = prop.get("v")
                                self.ways[element_id].is_highway = True
                            if prop.get("k") == "bridge":
                                self.ways[element_id].bridge = True
                            if prop.get("k") == "ref":
                                self.ways[element_id].ref = prop.get("ref")
                            if prop.get("k") == "maxspeed":
                                maxspeed_raw = prop.get("maxspeed")
                                maxspeed_ms = None
                                if not maxspeed_raw is None:
                                    if maxspeed_raw.endswith("mph"):
                                        maxspeed_ms = int(maxspeed_raw[:-3]) / 2.2369362920544
                                    elif maxspeed_raw.endswith("kph"):
                                        maxspeed_ms = int(maxspeed_raw[:-3]) / 3.59999999712
                                    elif maxspeed_raw.endswith("kmph"):
                                        maxspeed_ms = int(maxspeed_raw[:-4]) / 3.59999999712
                                    elif maxspeed_raw:
                                        maxspeed_ms = int(maxspeed_raw) / 3.59999999712
                                    else:
                                        maxspeed_ms = None
                                self.ways[element_id].maxspeed = maxspeed_ms
        print("Calculating params")
        waypc = 0
        waytot = len(self.ways)
        for way_id in self.ways:
            for ptref in self.ways[way_id].point_refs:
                if ptref in self.point_map:
                    self.ways[way_id].add_point(self.point_map[ptref])
            self.ways[way_id].calc_path_properties(chunk_resolution * 2)
            for olc_code in self.ways[way_id].olc_codes_list:
                if not olc_code in self.olc_map:
                    self.olc_map[olc_code] = {"ways": []}
                self.olc_map[olc_code]["ways"].append(self.ways[way_id])
            waypc += 1
            if waypc % 64 == 0:
                print(str(waypc) + " of " + str(waytot) + " processed")
                #print(json.dumps(self.ways[way_id].to_dict(), indent=2))
        print("XML loaded")
        return True
    
    def export_to_couchdb(self, couch_base_uri):
        couch = couchbeans.CouchClient(couch_base_uri)
        try:
            couch.delete_db("grippy_segments")
        except Exception:
            pass
        couch.create_db("grippy_segments")
        olcpc = 0
        olctot = len(self.olc_map)
        for olc_code in self.olc_map:
            oways = self.olc_map[olc_code]["ways"]
            sector_ways = []
            for way in oways:
                sector_ways.append(way.to_dict())
            doc = {
                    "ways": sector_ways
                }
            #print("Exported zone " + olc_code)
            
            olcpc += 1
            if olcpc % 64 == 0:
                print(str(olcpc) + " of " + str(olctot) + " zones uploaded")
            couch.put_document("grippy_segments", olc_code, doc)
            #print(olc_code)

    def calc_scale_factors(self, bt, bl, bb, br):
        lat_delta = bb - bt
        long_delta = br - bl
        lat_delta_scale = 1 / lat_delta
        long_delta_scale = 1 / long_delta
        lat_range_offset = -((bt + bb) / 2)
        long_range_offset = -((bl + br) / 2)
        return {
                "xt_mult": long_delta_scale * self.screen_space_x,
                "xt_offset": long_range_offset,
                "xb_mult": long_delta_scale * self.screen_space_x,
                "xb_offset": long_range_offset,
                "yl_mult": lat_delta_scale * self.screen_space_y,
                "yl_offset": lat_range_offset,
                "yr_mult": lat_delta_scale * self.screen_space_y,
                "yr_offset": lat_range_offset
            }

    def transform_coords(self, lat, lon):
        x = (lon + self.scale_factors["xt_offset"]) * self.scale_factors["xt_mult"]
        y = (lat + self.scale_factors["yl_offset"]) * self.scale_factors["yl_mult"]
        return (x, y)


    def set_slippy_area(self, x, y, zoom):
        subdiv = pow(2, int(zoom))
        x_l = int(x) / float(subdiv)
        y_l = int(y) / float(subdiv)
        x_h = (int(x) + 1) / float(subdiv)
        y_h = (int(y) + 1) / float(subdiv)
        
        lon_deg_l = (x_l * 360.0) - 180.0
        lat_rad_l = math.atan(math.sinh(math.pi * (1 - (2 * y_l))))
        lat_deg_l = (lat_rad_l * 180.0) / math.pi

        lon_deg_h = (x_h * 360.0) - 180.0
        lat_rad_h = math.atan(math.sinh(math.pi * (1 - (2 * y_h))))
        lat_deg_h = (lat_rad_h * 180.0) / math.pi
        
        self.bound_top = lat_deg_l
        self.bound_left = lon_deg_l
        self.bound_bottom = lat_deg_h
        self.bound_right = lon_deg_h
        
        self.scale_factors = self.calc_scale_factors(self.bound_top, self.bound_left, self.bound_bottom, self.bound_right)
        
if __name__ == "__main__":
    mi = MapImporter()
    mi.load_xml("cardiff.osm")
    mi.export_to_couchdb(couch_base_uri)
    #print(mi.olc_to_bounds("9C"))
    #print(mi.olc_to_bounds("9C3R"))
    #print(mi.olc_to_bounds("9C3RFR"))
    #bounds = mi.olc_to_bounds("9C3RFRJC")
    #print(bounds)
    #print(mi.pos_to_olc((bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2, 8))
    
    
