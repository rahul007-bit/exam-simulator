from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("secure-pipeline", "hardened-worker")
    if not pod:
        return GradeResult(False, 0, 3, "Pod hardened-worker not found in secure-pipeline")

    spec = pod.get("spec", {})
    if spec.get("serviceAccountName") != "pipeline-runner":
        return GradeResult(False, 1, 3, f"Pod serviceAccountName is {spec.get('serviceAccountName')}, expected pipeline-runner")

    pod_sc = spec.get("securityContext", {})
    containers = spec.get("containers", [])
    if not containers:
        return GradeResult(False, 1, 3, "No containers found in pod hardened-worker")
    c_sc = containers[0].get("securityContext", {})

    run_as_non_root = c_sc.get("runAsNonRoot") if c_sc.get("runAsNonRoot") is not None else pod_sc.get("runAsNonRoot")
    run_as_user = c_sc.get("runAsUser") if c_sc.get("runAsUser") is not None else pod_sc.get("runAsUser")
    allow_priv_esc = c_sc.get("allowPrivilegeEscalation")
    read_only_root = c_sc.get("readOnlyRootFilesystem") if c_sc.get("readOnlyRootFilesystem") is not None else pod_sc.get("readOnlyRootFilesystem")
    drop_caps = c_sc.get("capabilities", {}).get("drop", [])

    if not run_as_non_root:
        return GradeResult(False, 1, 3, "runAsNonRoot is not set to true")
    if run_as_user != 10001:
        return GradeResult(False, 1, 3, f"runAsUser is {run_as_user}, expected 10001")
    if allow_priv_esc is not False:
        return GradeResult(False, 2, 3, "allowPrivilegeEscalation is not set to false")
    if not read_only_root:
        return GradeResult(False, 2, 3, "readOnlyRootFilesystem is not set to true")
    if "ALL" not in drop_caps:
        return GradeResult(False, 2, 3, f"Capabilities drop does not contain ALL (drop: {drop_caps})")

    return GradeResult(True, 3, 3, "Pod hardened-worker is running with all required SecurityContext constraints")
