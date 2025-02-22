import argparse
from lxml import etree
import drawsvg as drawsvg
import math
import uuid
import json
import db
import couchbeans


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
        
    #print(llb)
    
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

def bounds_to_olcs(bounds, olc_resolution=6):
    latres = 180 / (9 * (20**((olc_resolution/2)-1)))
    lonres = 360 / (18 * (20**((olc_resolution/2)-1)))
    olcs = []
    for lat in frange(bounds[0] - latres, bounds[1] + latres, latres):
        for lon in frange(bounds[2] - lonres, bounds[3] + lonres, lonres):
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

class OSMWay:
    highway_type = "path"
    bridge = False
    maxspeed = "60 mph"
    ref = None
    
    def __init__(self):
        self.points = []
        self.point_refs = []
    
    def add_point(self, point):
        self.points.append(point)
        
    def plot_on_path(self, path_object):
        path_object.M(*(self.points[0].as_xy_coords())) # Start
        for pt in self.points[1:]:
            path_object.L(*(pt.as_xy_coords())) # Point

class AreaRenderer:
    point_map = None
    ways = None
    highways = None
    scale_factors = None

    bound_top = 51.5709
    bound_left = -3.3062
    bound_bottom = 51.4159
    bound_right = -3.0580

    screen_space_x = 256
    screen_space_y = 256
    

    
    couch_base_uri = ""

    def load_couch(self, bounds):
        olcs = bounds_to_olcs(bounds, 8)
        couch = couchbeans.CouchClient(self.couch_base_uri)
        print("Loading " + json.dumps(olcs))
        all_ways = []
        for olc in olcs:
            try:
                in_doc = couch.get_document("grippy_segments", olc)
                all_ways.extend(in_doc["ways"])
            except couchbeans.exceptions.CouchHTTPError as e:
                print("Could not load " + olc)
                pass
        #print(all_ways)
        for way_def in all_ways:
            way = OSMWay()
            for point_def in way_def["path"]:
                way.add_point(OSMPoint(point_def[0], point_def[1],self))
            way.highway_type = way_def["type"]
            self.ways[way_def["id"]] = way
            if way_def["is_highway"]:
                self.highways.append(way_def["id"])

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
        
    
    def render_area(self):
        #self.load_xml("cardiff.osm")
        #print("XML loaded")
        self.load_couch([self.bound_bottom, self.bound_top, self.bound_left, self.bound_right])
        #print(self.highways)
        
        drawing = drawsvg.Drawing(self.screen_space_x, self.screen_space_y, origin='center')
        
        wayct = 0
        
        layers = {}
        layer_order = ["background", "path", "road_outlines", "tertiary_link", "secondary_link", "tertiary", "primary_link", "trunk_link", "secondary", "motorway_link", "primary", "trunk", "motorway", "bridge_base", "bridge_outline", "bridge"]
        path_base_colors = {
                "path": "#dddddd",
                "tertiary": "#ffffff",
                "secondary": "#f3ef14",
                "primary": "#e10f1c",
                "trunk": "#349843",
                "motorway": "#0871b9",
                "tertiary_link": "#ffffff",
                "secondary_link": "#f3ef14",
                "primary_link": "#e10f1c",
                "trunk_link": "#349843",
                "motorway_link": "#0871b9"
            }
        rsf = 1
        path_base_widths = {
                "path": 1 * rsf,
                "tertiary": 2 * rsf,
                "secondary": 3 * rsf,
                "primary": 4 * rsf,
                "trunk": 4 * rsf,
                "motorway": 5 * rsf,
                "tertiary_link": 1 * rsf,
                "secondary_link": 1.5 * rsf,
                "primary_link": 2 * rsf,
                "trunk_link": 2 * rsf,
                "motorway_link": 2.5 * rsf
            }
        for layer_name in layer_order:
            layers[layer_name] = []
        
        pt_types = ["motorway", "motorway_link", "trunk_link", "trunk", "secondary_link", "primary", "secondary_link", "secondary", "tertiary_link", "tertiary", "areas"]
        outline_types = ["tertiary_link", "tertiary"]
        
        for way_id in self.highways:
            way = self.ways[way_id]
            if len(way.points) >= 2:
                #print(way.points[0].as_xy_coords())
                
                path_type = "path"
                if way.highway_type in pt_types:
                    path_type = way.highway_type
                elif way.highway_type == "unclassified":
                    path_type = "tertiary"
                elif way.highway_type == "residential":
                    path_type = "tertiary"
                    
                layer_name = path_type
                
                if way.bridge:
                    layer_name = "bridge"
                #if path_type.endswith("_link"):
                #    layer_name = path_type[:-5]
                
                if way.bridge:
                    path = drawsvg.Path(stroke_width=path_base_widths[path_type] + (2 * rsf), stroke="#000000", fill_opacity=0, stroke_opacity=1)
                    way.plot_on_path(path)
                    layers["bridge_outline"].append(path)
                    path = drawsvg.Path(stroke_width=path_base_widths[path_type] + (4 * rsf), stroke="#ffffff", fill_opacity=0, stroke_opacity=1)
                    way.plot_on_path(path)
                    layers["bridge_base"].append(path)
                    
                path = drawsvg.Path(stroke_width=path_base_widths[path_type], stroke=path_base_colors[path_type], fill_opacity=0, stroke_opacity=1, stroke_linecap="round")
                way.plot_on_path(path)
                layers[layer_name].append(path)
                
                if path_type in outline_types:
                    path = drawsvg.Path(stroke_width=path_base_widths[path_type] + (1 * rsf), stroke="#888888", fill_opacity=0, stroke_opacity=1, stroke_linecap="round")
                    way.plot_on_path(path)
                    layers["road_outlines"].append(path)
                
            wayct += 1
        
        path = drawsvg.Path(fill="#ffffff", fill_opacity=1, stroke_opacity=0)
        path.M(*(OSMPoint(self.bound_top, self.bound_left, self).as_xy_coords()))
        path.L(*(OSMPoint(self.bound_top, self.bound_right, self).as_xy_coords()))
        path.L(*(OSMPoint(self.bound_bottom, self.bound_right, self).as_xy_coords()))
        path.L(*(OSMPoint(self.bound_bottom, self.bound_left, self).as_xy_coords()))
        path.Z()
        layers["background"].append(path)
            
        for layer_name in layer_order:
            for draw_object in layers[layer_name]:
                drawing.append(draw_object)

        tile_id = str(uuid.uuid4())

        drawing.save_svg("cache/temp/" + tile_id + ".svg")
        drawing.save_png("cache/temp/" + tile_id + ".png")
        
        return tile_id
        
    def __init__(self, couch_base_uri):
        self.couch_base_uri = couch_base_uri
        self.point_map = {}
        self.ways = {}
        self.highways = []
        self.scale_factors = {}
