import argparse
from lxml import etree
import drawsvg as drawsvg
import math
import uuid
import json
import db

"""
                  List of relations
  Schema  |           Name           | Type  | Owner  
----------+--------------------------+-------+--------
 public   | planet_osm_line          | table | grippy
 public   | planet_osm_nodes         | table | grippy
 public   | planet_osm_point         | table | grippy
 public   | planet_osm_polygon       | table | grippy
 public   | planet_osm_rels          | table | grippy
 public   | planet_osm_roads         | table | grippy
 public   | planet_osm_ways          | table | grippy
 public   | spatial_ref_sys          | table | grippy
 tiger    | addr                     | table | grippy
 tiger    | addrfeat                 | table | grippy
 tiger    | bg                       | table | grippy
 tiger    | county                   | table | grippy
 tiger    | county_lookup            | table | grippy
 tiger    | countysub_lookup         | table | grippy
 tiger    | cousub                   | table | grippy
 tiger    | direction_lookup         | table | grippy
 tiger    | edges                    | table | grippy
 tiger    | faces                    | table | grippy
 tiger    | featnames                | table | grippy
 tiger    | geocode_settings         | table | grippy
 tiger    | geocode_settings_default | table | grippy
 tiger    | loader_lookuptables      | table | grippy
 tiger    | loader_platform          | table | grippy
 tiger    | loader_variables         | table | grippy
 tiger    | pagc_gaz                 | table | grippy
 tiger    | pagc_lex                 | table | grippy
 tiger    | pagc_rules               | table | grippy
 tiger    | place                    | table | grippy
 tiger    | place_lookup             | table | grippy
 tiger    | secondary_unit_lookup    | table | grippy
 tiger    | state                    | table | grippy
 tiger    | state_lookup             | table | grippy
 tiger    | street_type_lookup       | table | grippy
 tiger    | tabblock                 | table | grippy
 tiger    | tabblock20               | table | grippy
 tiger    | tract                    | table | grippy
 tiger    | zcta5                    | table | grippy
 tiger    | zip_lookup               | table | grippy
 tiger    | zip_lookup_all           | table | grippy
 tiger    | zip_lookup_base          | table | grippy
 tiger    | zip_state                | table | grippy
 tiger    | zip_state_loc            | table | grippy
 topology | layer                    | table | grippy
 topology | topology                 | table | grippy
(44 rows)
 
"""

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
    point_map = {}
    ways = {}
    highways = []

    bound_top = 51.5709
    bound_left = -3.3062
    bound_bottom = 51.4159
    bound_right = -3.0580

    screen_space_x = 256
    screen_space_y = 256
    
    scale_factors = {}

    def load_xml(self, filename):
        print("XML load start")
        with open(filename, "rb") as f:
            for event, element in etree.iterparse(f):
                #print(f"{event}, {element.tag:>4}, {element.text}")
                element_id = element.get("id")
                if element.tag == "node":
                    self.point_map[element_id] = OSMPoint(element.get("lat"), element.get("lon"), self)
                if element.tag == "way":
                    self.ways[element_id] = OSMWay()
                    for prop in element.getchildren():
                        if prop.tag == "nd":
                            self.ways[element_id].point_refs.append(prop.get("ref"))
                        if prop.tag == "tag":
                            if prop.get("k") == "highway":
                                self.ways[element_id].highway_type = prop.get("v")
                                self.highways.append(element_id)
                            if prop.get("k") == "bridge":
                                self.ways[element_id].bridge = True
                            if prop.get("k") == "ref":
                                self.ways[element_id].ref = prop.get("ref")
                            if prop.get("k") == "maxspeed":
                                self.ways[element_id].maxspeed = prop.get("maxspeed")
        
        for way_id in self.ways:
            for ptref in self.ways[way_id].point_refs:
                if ptref in self.point_map:
                    self.ways[way_id].add_point(self.point_map[ptref])
        print("XML loaded")
        return True
                    
    def load_pg(self, bt, bl, bb, br):
        print("Postgres load start")
        conn = db.get_postgres()
        cur = conn.cursor()
        query = "SELECT * FROM planet_osm_nodes WHERE lat>=" + str(int(bb * 10000000)) + " AND lat<=" + str(int(bt * 10000000)) + " AND lon>=" + str(int(bl * 10000000)) + " AND lon<=" + str(int(br * 10000000))
        #print(query)
        cur.execute(query)
        
        nodes = cur.fetchall()
        inner_query = "SELECT * FROM planet_osm_ways WHERE nodes && ARRAY["
        for node in nodes:
            inner_query += str(node[0]) + "," # get node id
        
        inner_query = inner_query[:-1] + "]"
        print(inner_query)
        
        cur.execute(inner_query)
        ways = cur.fetchall()
        for way in ways:
            print(way)
        
        #cols = cur.description
        #for row in rows:
            #dictrow = {}
            #for idx in range(0, len(cols)):
            #    print(cols[idx].name)
            #    dictrow[cols[idx].name] = row[idx]
            #print(json.dumps(dictrow, indent=4))
            #break;
            #if not dictrow["highway"] is None:
            #    print(json.dumps(dictrow, indent=4))
            #break;
        
        conn.commit()
        print("Postgres loaded")
        return True

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
        self.load_pg(self.bound_top, self.bound_left, self.bound_bottom, self.bound_right)
        
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
        
    def __init__(self):
        pass
