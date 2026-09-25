<script setup lang="ts" generic="T extends object">
import {
  columnFilteringFeature,
  createColumnHelper,
  createFilteredRowModel,
  createPaginatedRowModel,
  createSortedRowModel,
  filterFn_includesString,
  FlexRender,
  globalFilteringFeature,
  rowPaginationFeature,
  rowSortingFeature,
  sortFn_alphanumeric,
  sortFn_basic,
  sortFn_text,
  tableFeatures,
  useTable,
} from '@tanstack/vue-table'
import type { ColumnDef } from '@tanstack/vue-table'
import { computed, ref, toRef, useId, watch } from 'vue'
import type { Ref } from 'vue'

import Button from './Button.vue'
import Icon from '../Icon.vue'
import Input from './Input.vue'
import Select from './Select.vue'
import Spinner from './Spinner.vue'
import { FOCUS_RING } from './shared'
import type { DataTableColumn } from './index'
import type { SelectOption } from './types'

/**
 * DataTable (FE-013) — admin-only table wrapper around `@tanstack/vue-table`.
 *
 * Registers only the features the admin surface needs (sorting, global
 * filtering, pagination) and renders an accessible, token-styled table:
 * sortable headers are real buttons in a `th[scope=col]` carrying `aria-sort`,
 * rows can be focused and activated from the keyboard, and empty/loading
 * states are announced. Styling resolves to design tokens only (no raw hex, no
 * glow/gradient, no emoji).
 */
const features = tableFeatures({
  rowSortingFeature,
  sortedRowModel: createSortedRowModel(),
  columnFilteringFeature,
  globalFilteringFeature,
  filteredRowModel: createFilteredRowModel(),
  rowPaginationFeature,
  paginatedRowModel: createPaginatedRowModel(),
  filterFns: { includesString: filterFn_includesString },
  sortFns: { alphanumeric: sortFn_alphanumeric, text: sortFn_text, basic: sortFn_basic },
})

const props = withDefaults(
  defineProps<{
    data: T[]
    columns: DataTableColumn<T>[]
    caption?: string
    loading?: boolean
    emptyMessage?: string
    searchable?: boolean
    searchPlaceholder?: string
    searchLabel?: string
    loadingLabel?: string
    paginate?: boolean
    pageSize?: number
    pageSizeOptions?: number[]
    maxHeight?: string
    interactive?: boolean
    rowKey?: (row: T) => string | number
  }>(),
  {
    caption: 'Data table',
    loading: false,
    emptyMessage: 'No rows to display.',
    searchable: true,
    searchPlaceholder: 'Search',
    searchLabel: 'Search',
    loadingLabel: 'Loading rows',
    paginate: true,
    pageSize: 10,
    pageSizeOptions: () => [10, 25, 50, 100],
    maxHeight: '24rem',
    interactive: false,
  },
)

const emit = defineEmits<{
  'row-click': [row: T, index: number]
  'update:pageSize': [size: number]
}>()

const columnHelper = createColumnHelper<typeof features, Record<string, unknown>>()

const tableColumns = props.columns.map((column) =>
  columnHelper.accessor(
    (row: Record<string, unknown>) => (column.accessor ? column.accessor(row as T) : row[column.key]),
    {
      id: column.key,
      header: column.header,
      sortFn: 'alphanumeric',
      enableSorting: column.sortable ?? true,
      enableGlobalFilter: column.filterable ?? true,
      // v9 has no implicit default cell, so fall back to the accessor value.
      cell: (context) =>
        column.cell
          ? column.cell(context.row.original as T)
          : (context.getValue() as string | number),
    },
  ),
) as unknown as ColumnDef<typeof features, Record<string, unknown>>[]

const table = useTable({
  features,
  columns: tableColumns,
  data: toRef(props, 'data') as unknown as Ref<Record<string, unknown>[]>,
  getRowId: (row: Record<string, unknown>, index: number) =>
    props.rowKey ? String(props.rowKey(row as T)) : String(index),
  initialState: {
    pagination: {
      pageIndex: 0,
      pageSize: props.paginate ? props.pageSize : Number.POSITIVE_INFINITY,
    },
  },
  enableSorting: true,
  enableSortingRemoval: false,
  enableMultiSort: false,
  enableFilters: true,
  enableGlobalFilter: true,
  globalFilterFn: 'includesString',
  autoResetPageIndex: true,
})

const selectedPageSize = ref(props.pageSize)

watch(
  () => [props.pageSize, props.paginate] as const,
  ([size, paginate]) => {
    selectedPageSize.value = size
    table.setPageSize(paginate ? size : Number.POSITIVE_INFINITY)
  },
)

const uid = useId()
const captionId = computed(() => `datatable-caption-${uid}`)

const search = computed({
  get: () => (table.atoms.globalFilter.get() as string | undefined) ?? '',
  set: (value: string) => table.setGlobalFilter(value),
})

const headerGroups = computed(() => table.getHeaderGroups())
const rows = computed(() => table.getRowModel().rows)
const rowCount = computed(() => table.getFilteredRowModel().rows.length)
const pagination = computed(() => table.atoms.pagination.get())
const pageCount = computed(() => Math.max(table.getPageCount(), 1))
const canPrevious = computed(() => table.getCanPreviousPage())
const canNext = computed(() => table.getCanNextPage())

const pageSizeSelectOptions = computed<SelectOption[]>(() => {
  const sizes = new Set(props.pageSizeOptions)
  sizes.add(props.pageSize)
  return Array.from(sizes)
    .sort((a, b) => a - b)
    .map((size) => ({ value: String(size), label: String(size) }))
})

const pageSizeValue = computed({
  get: () => String(selectedPageSize.value),
  set: (value: string) => changePageSize(Number(value)),
})

function changePageSize(size: number): void {
  selectedPageSize.value = size
  table.setPageSize(size)
  table.setPageIndex(0)
  emit('update:pageSize', size)
}

const alignByKey = computed(() =>
  Object.fromEntries(props.columns.map((column) => [column.key, column.align ?? 'left'])),
)

const ALIGN: Record<'left' | 'center' | 'right', string> = {
  left: 'text-left',
  center: 'text-center',
  right: 'text-right',
}

function cellAlign(columnId: string): string {
  return ALIGN[(alignByKey.value[columnId] as 'left' | 'center' | 'right') ?? 'left']
}

function ariaSort(column: {
  getCanSort: () => boolean
  getIsSorted: () => false | 'asc' | 'desc'
}): 'ascending' | 'descending' | 'none' | undefined {
  if (!column.getCanSort()) return undefined
  const sorted = column.getIsSorted()
  if (sorted === 'asc') return 'ascending'
  if (sorted === 'desc') return 'descending'
  return 'none'
}

function activateRow(row: { original: Record<string, unknown>; index: number }): void {
  emit('row-click', row.original as T, row.index)
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <div v-if="searchable" class="flex items-end justify-between gap-3">
      <div class="w-full max-w-xs">
        <Input
          :model-value="search"
          :label="searchLabel"
          :placeholder="searchPlaceholder"
          type="search"
          data-testid="datatable-search"
          @update:model-value="search = $event"
        />
      </div>
      <p class="pb-1 text-xs text-text-muted">{{ rowCount }} total</p>
    </div>

    <div
      class="overflow-auto rounded-[var(--radius-md)] border border-border"
      :style="{ maxHeight }"
    >
      <table
        class="w-full border-collapse text-sm text-text"
        :aria-busy="loading ? 'true' : undefined"
        :aria-describedby="captionId"
      >
        <caption :id="captionId" class="sr-only">
          {{ caption }}
        </caption>
        <thead class="sticky top-0 z-10 bg-elevated">
          <tr v-for="headerGroup in headerGroups" :key="headerGroup.id">
            <th
              v-for="header in headerGroup.headers"
              :key="header.id"
              scope="col"
              :aria-sort="ariaSort(header.column)"
              :class="[
                'border-b border-border px-3 py-2 font-semibold text-text-muted',
                cellAlign(header.column.id),
              ]"
            >
              <button
                v-if="header.column.getCanSort()"
                type="button"
                data-testid="datatable-sort"
                :class="[
                  'group inline-flex items-center gap-1 rounded-[var(--radius-sm)] px-1 py-0.5 text-left font-semibold text-text transition-colors hover:text-accent-text',
                  header.column.getIsSorted() ? 'text-accent-text' : '',
                  FOCUS_RING,
                ]"
                @click="header.column.getToggleSortingHandler()?.($event)"
              >
                <FlexRender v-if="!header.isPlaceholder" :header="header" />
                <Icon
                  v-if="header.column.getIsSorted() === 'asc'"
                  name="chevron-up"
                  :size="14"
                  class="flex-none"
                />
                <Icon
                  v-else-if="header.column.getIsSorted() === 'desc'"
                  name="chevron-down"
                  :size="14"
                  class="flex-none"
                />
                <Icon
                  v-else
                  name="chevrons-up-down"
                  :size="14"
                  class="flex-none opacity-0 transition-opacity group-hover:opacity-60"
                />
              </button>
              <FlexRender v-else-if="!header.isPlaceholder" :header="header" />
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading" data-testid="datatable-loading">
            <td :colspan="props.columns.length" class="px-3 py-10 text-center">
              <Spinner size="md" :label="loadingLabel" />
            </td>
          </tr>
          <tr v-else-if="rows.length === 0" data-testid="datatable-empty">
            <td :colspan="props.columns.length" class="px-3 py-10 text-center text-text-muted">
              {{ emptyMessage }}
            </td>
          </tr>
          <template v-else>
            <tr
              v-for="row in rows"
              :key="row.id"
              :data-testid="`datatable-row`"
              :tabindex="interactive ? 0 : undefined"
              :class="[
                'border-b border-border transition-colors last:border-b-0',
                interactive
                  ? 'cursor-pointer hover:bg-hover focus-visible:bg-hover focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[var(--focus-ring-color)]'
                  : '',
              ]"
              @click="interactive && activateRow(row)"
              @keydown.enter="interactive && activateRow(row)"
              @keydown.space.prevent="interactive && activateRow(row)"
            >
              <td
                v-for="cell in row.getAllCells()"
                :key="cell.id"
                :data-testid="`datatable-cell-${cell.column.id}`"
                :class="['px-3 py-2', cellAlign(cell.column.id)]"
              >
                <FlexRender :cell="cell" />
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <div
      v-if="paginate"
      class="flex flex-wrap items-end justify-between gap-3"
      data-testid="datatable-pagination"
    >
      <p class="pb-1.5 text-sm text-text-muted" data-testid="datatable-page">
        Page {{ pagination.pageIndex + 1 }} of {{ pageCount }}
      </p>
      <div class="flex flex-wrap items-end gap-3">
        <div class="w-28">
          <Select
            v-model="pageSizeValue"
            :options="pageSizeSelectOptions"
            aria-label="Rows per page"
            title="Rows per page"
            data-testid="datatable-page-size"
          />
        </div>
        <div class="flex items-center gap-2 pb-0.5">
          <Button
            variant="secondary"
            size="sm"
            data-testid="datatable-prev"
            :disabled="!canPrevious"
            @click="table.previousPage()"
          >
            Previous
          </Button>
          <Button
            variant="secondary"
            size="sm"
            data-testid="datatable-next"
            :disabled="!canNext"
            @click="table.nextPage()"
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
