import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'
import type { DefineComponent } from 'vue'
import { describe, expect, it } from 'vitest'

import { DataTable } from '@/components/ui'
import Select from '@/components/ui/Select.vue'
import type { DataTableColumn } from '@/components/ui'

// Headless UI observes its popper/panel with ResizeObserver and scrolls the
// active option into view; jsdom implements neither. The DataTable's page-size
// control is a `Select`, so provide the same stubs used in
// `ui-primitives.test.ts`.
if (!('ResizeObserver' in globalThis)) {
  class ResizeObserverStub {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }
  ;(globalThis as { ResizeObserver?: unknown }).ResizeObserver = ResizeObserverStub
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {}
}

/**
 * FE-013 unit coverage for the admin DataTable (TanStack Table v9 wrapper):
 * sorting, global filtering and pagination are driven through the real
 * rendered controls so the test exercises the component contract, not just
 * helper functions.
 */

interface Person {
  id: number
  name: string
  role: string
  score: number
}

const DATA: Person[] = [
  { id: 1, name: 'Charlie', role: 'admin', score: 30 },
  { id: 2, name: 'Alice', role: 'candidate', score: 10 },
  { id: 3, name: 'Bob', role: 'candidate', score: 20 },
  { id: 4, name: 'Dana', role: 'admin', score: 40 },
  { id: 5, name: 'Eve', role: 'candidate', score: 50 },
]

const COLUMNS: DataTableColumn<Person>[] = [
  { key: 'name', header: 'Name' },
  { key: 'role', header: 'Role' },
  { key: 'score', header: 'Score', align: 'right' },
]

// The SFC is generic over its row type; pin the concrete prop shape for the
// test harness so `mount` can type-check without generic inference.
interface DataTableProps {
  data: Person[]
  columns: DataTableColumn<Person>[]
  pageSize?: number
  pageSizeOptions?: number[]
  maxHeight?: string
  loading?: boolean
  interactive?: boolean
}

const DataTableComponent = DataTable as unknown as DefineComponent<DataTableProps>

async function tick(times = 4): Promise<void> {
  for (let i = 0; i < times; i += 1) {
    await nextTick()
    await flushPromises()
  }
}

function mountTable(
  props: Partial<{
    data: Person[]
    columns: DataTableColumn<Person>[]
    pageSize: number
    pageSizeOptions: number[]
    maxHeight: string
    loading: boolean
    interactive: boolean
  }> = {},
): VueWrapper {
  return mount(DataTableComponent, { props: { data: DATA, columns: COLUMNS, ...props } })
}

function columnValues(wrapper: VueWrapper, columnId: string): string[] {
  return wrapper
    .findAll(`[data-testid="datatable-cell-${columnId}"]`)
    .map((cell) => cell.text())
}

function rowCount(wrapper: VueWrapper): number {
  return wrapper.findAll('[data-testid="datatable-row"]').length
}

describe('DataTable — FE-013', () => {
  it('renders one header per column and the current page rows', () => {
    const wrapper = mountTable()
    expect(wrapper.findAll('th').map((th) => th.text())).toEqual(['Name', 'Role', 'Score'])
    expect(rowCount(wrapper)).toBe(5)
    expect(columnValues(wrapper, 'name')).toEqual(['Charlie', 'Alice', 'Bob', 'Dana', 'Eve'])
  })

  it('sorts a column ascending then descending from the header control', async () => {
    const wrapper = mountTable()
    const nameHeader = wrapper.findAll('[data-testid="datatable-sort"]')[0]

    await nameHeader.trigger('click')
    await tick()
    expect(columnValues(wrapper, 'name')).toEqual(['Alice', 'Bob', 'Charlie', 'Dana', 'Eve'])
    expect(wrapper.findAll('th')[0].attributes('aria-sort')).toBe('ascending')

    await nameHeader.trigger('click')
    await tick()
    expect(columnValues(wrapper, 'name')).toEqual(['Eve', 'Dana', 'Charlie', 'Bob', 'Alice'])
    expect(wrapper.findAll('th')[0].attributes('aria-sort')).toBe('descending')
  })

  it('filters rows with the global search box and reports the filtered count', async () => {
    const wrapper = mountTable()
    const search = wrapper.get('[data-testid="datatable-search"] input')

    await search.setValue('candidate')
    await tick()
    expect(columnValues(wrapper, 'name')).toEqual(['Alice', 'Bob', 'Eve'])
    expect(wrapper.text()).toContain('3 total')
  })

  it('shows the empty state when the filter matches nothing', async () => {
    const wrapper = mountTable()
    await wrapper.get('[data-testid="datatable-search"] input').setValue('no-such-row')
    await tick()

    expect(rowCount(wrapper)).toBe(0)
    expect(wrapper.get('[data-testid="datatable-empty"]').text()).toContain('No rows to display')
  })

  it('paginates and navigates with next/previous', async () => {
    const wrapper = mountTable({ pageSize: 2 })

    expect(rowCount(wrapper)).toBe(2)
    expect(columnValues(wrapper, 'name')).toEqual(['Charlie', 'Alice'])
    expect(wrapper.get('[data-testid="datatable-page"]').text()).toBe('Page 1 of 3')

    await wrapper.get('[data-testid="datatable-next"]').trigger('click')
    await tick()
    expect(columnValues(wrapper, 'name')).toEqual(['Bob', 'Dana'])
    expect(wrapper.get('[data-testid="datatable-page"]').text()).toBe('Page 2 of 3')

    await wrapper.get('[data-testid="datatable-prev"]').trigger('click')
    await tick()
    expect(columnValues(wrapper, 'name')).toEqual(['Charlie', 'Alice'])
    expect(wrapper.get('[data-testid="datatable-page"]').text()).toBe('Page 1 of 3')
  })

  it('renders an announced loading state instead of rows', () => {
    const wrapper = mountTable({ loading: true })
    expect(wrapper.get('table').attributes('aria-busy')).toBe('true')
    expect(wrapper.find('[data-testid="datatable-loading"] [role="status"]').exists()).toBe(true)
    expect(rowCount(wrapper)).toBe(0)
    expect(wrapper.find('[data-testid="datatable-empty"]').exists()).toBe(false)
  })

  it('exposes sortable headers as buttons and focusable, activatable rows', async () => {
    const wrapper = mountTable({ interactive: true })

    const sortButtons = wrapper.findAll('[data-testid="datatable-sort"]')
    expect(sortButtons.length).toBe(3)
    expect(sortButtons[0].element.tagName).toBe('BUTTON')

    const firstRow = wrapper.findAll('[data-testid="datatable-row"]')[0]
    expect(firstRow.attributes('tabindex')).toBe('0')

    await firstRow.trigger('keydown.enter')
    expect(wrapper.emitted('row-click')?.[0]?.[0]).toMatchObject({ name: 'Charlie' })
  })

  it('uses a custom cell renderer and right-aligns columns', () => {
    const columns: DataTableColumn<Person>[] = [
      { key: 'name', header: 'Name', cell: (row) => row.name.toUpperCase() },
      { key: 'score', header: 'Score', align: 'right' },
    ]
    const wrapper = mount(DataTableComponent, { props: { data: DATA, columns } })
    expect(columnValues(wrapper, 'name')[0]).toBe('CHARLIE')
    expect(wrapper.get('[data-testid="datatable-cell-score"]').classes()).toContain('text-right')
  })

  it('searches a custom accessor value that is not the displayed cell text', async () => {
    interface Item {
      id: number
      name: string
      code: string
    }
    const items: Item[] = [
      { id: 1, name: 'Alpha', code: 'ZX-100' },
      { id: 2, name: 'Beta', code: 'ZX-200' },
    ]
    const columns: DataTableColumn<Item>[] = [
      {
        key: 'name',
        header: 'Name',
        accessor: (row) => `${row.name} ${row.code}`,
        cell: (row) => row.name,
      },
    ]
    const ItemTable = DataTable as unknown as DefineComponent<{
      data: Item[]
      columns: DataTableColumn<Item>[]
    }>
    const wrapper = mount(ItemTable, { props: { data: items, columns } })

    expect(columnValues(wrapper, 'name')).toEqual(['Alpha', 'Beta'])

    await wrapper.get('[data-testid="datatable-search"] input').setValue('ZX-200')
    await tick()

    expect(rowCount(wrapper)).toBe(1)
    expect(columnValues(wrapper, 'name')).toEqual(['Beta'])
  })

  it('renders the rows-per-page selector with the default options and a non-visual name', () => {
    const wrapper = mountTable()
    const select = wrapper.findComponent(Select)
    const control = wrapper.find('[data-testid="datatable-page-size"]')

    expect(select.exists()).toBe(true)
    expect(control.exists()).toBe(true)
    expect(wrapper.text()).not.toContain('Rows per page')
    expect(control.attributes('aria-label')).toBe('Rows per page')
    expect(select.props('options')).toEqual([
      { value: '10', label: '10' },
      { value: '25', label: '25' },
      { value: '50', label: '50' },
      { value: '100', label: '100' },
    ])
  })

  it('changing the page size shows more rows and updates the page display', async () => {
    const wrapper = mountTable({ pageSize: 2 })
    expect(rowCount(wrapper)).toBe(2)
    expect(wrapper.get('[data-testid="datatable-page"]').text()).toBe('Page 1 of 3')

    const select = wrapper.findComponent(Select)
    select.vm.$emit('update:modelValue', '25')
    await tick()

    expect(rowCount(wrapper)).toBe(5)
    expect(wrapper.get('[data-testid="datatable-page"]').text()).toBe('Page 1 of 1')
    expect(wrapper.emitted('update:pageSize')?.[0]).toEqual([25])
  })

  it('applies the max height to the scroll container and pins the header', () => {
    const wrapper = mountTable({ maxHeight: '12rem' })
    const container = wrapper.get('table').element.parentElement as HTMLElement
    const thead = wrapper.get('thead')

    expect(container.className).toContain('overflow-auto')
    expect(container.style.maxHeight).toBe('12rem')
    expect(thead.classes()).toContain('sticky')
    expect(thead.classes()).toContain('top-0')
    expect(thead.classes()).toContain('bg-elevated')
  })

  it('defaults the scroll container max height to 24rem', () => {
    const wrapper = mountTable()
    const container = wrapper.get('table').element.parentElement as HTMLElement
    expect(container.style.maxHeight).toBe('24rem')
  })
})
