# Solution for WL-C01: Chaos: Trigger Dynamic Pod Preemption via PriorityClasses

Create PriorityClasses `high-priority` (value 1000000) and `low-priority` (value 1000). Deploy high-priority pod that triggers preemption of low-priority pods on saturated node.
