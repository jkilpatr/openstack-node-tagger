import argparse
import lib.Tools
import threading
import sys
import openstack
import os
import json
from collections import deque

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

parser = MyParser(description='Automated node tagging script for \
                               large OpenStack deployments')

parser.add_argument('-n', '--nodes', dest='num_nodes', type=int,
                    help='The number of nodes to tag', required=True)

parser.add_argument('--hint', dest='hint', default="", type=str,
                    help='Scheduling hint to search for in ironic node-show')

parser.add_argument('-t', '--tag', dest='tag', type=str,
                    help='What role to tag the nodes with', required=True)

parser.add_argument('-c', '--clear', '--clean', dest='clear', action="store_true",
                    help='Clean existing tags from all nodes')

args = parser.parse_args()

if 'OS_AUTH_URL' not in os.environ:
    print("Please source a cloud rc file")
    exit(1)


auth_args = {
    'auth_url': os.environ['OS_AUTH_URL'],
    'project_name': 'admin',
    'username': os.environ['OS_USERNAME'],
    'password': os.environ['OS_PASSWORD'],
}


conn = openstack.connection.Connection(**auth_args)

hint_enabled = (len(args.hint) > 0)

# Issue one thread for each node
if args.clear == True:
    nodes = deque(lib.Tools.get_uuid_list(conn))
    clear_threads = []
    while len(nodes):
        uuid = nodes.pop()
        clear_thread = threading.Thread(target=lib.Tools.clean_tags, args=(uuid, conn))
        clear_threads.append(clear_thread)
        clear_thread.start()
    for clear_thread in clear_threads:
        clear_thread.join()

# Issue a thread for each node being tagged
tag_threads = []
nodes = deque(lib.Tools.get_uuid_list(conn))
for thread_idx in range(args.num_nodes):
    tag_thread = threading.Thread(target=lib.Tools.tag_node,
                                  args=(nodes, thread_idx,
                                       args.tag, conn,
                                       hint_enabled, args.hint))
    tag_threads.append(tag_thread)
    tag_thread.start()

for thread in tag_threads:
    thread.join()



