#!/bin/python3

import argparse
from lxml import etree
import drawsvg as drawsvg

class OSMPoint:
    lat = 0
    lon = 0
    
    def __init__(self, lat, lon):
        self.lat = float(lat)
        self.lon = float(lon)
        
    def as_xy_coords(self):
        return transform_coords(self.lat, self.lon)

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
        path.M(*(self.points[0].as_xy_coords())) # Start
        for pt in self.points[1:]:
            path.L(*(pt.as_xy_coords())) # Point

point_map = {}
ways = {}
highways = []

def load_xml(filename):
    with open(filename, "rb") as f:
        for event, element in etree.iterparse(f):
            #print(f"{event}, {element.tag:>4}, {element.text}")
            element_id = element.get("id")
            if element.tag == "node":
                point_map[element_id] = OSMPoint(element.get("lat"), element.get("lon"))
            if element.tag == "way":
                ways[element_id] = OSMWay()
                for prop in element.getchildren():
                    if prop.tag == "nd":
                        ways[element_id].point_refs.append(prop.get("ref"))
                    if prop.tag == "tag":
                        if prop.get("k") == "highway":
                            ways[element_id].highway_type = prop.get("v")
                            highways.append(element_id)
                        if prop.get("k") == "bridge":
                            ways[element_id].bridge = True
                        if prop.get("k") == "ref":
                            ways[element_id].ref = prop.get("ref")
                        if prop.get("k") == "maxspeed":
                            ways[element_id].maxspeed = prop.get("maxspeed")
    
    for way_id in ways:
        for ptref in ways[way_id].point_refs:
            if ptref in point_map:
                ways[way_id].add_point(point_map[ptref])

bound_top = 51.5709
bound_left = -3.3062
bound_bottom = 51.4159
bound_right = -3.0580

screen_space_x = 1024 * 4
screen_space_y = 1024 * 4

def calc_scale_factors(bt, bl, bb, br):
    lat_delta = bb - bt
    long_delta = br - bl
    lat_delta_scale = 1 / lat_delta
    long_delta_scale = 1 / long_delta
    lat_range_offset = -((bt + bb) / 2)
    long_range_offset = -((bl + br) / 2)
    return {
            "xt_mult": long_delta_scale * screen_space_x,
            "xt_offset": long_range_offset,
            "xb_mult": long_delta_scale * screen_space_x,
            "xb_offset": long_range_offset,
            "yl_mult": lat_delta_scale * screen_space_y,
            "yl_offset": lat_range_offset,
            "yr_mult": lat_delta_scale * screen_space_y,
            "yr_offset": lat_range_offset
        }

scale_factor = calc_scale_factors(bound_top, bound_left, bound_bottom, bound_right)

def transform_coords(lat, lon):
    x = (lon + scale_factor["xt_offset"]) * scale_factor["xt_mult"]
    y = (lat + scale_factor["yl_offset"]) * scale_factor["yl_mult"]
    return (x, y)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                    prog="osmrender",
                    description="Renders OSM maps")
    
    parser.add_argument("--output", type=str, default="output.svg", help="Output svg file")
    parser.add_argument("infiles", nargs="*", default=[], help="OSM XML files to pull data from")
    args = parser.parse_args()
    
    load_xml(args.infiles[0])
    print("XML loaded")
    
    drawing = drawsvg.Drawing(screen_space_x, screen_space_y, origin='center')
    
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
    
    for way_id in highways:
        way = ways[way_id]
        if len(way.points) >= 2:
            #print(way.points[0].as_xy_coords())
            
            path_type = "path"
            if way.highway_type in pt_types:
                path_type = way.highway_type
            elif way.highway_type == "unclassified":
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
    path.M(*(OSMPoint(bound_top, bound_left).as_xy_coords()))
    path.L(*(OSMPoint(bound_top, bound_right).as_xy_coords()))
    path.L(*(OSMPoint(bound_bottom, bound_right).as_xy_coords()))
    path.L(*(OSMPoint(bound_bottom, bound_left).as_xy_coords()))
    path.Z()
    layers["background"].append(path)
        
    for layer_name in layer_order:
        for draw_object in layers[layer_name]:
            drawing.append(draw_object)

    drawing.save_svg("example.svg")
    drawing.save_png("example.png")
