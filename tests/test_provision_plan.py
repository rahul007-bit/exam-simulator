"""P1 — conditional provisioning plan.

Decides which sandboxes a session needs from its target contexts so Incus
microVMs (kubeadm) are not provisioned for k3d-only exams.
"""
import unittest

try:
    from core.sandbox_orchestrator import provision_plan

    HAS_ORCH = True
except Exception:  # pragma: no cover - host-only deps
    HAS_ORCH = False


@unittest.skipUnless(HAS_ORCH, "sandbox_orchestrator unavailable")
class ProvisionPlanTest(unittest.TestCase):
    def test_k3d_only(self):
        plan = provision_plan(["k3d-cka"])
        self.assertEqual({"k3d": True, "kubeadm": False, "desktop": True}, plan)

    def test_kubeadm_only(self):
        plan = provision_plan(["kubeadm-vms"])
        self.assertEqual({"k3d": False, "kubeadm": True, "desktop": True}, plan)

    def test_mixed_contexts(self):
        plan = provision_plan(["k3d-cka", "kubeadm-vms"])
        self.assertEqual({"k3d": True, "kubeadm": True, "desktop": True}, plan)

    def test_unknown_contexts_default_to_legacy(self):
        self.assertEqual(
            {"k3d": True, "kubeadm": True, "desktop": True},
            provision_plan(None),
        )

    def test_empty_contexts_k3d_only(self):
        self.assertEqual({"k3d": True, "kubeadm": False, "desktop": True}, provision_plan([]))

    def test_desktop_always_provisioned(self):
        for contexts in (["k3d-cka"], ["kubeadm-vms"], None):
            self.assertTrue(provision_plan(contexts)["desktop"])

    def test_custom_kubeadm_context(self):
        plan = provision_plan(["kubeadm-prod"], kubeadm_context="kubeadm-prod")
        self.assertFalse(plan["k3d"])
        self.assertTrue(plan["kubeadm"])


if __name__ == "__main__":
    unittest.main()
