import collections
import subprocess
import json
import openstack

# Get list of Ironic nodes
def get_uuid_list(conn):
    return list(map(lambda node: node.id, conn.bare_metal.nodes()))

def node_details_contain(uuid, pattern, conn):
    properties = conn.bare_metal.get_node(uuid).properties
    if pattern in str(properties):
       return True
    else:
       return False

def node_already_tagged(uuid, conn):
    properties = conn.bare_metal.get_node(uuid).properties
    if 'node' in properties:
        return True
    else:
        return False

def clean_tags(uuid, conn):
    node = conn.bare_metal.get_node(uuid)
    if 'node' in node.properties:
        node.properties['node'].delete()
        conn.bare_metal.update_node(uuid, **node)

def tag_node(nodes, num, tag, conn, hint_enabled=False, hint=""):
    try:
        uuid = nodes.pop()
        if hint_enabled:
            tries = 0
            while not node_details_contain(uuid, hint, conn) \
                  and node_already_tagged(uuid, conn):
                nodes.append(uuid)
                uuid = nodes.pop()
                tries = tries + 1
                if tries > len(nodes):
                    print ("No untagged nodes found that match hint " + hint)
                    print ("Either none exist or we ran out before tagging all " + num)
                    exit(1)
        else:
            tries = 0
            while node_already_tagged(uuid, conn):
                nodes.append(uuid)
                uuid = nodes.pop()
                tries = tries + 1
                if tries > len(nodes):
                    print ("Not enough untagged nodes left ")
                    print ("clear tags and retag as appropriate")
                    exit(1)

        node = conn.bare_metal.get_node(uuid)
        node.properties['node'] = tag + "-" + str(num)
        test_dict = {"name": "test"}
        conn.bare_metal.update_node(uuid, **test_dict)
    except ValueError:
        print("You ran out of nodes before all where tagged")
        print("If this wasn't supposed to happen you might want to clear previous tags")
        exit(1)
