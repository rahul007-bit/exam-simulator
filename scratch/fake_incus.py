"""Fake Incus CLI for offline unit verification of IncusClusterManager.

Simulates: remotes, instances, exec (kubeadm/kubectl), file pull, storage.
State is persisted as JSON so separate subprocess invocations share it.
"""
import sys
import os
import json
import time

STATE_FILE = os.environ["FAKE_INCUS_STATE"]
LOCK_FILE = STATE_FILE + ".lock"


def acquire_lock():
    for _ in range(500):
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            return fd
        except FileExistsError:
            time.sleep(0.01)
    raise RuntimeError("fake_incus lock timeout")


def release_lock(fd):
    os.close(fd)
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass

KUBECONFIG_YAML = """apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://10.0.0.1:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
current-context: kubernetes-admin@kubernetes
users:
- name: kubernetes-admin
  user:
    client-certificate-data: ZmFrZQ==
    client-key-data: ZmFrZQ==
"""


def load_state():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_FILE)


def parse_target(arg, state):
    """Splits 'remote:instance' -> (remote, instance)."""
    if ":" in arg:
        rem, inst = arg.split(":", 1)
        return (rem if rem != "local" else None), inst
    return None, arg


def ikey(rem, inst):
    """State-store key: bare name for local instances (matches engine usage)."""
    return f"{rem}:{inst}" if rem else inst


def irem(key):
    """Inverse of ikey for a stored key: returns (rem, inst)."""
    return (key.split(":", 1) + [None])[:2] if ":" in key else (None, key)


def instance_json(state, rem, inst):
    data = state["instances"].get(ikey(rem, inst))
    if data is None:
        return None
    return {
        "name": inst,
        "type": data.get("type", "container"),
        "status": data.get("status", "Stopped"),
        "created_at": data.get("created_at", "2026-01-01T00:00:00Z"),
        "config": data.get("config", {}),
        "state": {
            "network": {
                "eth0": {
                    "addresses": [
                        {
                            "family": "inet",
                            "scope": "global",
                            "address": data.get("ip", "10.10.10.10"),
                        }
                    ]
                }
            }
        },
    }


def main():
    args = sys.argv[1:]
    lock_fd = acquire_lock()
    try:
        _main(args)
    finally:
        release_lock(lock_fd)


def _main(args):
    state = load_state()
    out = ""
    rc = 0
    err = ""

    if not args:
        rc = 1
    elif args[0] == "--version":
        out = "6.0.0\n"
    elif args[0] == "remote" and len(args) >= 2 and args[1] == "list":
        out = json.dumps(state["remotes"]) + "\n"
    elif args[0] == "info":
        target = args[1]
        inst_part = target.split(":", 1)[1] if ":" in target else target
        inst_key = None
        if ":" in target:
            r, i = target.split(":", 1)
            cand = f"{r if r != 'local' else ''}:{i}" if r != "local" else i
            for k in state["instances"]:
                if k == cand or k.endswith(f":{i}"):
                    inst_key = k
                    break
        else:
            for k in state["instances"]:
                krem, kinst = irem(k)
                if kinst == target:
                    inst_key = k
                    break
        if inst_key:
            snaps = state.get("snapshots", {}).get(inst_key, [])
            out = f"Name: {inst_key}\nStatus: {state['instances'][inst_key].get('status', 'Stopped')}\nSnapshots:\n"
            out += "+------+----------+------------+----------+\n"
            out += "| Name | Taken at | Expires at | Stateful |\n"
            out += "+------+----------+------------+----------+\n"
            for s in snaps:
                out += f"| {s} | 2026/09/08 |            | NO       |\n"
            out += "+------+----------+------------+----------+\n"
        else:
            rem = target.rstrip(":")
            info = state["remotes"].get(rem, {})
            if rem and rem not in ("local",) and not info.get("_responsive", True):
                rc = 1
                err = "unreachable\n"
            elif rem and rem not in ("local",) and rem not in state["remotes"]:
                rc = 1
                err = f"Remote {rem} not found\n"
            else:
                out = "Ok: connected\n"
    elif args[0] == "copy":
        # copy <src> <dst> [--instance-only] [-c ...] [--vm]
        src, dst = args[1], args[2]
        srem, sinst = parse_target(src, state)
        drem, dinst = parse_target(dst, state)
        key = ikey(drem, dinst)
        src_data = state["instances"].get(ikey(srem, sinst.split("/")[0]), {})
        cfg = {}
        i = 3
        while i < len(args):
            if args[i] == "-c" and i + 1 < len(args):
                kv = args[i + 1].split("=", 1)
                cfg[kv[0]] = kv[1]
                i += 2
                continue
            if args[i] == "--vm":
                cfg["_vm"] = True
            i += 1
        state["instances"][key] = {
            "status": "Stopped",
            "config": cfg,
            "ip": src_data.get("ip", "10.10.10.99"),
            "type": "virtual-machine" if cfg.get("_vm") else "container",
        }
        save_state(state)
    elif args[0] == "launch":
        # launch <image> <dst> [-c ...] [--vm]
        image, dst = args[1], args[2]
        drem, dinst = parse_target(dst, state)
        cfg = {}
        i = 3
        while i < len(args):
            if args[i] == "-c" and i + 1 < len(args):
                kv = args[i + 1].split("=", 1)
                cfg[kv[0]] = kv[1]
                i += 2
                continue
            if args[i] == "--vm":
                cfg["_vm"] = True
            i += 1
        state["instances"][ikey(drem, dinst)] = {
            "status": "Running",
            "config": cfg,
            "ip": f"10.10.{len(state['instances'])}.5",
            "type": "virtual-machine" if cfg.get("_vm") else "container",
        }
        save_state(state)
    elif args[0] == "snapshot" and len(args) >= 2 and args[1] == "create":
        inst = args[2]
        name = args[3] if len(args) > 3 else "snap0"
        state.setdefault("snapshots", {}).setdefault(inst, [])
        if name not in state["snapshots"][inst]:
            state["snapshots"][inst].append(name)
        save_state(state)
    elif args[0] == "start":
        key = args[1]
        if key in state["instances"]:
            state["instances"][key]["status"] = "Running"
            save_state(state)
        else:
            rc = 1
            err = f"Instance {key} not found\n"
    elif args[0] == "stop":
        target = args[2] if args[1] == "-f" else args[1]
        if target in state["instances"]:
            state["instances"][target]["status"] = "Stopped"
            save_state(state)
    elif args[0] == "delete":
        target = args[2] if args[1] == "-f" else args[1]
        if target in state["instances"]:
            del state["instances"][target]
            save_state(state)
        else:
            rc = 1
            err = f"Error: Instance not found\n"
    elif args[0] == "list":
        try:
            fmt_idx = args.index("--format")
            targets = args[1:fmt_idx]
        except ValueError:
            targets = args[1:]
        results = []
        for key, data in state["instances"].items():
            rem, inst = irem(key)
            include = True
            if targets:
                include = False
                for t in targets:
                    if ":" in t:
                        trem, tinst = t.split(":", 1)
                        if tinst and tinst != inst:
                            continue
                        if trem and trem not in (rem, "local"):
                            continue
                        include = True
                    elif t == inst:
                        include = True
            if include:
                j = instance_json(state, rem, inst)
                if j:
                    results.append(j)
        out = json.dumps(results) + "\n"
    elif args[0] == "exec":
        target = args[1]
        cmd = args[args.index("--") + 1:]
        if target not in state["instances"]:
            rc = 1
            err = f"Instance {target} not found\n"
        elif "token" in cmd and "create" in cmd:
            out = "kubeadm join 10.10.0.1:6443 --token abcdef.0123456789abcdef --discovery-token-ca-cert-hash sha256:deadbeef\n"
        elif "get" in cmd and "nodes" in cmd:
            nodes = []
            for role in ("node1", "node2", "node3"):
                ready = state.get("nodes_ready", True)
                nodes.append(
                    {
                        "metadata": {"name": f"{role}-test"},
                        "status": {
                            "conditions": [
                                {
                                    "type": "Ready",
                                    "status": "True" if ready else "False",
                                }
                            ]
                        },
                    }
                )
            out = json.dumps({"items": nodes}) + "\n"
        else:
            out = "ok\n"
    elif args[0] == "file" and len(args) >= 3 and args[1] == "pull":
        target_path = args[2]
        rem, rest = (target_path.split(":", 1) if ":" in target_path else (None, target_path))
        inst = rest.split("/")[0]
        found = any(
            (k == f"{rem}:{inst}" if rem else k == inst or k.endswith(f":{inst}"))
            for k in state["instances"]
        )
        if found:
            out = KUBECONFIG_YAML
        else:
            rc = 1
            err = f"Instance {target_path} not found\n"
    elif args[0] == "storage" and len(args) >= 2:
        sub = args[1]
        if sub == "list":
            out = json.dumps(state.get("pools", [])) + "\n"
        elif sub == "volume":
            if "list" in args:
                out = json.dumps(state.get("volumes", [])) + "\n"
            elif "delete" in args:
                state["volumes"] = [
                    v for v in state.get("volumes", [])
                    if v.get("name") not in " ".join(args)
                ]
                save_state(state)
    else:
        rc = 1
        err = "unsupported: " + " ".join(args) + "\n"

    if out:
        sys.stdout.write(out)
    if err:
        sys.stderr.write(err)
    sys.exit(rc)


if __name__ == "__main__":
    main()
