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

"""ostag main, issues threads."""
import argparse
from collections import deque
import lib.Tools
import openstack
import os
import sys
import threading


class MyParser(argparse.ArgumentParser):
    """Custom parser class."""

    def error(self, message):
        """Print help on argument parse error."""
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


def parse_args():
    """Parse input args and returns an args dict."""
    parser = MyParser(description='Automated node tagging script for \
                                   large OpenStack deployments')

    parser.add_argument('-n', '--nodes', dest='num_nodes', type=int,
                        help='The number of nodes to tag', required=True)

    parser.add_argument('--hint', dest='hint', default="", type=str,
                        help='Scheduling hint to search for \
                              in ironic node properties')

    parser.add_argument('-t', '--tag', dest='tag', type=str,
                        help='What role to tag the nodes with', default="")

    parser.add_argument('-p', '--pin', dest='pin', type=str,
                        help='What role to pin the nodes to', default="")

    parser.add_argument('-c', '--clear', '--clean', dest='clear',
                        action="store_true",
                        help='Clean existing tags from all nodes')

    args = parser.parse_args()
    return args


def setup_openstack_api():
    """Grab auth info from the environment."""
    if 'OS_AUTH_URL' not in os.environ:
        print("Please source a cloud rc file")
        exit(1)

    auth_args = {
        'auth_url': os.environ['OS_AUTH_URL'],
        'project_name': 'admin',
        'username': os.environ['OS_USERNAME'],
        'password': os.environ['OS_PASSWORD'],
    }

    return openstack.connection.Connection(**auth_args)


def clear_tags(conn=None):
    """Clean existing tags/pins from nodes."""
    if conn is None:
        conn = setup_openstack_api()
        # Issue one thread for each node
        nodes = deque(lib.Tools.get_uuid_list(conn))
        clear_threads = []
        while len(nodes):
            uuid = nodes.pop()
            clear_thread = threading.Thread(target=lib.Tools.clean_tags,
                                            args=(uuid, conn))
            clear_threads.append(clear_thread)
            clear_thread.start()
        for clear_thread in clear_threads:
            clear_thread.join()
        return True


def mark_nodes(tag, pin, conn, hint_enabled, hint, num_nodes):
    """Pin or tags nodes."""
    # Issue a thread for each node being tagged
    tag_threads = []
    nodes = deque(lib.Tools.get_uuid_list(conn))
    for thread_idx in range(num_nodes):
        tag_thread = threading.Thread(target=lib.Tools.tag_node,
                                      args=(nodes, thread_idx,
                                            tag, pin, conn,
                                            hint_enabled, hint))
        tag_threads.append(tag_thread)
        tag_thread.start()

        for thread in tag_threads:
            thread.join()


def main():
    """ostag, OpenStack node marking tool."""
    args = parse_args()
    if len(args.tag) > 0 and len(args.pin) > 0:
        print("You can't use both tagging and pins at the same time")
        exit(1)
    conn = setup_openstack_api()

    hint_enabled = (len(args.hint) > 0)

    if args.clear:
        clear_tags(conn)

    mark_nodes(args.tag,
               args.pin,
               conn,
               hint_enabled,
               args.hint,
               args.num_nodes)
