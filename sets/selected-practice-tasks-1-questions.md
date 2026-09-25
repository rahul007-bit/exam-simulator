# Selected Practice Tasks (1 Questions)

- **Session ID:** `session-1788616761`
- **Total Tasks:** 1
- **Total Points:** 2 pts
- **Time Limit:** Untimed
- **Pass Threshold:** 66%
- **Mode:** `sequential`

To navigate tasks during the exam:
- Run `examctl task` to view the current active task
- Run `examctl next` to deploy and advance to the next task
- Run `examctl prev` to return to the previous task
- Run `examctl jump <num>` to jump directly to a task
- Run `examctl status` to view overall exam progress

---

### Task 1: Create PersistentVolume and Bind to PersistentVolumeClaim [EASY] (2 pts) (CURRENT ACTIVE TASK)
- **ID:** `ST-001`
- **Context:** `k3d-cka`
- **Namespace:** `data-storage`

#### Description
In namespace `data-storage`:
1. Create a PersistentVolume named `app-pv` with capacity `2Gi`, accessMode `ReadWriteOnce`, hostPath `/mnt/data/app`, and storageClassName `manual`.
2. Create a PersistentVolumeClaim named `app-pvc` in namespace `data-storage` requesting `2Gi` with accessMode `ReadWriteOnce` and storageClassName `manual`.

---
