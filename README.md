# ostag
A tool for tagging/pinning nodes in OpenStack deployments

Warning: This tool is in Beta, know bugs include an infreqent race condition that causes
a gap in pin numbers. This happens rarely so if your deploy fails due to 'not enough nodes'
check that the pinning is seqential and run again if it isn't.

Usage:

run the following command in a virtualenv or at the system level if your brave

	pip install git+https://github.com/jkilpatr/ostag

Then run the following to tag nodes

 	ostag -n <number of nodes to tag> -t <role name>

Or the following to pin nodes

	ostag -n <number of nodes to tag> -p <role name>

Node tagging ensures that only a specific node type will land on the tagged baremetal node
pinning goes a step further and ensures that only a specific instance can occupy a pinned node.
For example you may pin a baremetal node to `node:controller-2` which would ensure only the second
controller instance could ever run on it. Whereas a tag `profile:control` would mean only controller
instances could run on that baremetal node, but with no details as to which instance. Tagging will
make sure your instances land in the right place, pinning will do the same and accelerate your deployment
time if you have enough nodes for scheduling contention to be an issue.

You can also pass `--hint <search string>` which will search the node properties for a string
for example if you wanted to schedule controllers on machine with 24 cpus you could run.

	ostag -n 3 -t controller --hint "'cpus': u'24'"

This script will detect if you already have tags on nodes and not disrupt them, if you need to clear
tags on existing nodes to perform retagging pass the -c option, be warned this deletes tags on all nodes
rather than only the ones it ends up scheduling on. A workflow for changing the tags on a cloud might look
like this.

	ostag -n 3 -t controller -c
	ostag -n 50 -t compute

Where the first run clears existing tags and pins on all 53 nodes, then tags three control instances, and
the second command will tag the remaining 50 nodes as compute instances.

After that, if you are just tagging you are done and can ignore this section, if you are using node pinning you need
to deploy your overcloud with a scheduler hints file to determine your mapping from pins to roles.

	openstack overcloud deploy --templates -e scheduler-hints.yaml

See the example contents of a scheduler-hints.yaml file below, if you don't have any custom roles you can just copy
that into a file. In the future I might have ostag create this file for you dynamically based on the mappings you
pass, but since most deployments take more than one run I haven't done that yet.

	parameter_defaults:
	  ControllerSchedulerHints:
	    'capabilities:node': 'controller-%index%'
	  NovaComputeSchedulerHints:
	    'capabilities:node': 'compute-%index%'
	  BlockStorageSchedulerHints:
	    'capabilities:node': 'blockstorage-%index%'
	  ObjectStorageSchedulerHints:
	    'capabilities:node': 'objectstorage-%index%'
	  CephStorageSchedulerHints:
	    'capabilities:node': 'cephstorage-%index%'

If you need processing of more complex rules I suggest using [profile matching](https://docs.openstack.org/developer/tripleo-docs/advanced_deployment/profile_matching.html) but since profile matching uses tagging and not pinning
you may experience scheduling problems on large deployments.
