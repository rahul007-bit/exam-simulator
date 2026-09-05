# Solution for SC-C01: Chaos: Resolve Nested RBAC Privilege Escalation Deadlock

An operator ServiceAccount cannot bind a ClusterRole because it lacks permissions on the target verbs/resources (privilege escalation check). Grant required intermediate permissions.
