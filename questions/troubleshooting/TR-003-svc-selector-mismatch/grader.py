import time
from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    ep = None
    for _ in range(5):
        ep = ctx.get_endpoints("ecommerce", "cart-svc")
        if ep and "subsets" in ep and len(ep["subsets"][0].get("addresses", [])) >= 2:
            break
        time.sleep(1)
    if not ep or "subsets" not in ep:
        return GradeResult(passed=False, score=0, max_score=2, message="Service cart-svc has no endpoints")
    addresses = ep["subsets"][0].get("addresses", [])
    if len(addresses) < 2:
        return GradeResult(passed=False, score=1, max_score=2, message=f"Expected 2 endpoints, found {len(addresses)}")
    return GradeResult(passed=True, score=2, max_score=2, message="cart-svc has 2 healthy endpoints matching backend pods")
