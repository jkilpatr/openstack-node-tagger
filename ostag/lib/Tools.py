import collections
import subprocess
import json
import openstack

# Run command, return stdout as result
def run_cmd(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode > 0:
        print("The command " + cmd + " returned with errors!")
        print("Printing stderr and continuing")
        print(stderr)

    return stdout.strip()

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
    if 'node' in str(properties['capabilities']) or 'profile' in str(properties['capabilities']):
        return True
    else:
        return False

def clean_tags(uuid, conn):
    node = conn.bare_metal.get_node(uuid)
    if node_already_tagged(uuid, conn):
        pairs = node.properties['capabilities'].split(',')
        capabilities = "'"
        for pair in pairs:
            if not 'node' in pair and not 'profile' in pair:
               capabilities = capabilities + pair + ","
        capabilities = capabilities.rstrip(',')
        capabilities = capabilities + "' "
        cmd = "openstack baremetal node set --property capabilities=" + capabilities + uuid
        run_cmd(cmd)

def tag_node(nodes, num, tag, pin, conn, hint_enabled=False, hint=""):
    try:
        uuid = nodes.pop()
        if hint_enabled:
            tries = 0
            while not node_details_contain(uuid, hint, conn) \
                  and node_already_tagged(uuid, conn):
                nodes.appendleft(uuid)
                uuid = nodes.pop()
                tries = tries + 1
                if tries > len(nodes):
                    print ("No untagged/unpinned nodes found that match hint " + hint)
                    print ("Either none exist or we ran out before tagging all " + num)
                    exit(1)
        else:
            tries = 0
            while node_already_tagged(uuid, conn):
                nodes.appendleft(uuid)
                uuid = nodes.pop()
                tries = tries + 1
                if tries > len(nodes):
                    print ("Not enough untagged/unpinned nodes left ")
                    print ("clear tags and retag as appropriate")
                    exit(1)

        node = conn.bare_metal.get_node(uuid)
        capabilities = node.properties['capabilities']

        if len(tag) > 0:
           value = "node:" + pin + "-" + str(num)
        elif len(pin) > 0:
           value = "profile:" + tag
        if len(capabilities) > 0:
           capabilities = "'" + value + "," + capabilities + "' "
        else:
           capabilities = "'" + value  + "' "
        cmd = "openstack baremetal node set --property capabilities=" + capabilities + uuid
        run_cmd(cmd)

    except ValueError:
        print("You ran out of nodes before all where tagged")
        print("If this wasn't supposed to happen you might want to clear previous tags")
        exit(1)
