# ostag
A tool for tagging/pinning nodes in Openstack deployments

Usage:

run the following command in a virtualenv or at the system level if your brave

	pip install git+https://github.com/jkilpatr/openstack-node-tagger

Then run

 	ostag -n <number of nodes to tag> -t <role name>

You can also pass --hint <search string> which will search the node properties for a string
for example if you wanted to schedule controllers on machine with 24 cpus you could run.

	ostag -n 3 -t controller --hint "'cpus': u'24'"

This script will detect if you already have tags on nodes and not disrupt them, if you need to clear
tags on existing nodes to perform retagging pass the -c option, be warned this deletes tags on all nodes
rather than only the ones it ends up scheduling on. A workflow for changing the tags on a cloud might look
like this.

	ostag -n 3 -t controller -c
	ostag -n 50 -t compute

Where the first run clears existing tags on all 53 nodes, then pins three control instances, and the second command
will pin the remaining 50 nodes as compute instances.

After that you can deploy your overcloud with the scheduler hints file to determine your mapping from tags to roles.

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

If you need processing of more complex rules I suggest using [profile matching](https://docs.openstack.org/developer/tripleo-docs/advanced_deployment/profile_matching.html) but since profile matching doesnt automatically pin
instances to nodes like this script does you may experience scheduling problems on large deployments.
