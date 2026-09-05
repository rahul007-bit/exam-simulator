from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("sec-apps", "hardened-api")
    if not pod:
        return GradeResult(False, 0, 3, "Pod hardened-api not found in sec-apps")
    
    spec = pod.get("spec", {})
    sc = spec.get("securityContext", {})
    c_sc = spec.get("containers", [{}])[0].get("securityContext", {})
    
    run_as_user = sc.get("runAsUser") or c_sc.get("runAsUser")
    run_as_non_root = sc.get("runAsNonRoot") or c_sc.get("runAsNonRoot")
    read_only_root = c_sc.get("readOnlyRootFilesystem") or sc.get("readOnlyRootFilesystem")
    
    if run_as_user != 10001 or not run_as_non_root or not read_only_root:
        return GradeResult(False, 1, 3, f"SecurityContext params mismatch: user={run_as_user}, nonRoot={run_as_non_root}, readOnly={read_only_root}")
        
    return GradeResult(True, 3, 3, "hardened-api configured with non-root security context")
