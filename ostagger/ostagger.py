import argparse
import lib.Tools
import threading
import sys
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

parser.add_argument('-c', '--clear', dest='clear', default="False", type=bool,
                    help='Clean existing tags from all nodes')

parser.add_argument('-s', '--stackrc', dest='stackrc', default="$HOME/stackrc",
                    type=str, help='Path to stackrc file')

args = parser.parse_args()

env_setup = "source " + args.stackrc + ";"
nodes = deque(lib.Tools.get_uuid_list(env_setup))
total_nodes = len(nodes)
hint_enabled = (len(args.hint) > 0)

# Issue one thread for each node
if args.clear == True:
    clear_threads = []
    for uuid in nodes:
        clear_thread = threading.Thread(target=lib.Tools.clean_tags, args=(uuid, env_setup))
        clear_threads.append(clear_thread)
        clear_thread.start()
    for clear_thread in clear_threads:
        clear_thread.join()

# Issue a thread for each node being tagged
tag_threads = []
for thread_idx in range(args.num_nodes):
    tag_thread = threading.Thread(target=lib.Tools.tag_node,
                                  args=(nodes, args.num_nodes,
                                       args.tag, env_setup,
                                       hint_enabled, args.hint))
    tag_threads.append(tag_thread)
    tag_thread.start()

for thread in tag_threads:
    thread.join()



