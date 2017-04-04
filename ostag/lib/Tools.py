# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""ostag utility functions."""
import subprocess


def run_cmd(cmd):
    """Run console command. Return stdout print stderr."""
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode > 0:
        print("The command " + cmd + " returned with errors!")
        print("Printing stderr and continuing")
        print(stderr)

    return stdout.strip()


def get_uuid_list(conn):
    """Grab list of Ironic nodes."""
    return list(map(lambda node: node.id, conn.bare_metal.nodes()))


def node_details_contain(uuid, pattern, conn):
    """Return true if node details contain the pattern."""
    properties = conn.bare_metal.get_node(uuid).properties
    if pattern in str(properties):
        return True
    else:
        return False


def node_already_tagged(uuid, conn):
    """Return true if a node is already tagged."""
    properties = conn.bare_metal.get_node(uuid).properties
    if 'node' in str(properties['capabilities']) \
        or 'profile' in str(properties['capabilities']):
        return True
    else:
        return False


def clean_tags(uuid, conn):
    """Clean the tags on a given uuid."""
    node = conn.bare_metal.get_node(uuid)
    if node_already_tagged(uuid, conn):
        pairs = node.properties['capabilities'].split(',')
        capabilities = "'"
        for pair in pairs:
            if 'node' not in pair and 'profile' not in pair:
                capabilities = capabilities + pair + ","
        capabilities = capabilities.rstrip(',')
        capabilities = capabilities + "' "
        cmd = "openstack baremetal node set --property capabilities=" \
              + capabilities + \
              uuid
        run_cmd(cmd)


def tag_node(nodes, num, tag, pin, conn, hint_enabled=False, hint=""):
    """Tag one node from the deque. Searching until match is found."""
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
                    print ("No untagged/unpinned nodes \
                            found that match hint " + hint)
                    print ("Either none exist or we ran \
                            out before tagging all " + num)
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

        if len(pin) > 0:
            value = "node:" + pin + "-" + str(num)
        elif len(tag) > 0:
            value = "profile:" + tag
        if len(capabilities) > 0:
            capabilities = "'" + value + "," + capabilities + "' "
        else:
            capabilities = "'" + value + "' "
        cmd = "openstack baremetal node set --property capabilities=" \
              + capabilities \
              + uuid
        run_cmd(cmd)

    except ValueError:
        print("You ran out of nodes before all where tagged")
        print("You might want to clear previous tags")
        exit(1)
