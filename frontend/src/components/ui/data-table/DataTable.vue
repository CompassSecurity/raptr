<script setup lang="ts" generic="TData extends RowData">
import { ref, watch, computed, toRef } from 'vue';
import {
  FlexRender,
  useTable,
  type ColumnDef,
  type ColumnFiltersState,
  type RowData,
  type SortingState,
} from '@tanstack/vue-table'
import { dataTableFeatures, type DataTableFeatures } from './features'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ChevronDown, Check, ArrowUp, ArrowDown, ArrowUpDown } from '@lucide/vue'
import Pagination from '@/components/ui/Pagination.vue'

// Filter option type for select filters
export interface FilterOption {
  label: string;
  value: string;
}

interface PaginationMeta {
  total: number;
  page: number;
  size: number;
  pages: number;
}

const props = defineProps<{
  columns: ColumnDef<DataTableFeatures, TData>[]
  data: TData[]
  pagination?: PaginationMeta
  pageSize?: number
  manualSorting?: boolean
  manualFiltering?: boolean
}>()

const emit = defineEmits<{
  (e: 'page-change', page: number): void
  (e: 'page-size-change', size: number): void
  (e: 'row-click', row: TData): void
  (e: 'sort-change', column: string | null, direction: 'asc' | 'desc' | null): void
  (e: 'column-filter-change', columnId: string, value: string): void
}>()

const sorting = ref<SortingState>([])
const columnFilters = ref<ColumnFiltersState>([])

// In manual mode the table skips its client-side sorted/filtered row models
const table = useTable<DataTableFeatures, TData>({
  features: dataTableFeatures,
  data: toRef(props, 'data'),
  columns: toRef(props, 'columns'),
  manualSorting: toRef(props, 'manualSorting'),
  manualFiltering: toRef(props, 'manualFiltering'),
  state: computed(() => ({
    sorting: sorting.value,
    columnFilters: columnFilters.value,
  })),
  onSortingChange: updaterOrValue => {
     sorting.value = typeof updaterOrValue === 'function' ? updaterOrValue(sorting.value) : updaterOrValue
  },
  onColumnFiltersChange: updaterOrValue => {
     columnFilters.value = typeof updaterOrValue === 'function' ? updaterOrValue(columnFilters.value) : updaterOrValue
  },
})

// Emit sort-change when sorting changes (for server-side sorting)
watch(sorting, (newSorting) => {
  if (props.manualSorting) {
    const sort = newSorting[0];
    if (sort) {
      emit('sort-change', sort.id, sort.desc ? 'desc' : 'asc');
    } else {
      emit('sort-change', null, null);
    }
  }
}, { deep: true })

// Debounced column filter emission for server-side filtering
const filterTimeouts = new Map<string, ReturnType<typeof setTimeout>>();

const handleColumnFilter = (columnId: string, value: string) => {
  // Clear existing timeout for this column
  const existingTimeout = filterTimeouts.get(columnId);
  if (existingTimeout) {
    clearTimeout(existingTimeout);
  }

  // Set new debounced timeout
  const timeout = setTimeout(() => {
    emit('column-filter-change', columnId, value);
    filterTimeouts.delete(columnId);
  }, 300);

  filterTimeouts.set(columnId, timeout);
}

</script>

<template>
  <div class="space-y-4">
    <!-- Table -->
    <div class="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
            <TableHead v-for="header in headerGroup.headers" :key="header.id">
              <div class="flex flex-col gap-2 pt-2 pb-2">
                <div
                  v-if="!header.isPlaceholder"
                  :class="header.column.getCanSort() ? 'cursor-pointer select-none flex items-center gap-2' : ''"
                  @click="header.column.getToggleSortingHandler()?.($event)"
                >
                  <FlexRender :header="header" />
                  <component
                    v-if="header.column.getCanSort()"
                    :is="header.column.getIsSorted() === 'asc' ? ArrowUp : header.column.getIsSorted() === 'desc' ? ArrowDown : ArrowUpDown"
                    class="h-4 w-4"
                  />
                </div>
                <!-- Column Filter -->
                <div v-if="header.column.getCanFilter() && !header.isPlaceholder">
                    <!-- Dropdown filter for columns with filterVariant: 'select' -->
                    <DropdownMenu
                        v-if="(header.column.columnDef.meta as { filterVariant?: string })?.filterVariant === 'select'"
                    >
                        <DropdownMenuTrigger as-child>
                            <Button variant="ghost" size="sm" class="h-8 w-full justify-between px-2 text-xs font-normal border">
                                {{ (header.column.getFilterValue() as string)
                                    ? ((header.column.columnDef.meta as { filterOptions?: FilterOption[] })?.filterOptions ?? []).find(o => o.value === header.column.getFilterValue())?.label
                                    : 'All' }}
                                <ChevronDown class="h-3 w-3 opacity-50" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="start" class="w-[150px]">
                            <DropdownMenuLabel>Filter</DropdownMenuLabel>
                            <DropdownMenuItem
                                @select.prevent="() => {
                                    header.column.setFilterValue(undefined);
                                    if (manualFiltering) {
                                        handleColumnFilter(header.column.id, '');
                                    }
                                }"
                                class="cursor-pointer"
                            >
                                <Check :class="['mr-2 h-4 w-4', !header.column.getFilterValue() ? 'opacity-100' : 'opacity-0']" />
                                All
                            </DropdownMenuItem>
                            <DropdownMenuItem
                                v-for="option in ((header.column.columnDef.meta as { filterOptions?: FilterOption[] })?.filterOptions ?? [])"
                                :key="option.value"
                                @select.prevent="() => {
                                    header.column.setFilterValue(option.value);
                                    if (manualFiltering) {
                                        handleColumnFilter(header.column.id, option.value);
                                    }
                                }"
                                class="cursor-pointer"
                            >
                                <Check :class="['mr-2 h-4 w-4', header.column.getFilterValue() === option.value ? 'opacity-100' : 'opacity-0']" />
                                {{ option.label }}
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                    <!-- Text input filter (default) -->
                    <Input
                        v-else
                        class="h-8 text-xs w-full"
                        :placeholder="`Filter...`"
                        :model-value="(header.column.getFilterValue() as string) ?? ''"
                        @update:model-value="(value: string | number) => {
                          const strValue = String(value);
                          header.column.setFilterValue(strValue);
                          if (manualFiltering) {
                            handleColumnFilter(header.column.id, strValue);
                          }
                        }"
                        @click.stop
                    />
                </div>
              </div>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <template v-if="table.getRowModel().rows?.length">
            <TableRow
              v-for="row in table.getRowModel().rows"
              :key="row.id"
              @click="emit('row-click', row.original)"
              class="cursor-pointer hover:bg-muted/50"
            >
              <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                <FlexRender :cell="cell" />
              </TableCell>
            </TableRow>
          </template>
          <template v-else>
            <TableRow>
              <TableCell :colspan="columns.length" class="h-24 text-center">
                No results.
              </TableCell>
            </TableRow>
          </template>
        </TableBody>
      </Table>
    </div>

    <!-- Pagination -->
    <Pagination
      v-if="pagination"
      :pagination="pagination"
      :page-size="pageSize"
      @page-change="emit('page-change', $event)"
      @page-size-change="emit('page-size-change', $event)"
    />
  </div>
</template>
