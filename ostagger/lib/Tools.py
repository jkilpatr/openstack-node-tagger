import collections
import subprocess
import json

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
def get_uuid_list(env_setup):
    cmd = "ironic --json node-list|jq -r '.[]| .[\"uuid\"]'"
    cmd = env_setup + cmd
    results = run_cmd(cmd)
    uuid_list = []
    for line in results.rstrip().split('\n'):
        uuids = line.split(' ')
        uuid_list = uuid_list + [uuids[0]]
    return uuid_list

def node_details_contain(node, pattern, env_setup):
    cmd = env_setup + "openstack baremetal node show " + uuid
    if pattern in run_cmd(cmd):
       return True
    else:
       return False

def node_already_tagged(uuid, env_setup):
    cmd = env_setup + "ironic --json node-show " + uuid
    cmd = cmd + "|jq -r '.[]| .[\"properties\"]'"
    if "node:" in run_cmd(cmd):
        return True
    else:
        return False

def clean_tags(uuid, env_setup):
    cmd = env_setup + "ironic --json node-show " + uuid
    cmd = cmd + "|jq -r '.[]| .[\"properties\"]'"
    properties = json.loads(run_cmd(cmd))
    if 'node' in properties:
        properties['node'].delete()
        cmd = env_setup + "ironic node-update " + json.dumps(properties)

def tag_node(nodes, num, tag, env_setup, hint_enabled=False, hint=""):
    try:
        uuid = nodes.pop()
        if hint_enabled:
            tries = 0
            while not node_details_contain(uuid, args.hint, env_setup) \
                  and not node_already_tagged(uuid, env_setup):
                nodes.push(uuid)
                uuid = nodes.pop()
                tries = tries + 1
                if tries > len(nodes):
                    print ("No untagged nodes found that match hint " + hint)
                    print ("Either none exist or we ran out before tagging all " + num)
                    exit(1)
        else:
            tries = 0
            while not node_already_tagged(uuid, env_setup):
                nodes.push(uuid)
                uuid = nodes.pop()
                tries = tries + 1
                if tries > len(nodes):
                    print ("Not enough untagged nodes left ")
                    print ("clear tags and retag as appropriate " + num)
                    exit(1)
        cmd = env_setup + "openstack baremetal node set --property capabilities='node:" + tag + "-" + num + "' " + uuid
    except ValueError:
        print("You ran out of nodes before all " + num + " where tagged")
        print("If this wasn't supposed to happen you might want to clear previous tags")
        exit(1)
