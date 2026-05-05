<script setup lang="ts">
import {
    type ColumnDef,
    getCoreRowModel,
    type RowSelectionState,
    useVueTable,
} from '@tanstack/vue-table';
import { Check, ChevronDown, Loader2 } from '@lucide/vue';
import { computed, ref, watch } from 'vue';
import { toast } from 'vue-sonner';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import Pagination from '@/components/ui/Pagination.vue';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { activityTemplateService } from '@/services/activityTemplateService';
import type { ActivityTemplateRead, PaginationState } from '@/types/utils';

const props = defineProps<{
    open: boolean;
    assessmentId: string;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

// Data state
const templates = ref<ActivityTemplateRead[]>([]);
const loading = ref(false);
const importing = ref(false);
const pagination = ref<PaginationState>({
    total: 0,
    page: 1,
    size: 50,
    pages: 1,
});

// Table state
const rowSelection = ref<RowSelectionState>({});
const sortBy = ref<string | null>(null);
const sortOrder = ref<'asc' | 'desc' | null>(null);

// Server-side column filters
const columnFilters = ref<Record<string, string | string[]>>({});

// Filter options
const priorityOptions = ['Critical', 'High', 'Medium', 'Low'];

// Column definitions
const columns: ColumnDef<ActivityTemplateRead>[] = [
    {
        id: 'select',
        header: 'select-header',
        cell: 'select-cell',
        enableSorting: false,
        enableColumnFilter: false,
    },
    {
        accessorKey: 'name',
        header: 'Name',
        enableColumnFilter: true,
        meta: { filterVariant: 'text' },
    },
    {
        accessorKey: 'mitre_tactic',
        header: 'Tactic',
        enableColumnFilter: true,
        meta: { filterVariant: 'text' },
    },
    {
        accessorKey: 'mitre_technique',
        header: 'Technique',
        enableColumnFilter: true,
        meta: { filterVariant: 'text' },
    },
    {
        accessorKey: 'provider',
        header: 'Provider',
        enableColumnFilter: true,
        meta: { filterVariant: 'text' },
    },
    {
        accessorKey: 'priority',
        header: 'Priority',
        enableColumnFilter: true,
        meta: { filterVariant: 'multiselect', filterOptions: priorityOptions },
        cell: ({ row }) => row.original.priority || '-',
    },
];

const table = useVueTable({
    get data() {
        return templates.value;
    },
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
    manualFiltering: true,
    enableRowSelection: true,
    getRowId: (row) => row.id,
    state: {
        get rowSelection() {
            return rowSelection.value;
        },
    },
    onRowSelectionChange: (updaterOrValue) => {
        rowSelection.value =
            typeof updaterOrValue === 'function'
                ? updaterOrValue(rowSelection.value)
                : updaterOrValue;
    },
});

// Computed
const selectedCount = computed(() => Object.keys(rowSelection.value).length);
const selectedIds = computed(() => Object.keys(rowSelection.value));

// Selection helpers - use rowSelection directly for Vue reactivity
const isSelected = (rowId: string) => !!rowSelection.value[rowId];
const toggleSelection = (rowId: string, value?: boolean) => {
    const newValue = value ?? !rowSelection.value[rowId];
    if (newValue) {
        rowSelection.value = { ...rowSelection.value, [rowId]: true };
    } else {
        const { [rowId]: _, ...rest } = rowSelection.value;
        rowSelection.value = rest;
    }
};
const toggleAllRows = (value: boolean) => {
    if (value) {
        const newSelection: RowSelectionState = {};
        table.getRowModel().rows.forEach((row) => {
            newSelection[row.id] = true;
        });
        rowSelection.value = { ...rowSelection.value, ...newSelection };
    } else {
        const currentRowIds = new Set(
            table.getRowModel().rows.map((r) => r.id),
        );
        const newSelection: RowSelectionState = {};
        Object.keys(rowSelection.value).forEach((id) => {
            if (!currentRowIds.has(id)) {
                newSelection[id] = true;
            }
        });
        rowSelection.value = newSelection;
    }
};
const allRowsSelected = computed(() => {
    const rows = table.getRowModel().rows;
    if (rows.length === 0) return false;
    return rows.every((row) => rowSelection.value[row.id]);
});
const someRowsSelected = computed(() => {
    const rows = table.getRowModel().rows;
    if (rows.length === 0) return false;
    const selectedRows = rows.filter((row) => rowSelection.value[row.id]);
    return selectedRows.length > 0 && selectedRows.length < rows.length;
});

// Fetch templates
async function fetchTemplates() {
    loading.value = true;
    try {
        const offset = (pagination.value.page - 1) * pagination.value.size;

        // Build flat params with column filters
        const params: Record<string, unknown> = {
            offset,
            limit: pagination.value.size,
            sort_by: sortBy.value || undefined,
            sort_order: sortOrder.value || undefined,
        };

        // Add column filters to params
        for (const [key, value] of Object.entries(columnFilters.value)) {
            if (
                value &&
                (typeof value === 'string'
                    ? value.length > 0
                    : value.length > 0)
            ) {
                params[key] = value;
            }
        }

        const data = await activityTemplateService.getActivityTemplates(params);
        templates.value = data.items;
        pagination.value = {
            total: data.total,
            page: data.page,
            size: data.size,
            pages: data.pages,
        };
    } catch (error) {
        // Error handled globally
    } finally {
        loading.value = false;
    }
}

// Handlers
const handlePageChange = (page: number) => {
    pagination.value.page = page;
    fetchTemplates();
};

const handlePageSizeChange = (size: number) => {
    pagination.value.size = size;
    pagination.value.page = 1;
    fetchTemplates();
};

const handleSortChange = (columnId: string) => {
    if (sortBy.value === columnId) {
        if (sortOrder.value === 'asc') {
            sortOrder.value = 'desc';
        } else if (sortOrder.value === 'desc') {
            sortBy.value = null;
            sortOrder.value = null;
        } else {
            sortOrder.value = 'asc';
        }
    } else {
        sortBy.value = columnId;
        sortOrder.value = 'asc';
    }
    pagination.value.page = 1;
    fetchTemplates();
};

// Column filter handlers
let filterTimeout: ReturnType<typeof setTimeout>;
const handleTextFilter = (columnId: string, value: string) => {
    clearTimeout(filterTimeout);
    filterTimeout = setTimeout(() => {
        if (value) {
            columnFilters.value = { ...columnFilters.value, [columnId]: value };
        } else {
            const { [columnId]: _, ...rest } = columnFilters.value;
            columnFilters.value = rest;
        }
        pagination.value.page = 1;
        fetchTemplates();
    }, 300);
};

const toggleMultiSelectFilter = (columnId: string, value: string) => {
    const current = columnFilters.value[columnId];
    const currentArray = Array.isArray(current) ? current : [];

    if (currentArray.includes(value)) {
        const newArray = currentArray.filter((v) => v !== value);
        if (newArray.length === 0) {
            const { [columnId]: _, ...rest } = columnFilters.value;
            columnFilters.value = rest;
        } else {
            columnFilters.value = {
                ...columnFilters.value,
                [columnId]: newArray,
            };
        }
    } else {
        columnFilters.value = {
            ...columnFilters.value,
            [columnId]: [...currentArray, value],
        };
    }
    pagination.value.page = 1;
    fetchTemplates();
};

const clearMultiSelectFilter = (columnId: string) => {
    const { [columnId]: _, ...rest } = columnFilters.value;
    columnFilters.value = rest;
    pagination.value.page = 1;
    fetchTemplates();
};

const isMultiSelectOptionSelected = (columnId: string, value: string) => {
    const current = columnFilters.value[columnId];
    return Array.isArray(current) && current.includes(value);
};

const getMultiSelectCount = (columnId: string) => {
    const current = columnFilters.value[columnId];
    return Array.isArray(current) ? current.length : 0;
};

const handleImport = async () => {
    if (selectedIds.value.length === 0) {
        toast.error('Please select at least one template to import');
        return;
    }

    importing.value = true;
    try {
        const result = await activityTemplateService.importActivityTemplates(
            props.assessmentId,
            selectedIds.value,
        );
        toast.success(
            result.message ||
                `Successfully imported ${selectedIds.value.length} activity template(s)`,
        );
        rowSelection.value = {};
        emit('success');
        emit('update:open', false);
    } catch (error) {
        // Error handled globally
    } finally {
        importing.value = false;
    }
};

// Watch for modal open
watch(
    () => props.open,
    async (isOpen) => {
        if (isOpen) {
            rowSelection.value = {};
            columnFilters.value = {};
            sortBy.value = null;
            sortOrder.value = null;
            pagination.value = { total: 0, page: 1, size: 50, pages: 1 };
            await fetchTemplates();
        }
    },
);
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[1400px] max-h-[70vh] flex flex-col">
      <DialogHeader>
        <DialogTitle>Import Activity Templates</DialogTitle>
        <DialogDescription>
          Select activity templates to import into this assessment.
          <span v-if="selectedCount > 0" class="font-medium text-primary ml-2">
            {{ selectedCount }} selected
          </span>
        </DialogDescription>
      </DialogHeader>

      <div class="flex-1 overflow-hidden flex flex-col gap-4 py-4">
        <!-- Table -->
        <div class="flex-1 overflow-y-auto min-h-0 rounded-md border">
          <div v-if="loading && templates.length === 0" class="flex items-center justify-center h-64">
            <Loader2 class="h-8 w-8 animate-spin text-muted-foreground" />
          </div>

          <Table v-else>
            <TableHeader>
              <TableRow v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
                <TableHead
                  v-for="header in headerGroup.headers"
                  :key="header.id"
                  :class="header.column.id === 'select' ? 'w-12' : ''"
                >
                  <div class="flex flex-col gap-2 pb-2">
                    <!-- Select All Checkbox -->
                    <template v-if="header.column.id === 'select'">
                      <Checkbox
                        :model-value="allRowsSelected || (someRowsSelected && 'indeterminate')"
                        @update:model-value="(value) => toggleAllRows(!!value)"
                        aria-label="Select all"
                      />
                    </template>
                    <!-- Regular Headers -->
                    <div
                      v-else-if="!header.isPlaceholder"
                      class="cursor-pointer select-none flex items-center gap-2"
                      @click="handleSortChange(header.column.id)"
                    >
                      {{ header.column.columnDef.header }}
                      <span class="text-xs">
                        {{ sortBy === header.column.id ? (sortOrder === 'asc' ? '↑' : '↓') : '↕' }}
                      </span>
                    </div>
                    <!-- Column Filter -->
                    <div v-if="header.column.getCanFilter() && !header.isPlaceholder">
                      <!-- Multiselect dropdown for priority -->
                      <DropdownMenu v-if="(header.column.columnDef.meta as { filterVariant?: string })?.filterVariant === 'multiselect'">
                        <DropdownMenuTrigger as-child>
                          <Button variant="ghost" size="sm" class="h-8 w-full justify-between px-2 text-xs font-normal border">
                            {{ getMultiSelectCount(header.column.id) > 0 ? `${getMultiSelectCount(header.column.id)} Selected` : 'All' }}
                            <ChevronDown class="h-3 w-3 opacity-50" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="start" class="w-[150px]">
                          <DropdownMenuLabel>Filter {{ header.column.columnDef.header }}</DropdownMenuLabel>
                          <DropdownMenuItem
                            v-for="option in ((header.column.columnDef.meta as { filterOptions?: string[] })?.filterOptions ?? [])"
                            :key="option"
                            @select.prevent="toggleMultiSelectFilter(header.column.id, option)"
                            class="cursor-pointer"
                          >
                            <Check :class="['mr-2 h-4 w-4', isMultiSelectOptionSelected(header.column.id, option) ? 'opacity-100' : 'opacity-0']" />
                            {{ option }}
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            v-if="getMultiSelectCount(header.column.id) > 0"
                            @select.prevent="clearMultiSelectFilter(header.column.id)"
                            class="cursor-pointer justify-center text-muted-foreground border-t mt-1"
                          >
                            Clear filters
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                      <!-- Text input filter (default) -->
                      <Input
                        v-else
                        class="h-8 text-xs w-full"
                        placeholder="Filter..."
                        :model-value="(columnFilters[header.column.id] as string) ?? ''"
                        @update:model-value="handleTextFilter(header.column.id, $event as string)"
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
                  :data-state="isSelected(row.id) ? 'selected' : undefined"
                  :class="[
                    'cursor-pointer hover:bg-muted/50',
                    isSelected(row.id) ? 'bg-muted/50' : ''
                  ]"
                  @click="toggleSelection(row.id)"
                >
                  <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                    <!-- Checkbox Cell -->
                    <template v-if="cell.column.id === 'select'">
                      <Checkbox
                        :model-value="isSelected(row.id)"
                        @update:model-value="(value) => toggleSelection(row.id, !!value)"
                        @click.stop
                        aria-label="Select row"
                      />
                    </template>
                    <!-- Regular Cells -->
                    <template v-else>
                      {{ cell.column.id === 'priority' ? (row.original.priority || '-') : row.original[cell.column.id as keyof ActivityTemplateRead] }}
                    </template>
                  </TableCell>
                </TableRow>
              </template>
              <template v-else>
                <TableRow>
                  <TableCell :colspan="columns.length" class="h-24 text-center">
                    {{ loading ? 'Loading...' : 'No templates found.' }}
                  </TableCell>
                </TableRow>
              </template>
            </TableBody>
          </Table>
        </div>

        <!-- Pagination -->
        <div class="flex-shrink-0">
          <Pagination
            v-if="pagination.pages > 0"
            :pagination="pagination"
            :page-size="pagination.size"
            @page-change="handlePageChange"
            @page-size-change="handlePageSizeChange"
          />
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="emit('update:open', false)" :disabled="importing">
          Cancel
        </Button>
        <Button @click="handleImport" :disabled="importing || selectedCount === 0">
          <Loader2 v-if="importing" class="mr-2 h-4 w-4 animate-spin" />
          {{ importing ? 'Importing...' : `Import ${selectedCount > 0 ? selectedCount : ''} Template${selectedCount !== 1 ? 's' : ''}` }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>