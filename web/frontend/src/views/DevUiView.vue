<script setup lang="ts">
import { ref } from 'vue'

import {
  Badge,
  Button,
  Card,
  Chip,
  DataTable,
  Icon,
  ICON_NAMES,
  Input,
  Modal,
  SegmentedControl,
  Select,
  Spinner,
} from '@/components/ui'
import type { ChipVariant, DataTableColumn, SelectOption, SegmentOption } from '@/components/ui'

/**
 * Dev-only primitives gallery (FE-012).
 *
 * Renders every primitive in its variants and states so a browser can run axe
 * and a human can Tab through the controls. Registered only on the `/dev/ui`
 * route in development (see `src/router/index.ts`); it is not part of the
 * candidate or admin flows.
 */

const name = ref('')
const email = ref('not-an-email')
const role = ref('candidate')
const plan = ref('desktop')
const modalOpen = ref(false)

const SELECT_OPTIONS: SelectOption[] = [
  { value: 'candidate', label: 'Candidate' },
  { value: 'admin', label: 'Administrator' },
  { value: 'reviewer', label: 'Reviewer (disabled)', disabled: true },
]

const SEGMENTS: SegmentOption[] = [
  { value: 'desktop', label: 'Desktop' },
  { value: 'terminal', label: 'Terminal' },
  { value: 'disabled', label: 'Replay (disabled)', disabled: true },
]

const chipVariant: ChipVariant = 'accent'
interface ChipItem {
  id: number
  label: string
  variant: ChipVariant
}
const chips = ref<ChipItem[]>([
  { id: 1, label: 'react', variant: 'accent' },
  { id: 2, label: 'vue', variant: 'success' },
  { id: 3, label: 'angular', variant: 'danger' },
])
let nextChip = 4

function removeChip(id: number): void {
  chips.value = chips.value.filter((chip) => chip.id !== id)
}

function addChip(): void {
  chips.value = [...chips.value, { id: nextChip, label: `chip-${nextChip}`, variant: 'info' }]
  nextChip += 1
}

interface DemoSession {
  id: string
  candidate: string
  preset: string
  status: 'active' | 'completed' | 'expired'
  score: number
}

// Sample admin sessions for the FE-013 DataTable demo: enough rows to exercise
// pagination (12 rows / 5 per page), sortable columns and the global filter.
const sessions: DemoSession[] = [
  { id: 'S-1001', candidate: 'Ada Lovelace', preset: 'CKA Full', status: 'active', score: 0 },
  { id: 'S-1002', candidate: 'Grace Hopper', preset: 'CKA Practice', status: 'completed', score: 92 },
  { id: 'S-1003', candidate: 'Alan Turing', preset: 'CKAD Full', status: 'completed', score: 88 },
  { id: 'S-1004', candidate: 'Katherine Johnson', preset: 'CKA Full', status: 'active', score: 0 },
  { id: 'S-1005', candidate: 'Linus Torvalds', preset: 'CKS Full', status: 'expired', score: 41 },
  { id: 'S-1006', candidate: 'Barbara Liskov', preset: 'CKA Practice', status: 'completed', score: 96 },
  { id: 'S-1007', candidate: 'Margaret Hamilton', preset: 'CKS Full', status: 'completed', score: 79 },
  { id: 'S-1008', candidate: 'Dennis Ritchie', preset: 'CKAD Full', status: 'active', score: 0 },
  { id: 'S-1009', candidate: 'Radia Perlman', preset: 'CKA Full', status: 'completed', score: 84 },
  { id: 'S-1010', candidate: 'Ken Thompson', preset: 'CKA Practice', status: 'expired', score: 55 },
  { id: 'S-1011', candidate: 'Frances Allen', preset: 'CKS Full', status: 'completed', score: 91 },
  { id: 'S-1012', candidate: 'Anita Borg', preset: 'CKAD Full', status: 'active', score: 0 },
]

const sessionColumns: DataTableColumn<DemoSession>[] = [
  { key: 'id', header: 'Session' },
  { key: 'candidate', header: 'Candidate' },
  { key: 'preset', header: 'Preset' },
  { key: 'status', header: 'Status' },
  { key: 'score', header: 'Score', align: 'right' },
]
</script>

<template>
  <main data-testid="gallery" class="mx-auto flex max-w-5xl flex-col gap-8 p-6">
    <header class="flex flex-col gap-1">
      <h1 class="m-0 text-xl font-semibold text-text">UI Primitives Gallery</h1>
      <p class="m-0 text-sm text-text-muted">
        Dev-only route <code>/dev/ui</code>. Every primitive in its variants and states for axe and
        keyboard review.
      </p>
    </header>

    <Card data-testid="card-default" title="Buttons" subtitle="variants, sizes, disabled, loading">
      <div class="flex flex-col gap-4">
        <div class="flex flex-wrap items-center gap-2">
          <Button data-testid="btn-primary" variant="primary">Primary</Button>
          <Button data-testid="btn-secondary" variant="secondary">Secondary</Button>
          <Button data-testid="btn-ghost" variant="ghost">Ghost</Button>
          <Button data-testid="btn-danger" variant="danger">Danger</Button>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <Button data-testid="btn-sm" size="sm">Small</Button>
          <Button data-testid="btn-md" size="md">Medium</Button>
          <Button data-testid="btn-lg" size="lg">Large</Button>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <Button data-testid="btn-disabled" variant="primary" disabled>Disabled</Button>
          <Button data-testid="btn-loading" variant="primary" loading>Loading</Button>
          <Button data-testid="btn-ghost-loading" variant="secondary" loading>Saving</Button>
        </div>
        <div>
          <Button data-testid="btn-block" variant="secondary" block>Full-width button</Button>
        </div>
      </div>
    </Card>

    <Card title="Inputs" subtitle="label, hint, required, error, disabled, readonly">
      <div class="grid gap-4 sm:grid-cols-2">
        <Input
          v-model="name"
          data-testid="input-name"
          label="Display name"
          placeholder="Ada Lovelace"
          hint="Shown next to your session."
        />
        <Input
          v-model="email"
          data-testid="input-email"
          label="Email"
          type="email"
          required
          error="Enter a valid email address."
        />
        <Input
          data-testid="input-disabled"
          label="Disabled"
          model-value="Read-only value"
          disabled
        />
        <Input
          data-testid="input-readonly"
          label="Read-only"
          model-value="Copyable value"
          readonly
        />
      </div>
    </Card>

    <Card title="Select" subtitle="Headless UI Listbox">
      <div class="grid gap-4 sm:grid-cols-2">
        <div data-testid="select-basic">
          <Select v-model="role" label="Role" :options="SELECT_OPTIONS" />
        </div>
        <div data-testid="select-disabled">
          <Select
            model-value="candidate"
            label="Disabled select"
            :options="SELECT_OPTIONS"
            disabled
          />
        </div>
      </div>
    </Card>

    <Card title="Badges &amp; Chips" subtitle="semantic variants; chips can be dismissed">
      <div class="flex flex-col gap-4">
        <div class="flex flex-wrap items-center gap-2">
          <Badge data-testid="badge-neutral" variant="neutral">Neutral</Badge>
          <Badge data-testid="badge-accent" variant="accent">Accent</Badge>
          <Badge data-testid="badge-success" variant="success">Success</Badge>
          <Badge data-testid="badge-warning" variant="warning">Warning</Badge>
          <Badge data-testid="badge-danger" variant="danger">Danger</Badge>
          <Badge data-testid="badge-info" variant="info">Info</Badge>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <Badge variant="neutral" size="md">Medium badge</Badge>
          <Badge variant="accent" size="md">Medium accent</Badge>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <Chip
            v-for="chip in chips"
            :key="chip.id"
            :data-testid="`chip-${chip.id}`"
            :variant="chip.variant"
            removable
            :remove-label="`Remove ${chip.label}`"
            @remove="removeChip(chip.id)"
          >
            {{ chip.label }}
          </Chip>
          <Chip data-testid="chip-static" :variant="chipVariant">static chip</Chip>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm" @click="addChip">Add chip</Button>
        </div>
      </div>
    </Card>

    <Card title="Cards" subtitle="default, outlined, elevated">
      <div class="grid gap-4 sm:grid-cols-3">
        <Card data-testid="card-variant-default" variant="default" title="Default">
          <p class="m-0 text-sm text-text-muted">Surface card with a subtle border.</p>
        </Card>
        <Card data-testid="card-variant-outlined" variant="outlined" title="Outlined">
          <p class="m-0 text-sm text-text-muted">Transparent with a stronger border.</p>
        </Card>
        <Card data-testid="card-variant-elevated" variant="elevated" title="Elevated">
          <p class="m-0 text-sm text-text-muted">Elevated surface with a small shadow.</p>
        </Card>
      </div>
      <div class="mt-4">
        <Card variant="default" title="Card with footer" subtitle="slots: header, actions, footer">
          <template #actions>
            <Button variant="ghost" size="sm">Action</Button>
          </template>
          <p class="m-0 text-sm text-text-muted">Body content.</p>
          <template #footer>Footer content</template>
        </Card>
      </div>
    </Card>

    <Card title="Modal" subtitle="Headless UI Dialog, focus trapped">
      <Button data-testid="modal-open" variant="primary" @click="modalOpen = true">
        Open modal
      </Button>
      <Modal
        v-model="modalOpen"
        title="Confirm exam action"
        description="This is a demo dialog. Escape or the close button dismisses it."
        size="md"
      >
        <p class="m-0 text-sm text-text">
          Dialog content sits in a focus trap with a labelled title and description.
        </p>
        <template #footer>
          <Button data-testid="modal-confirm" variant="primary" @click="modalOpen = false">
            Confirm
          </Button>
          <Button data-testid="modal-cancel" variant="secondary" @click="modalOpen = false">
            Cancel
          </Button>
        </template>
      </Modal>
    </Card>

    <Card title="Spinner" subtitle="sizes; standalone (announced) and decorative">
      <div class="flex flex-wrap items-center gap-6">
        <Spinner data-testid="spinner-sm" size="sm" label="Loading small" />
        <Spinner data-testid="spinner-md" size="md" label="Loading medium" />
        <Spinner data-testid="spinner-lg" size="lg" label="Loading large" />
        <Button variant="primary" loading>Saving changes</Button>
      </div>
    </Card>

    <Card title="Segmented control" subtitle="Headless UI RadioGroup">
      <div class="flex flex-col gap-4">
        <div data-testid="segmented">
          <SegmentedControl v-model="plan" label="Workspace view" :options="SEGMENTS" />
        </div>
        <SegmentedControl v-model="plan" label="Compact view" :options="SEGMENTS" size="sm" />
        <SegmentedControl model-value="desktop" :options="SEGMENTS" disabled label="Disabled" />
      </div>
    </Card>

    <Card title="Icons" subtitle="inline-SVG set (FE-014); stroke=currentColor, decorative by default">
      <ul class="grid list-none grid-cols-2 gap-2 p-0 sm:grid-cols-3 md:grid-cols-4">
        <li
          v-for="iconName in ICON_NAMES"
          :key="iconName"
          class="flex items-center gap-2 rounded-[var(--radius-sm)] border border-border px-2 py-1.5 text-text"
        >
          <Icon :name="iconName" :size="18" class="flex-none text-accent-text" />
          <code class="truncate text-xs text-text-muted">{{ iconName }}</code>
        </li>
      </ul>
    </Card>

    <Card title="DataTable" subtitle="TanStack Table: sorting, global filter, pagination (admin only)">
      <DataTable
        data-testid="datatable-demo"
        :data="sessions"
        :columns="sessionColumns"
        caption="Sample candidate sessions"
        search-label="Filter sessions"
        search-placeholder="Filter by candidate, preset or status"
        :page-size="5"
        interactive
      />
    </Card>
  </main>
</template>
