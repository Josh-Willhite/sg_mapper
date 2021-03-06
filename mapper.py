#!/user/bin/python env
import json
import random
import sys

import boto3
from graphviz import Digraph


def get_security_groups(region_name, vpc_id):
    ec2 = boto3.resource('ec2', region_name=region_name)
    return [g for g in ec2.security_groups.all() if g.vpc_id == vpc_id]


class SGraph(object):
    def __init__(self, security_groups, outfile):
        self.dot = Digraph()
        self.dot.format = 'svg'
        self.sgs = security_groups
        self.colors = self.load_colors()
        self.colors_assigned = []
        self.create_nodes()
        self.create_edges()
        self.dot.render('img/{}.svg'.format(outfile))

    def load_colors(self, colors_file='colors.json'):
        with open(colors_file) as f:
            return json.load(f)

    def select_color(self):
            available_colors = list(
                                set(self.colors) - set(self.colors_assigned)
                               )
            if len(available_colors) > 0:
                color = random.choice(available_colors)
                self.colors_assigned.append(color)
                return color
            else:
                print('out of colors')
                return 'black'

    def create_nodes(self):
        for group in self.sgs:
            self.dot.node(group.group_name)

    def get_ingress(self, group):
        ingress = {}
        for dst_g in self.sgs:
            for perm in dst_g.ip_permissions:
                for src_g in perm['UserIdGroupPairs']:
                    if src_g['GroupId'] == group.group_id and 'ToPort' in perm:
                        ingress[dst_g.group_name] = perm['ToPort']
        return ingress

    def create_edges(self):
        port_to_color = {}
        for src_g in self.sgs:
            ingress = self.get_ingress(src_g)
            for dst_g, port in ingress.items():
                if port not in port_to_color:
                    port_to_color[port] = self.select_color()
                self.dot.edge(
                    src_g.group_name, dst_g, label=str(port),
                    color=port_to_color[port]
                )

region_name = sys.argv[1]
vpc_id = sys.argv[2]
outfile = sys.argv[3]
groups = get_security_groups(region_name, vpc_id)
SGraph(groups, outfile)
