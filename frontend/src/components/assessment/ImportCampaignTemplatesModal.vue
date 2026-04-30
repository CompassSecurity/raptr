<script setup lang="ts">
import {
    type ColumnDef,
    getCoreRowModel,
    type RowSelectionState,
    useVueTable,
} from '@tanstack/vue-table';
import { Loader2 } from 'lucide-vue-next';
import { ref, watch } from 'vue';
import { toast } from 'vue-sonner';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
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
import { campaignTemplateService } from '@/services/campaignTemplateService';
import type { CampaignTemplateRead, PaginationState } from '@/types/utils';

const props = defineProps<{
    open: boolean;
    assessmentId: string;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

// Data state
const campaignTemplates = ref<CampaignTemplateRead[]>([]);
const loading = ref(false);
const importing = ref(false);
const pagination = ref<PaginationState>({
    total: 0,
    page: 1,
    size: 50,
    pages: 1,
});

// Single selection — only one campaign can be imported at a time
const selectedId = ref<string | null>(null);

// Table state
const sortBy = ref<string | null>(null);
const sortOrder = ref<'asc' | 'desc' | null>(null);

// Server-side column filters
const columnFilters = ref<Record<string, string>>({});

// Column definitions
const columns: ColumnDef<CampaignTemplateRead>[] = [
    {
        accessorKey: 'name',
        header: 'Name',
        enableColumnFilter: true,
        meta: { filterVariant: 'text' },
    },
    {
        accessorKey: 'description',
        header: 'Description',
        enableColumnFilter: false,
        cell: ({ row }) => row.original.description || '-',
    },
    {
        id: 'item_count',
        header: 'Items',
        enableColumnFilter: false,
        cell: ({ row }) => row.original.items.length,
    },
];

// Use rowSelection for TanStack table compatibility but restrict to single select
const rowSelection = ref<RowSelectionState>({});

const table = useVueTable({
    get data() {
        return campaignTemplates.value;
    },
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
    manualFiltering: true,
    enableRowSelection: true,
    enableMultiRowSelection: false,
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
const isSelected = (rowId: string) => selectedId.value === rowId;

// Selection handler — single select
const selectRow = (rowId: string) => {
    if (selectedId.value === rowId) {
        selectedId.value = null;
        rowSelection.value = {};
    } else {
        selectedId.value = rowId;
        rowSelection.value = { [rowId]: true };
    }
};

// Fetch campaign templates
async function fetchCampaignTemplates() {
    loading.value = true;
    try {
        const offset = (pagination.value.page - 1) * pagination.value.size;

        const params: Record<string, unknown> = {
            offset,
            limit: pagination.value.size,
            sort_by: sortBy.value || undefined,
            sort_order: sortOrder.value || undefined,
        };

        for (const [key, value] of Object.entries(columnFilters.value)) {
            if (value && value.length > 0) {
                params[key] = value;
            }
        }

        const data = await campaignTemplateService.getCampaignTemplates(params);
        campaignTemplates.value = data.items;
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
    fetchCampaignTemplates();
};

const handlePageSizeChange = (size: number) => {
    pagination.value.size = size;
    pagination.value.page = 1;
    fetchCampaignTemplates();
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
    fetchCampaignTemplates();
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
        fetchCampaignTemplates();
    }, 300);
};

const handleImport = async () => {
    if (!selectedId.value) {
        toast.error('Please select a campaign template to import');
        return;
    }

    importing.value = true;
    try {
        const result = await campaignTemplateService.importCampaignTemplate(
            props.assessmentId,
            selectedId.value,
        );
        toast.success(
            result.message || 'Campaign template imported successfully',
        );
        selectedId.value = null;
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
            selectedId.value = null;
            rowSelection.value = {};
            columnFilters.value = {};
            sortBy.value = null;
            sortOrder.value = null;
            pagination.value = { total: 0, page: 1, size: 50, pages: 1 };
            await fetchCampaignTemplates();
        }
    },
);
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[900px] max-h-[70vh] flex flex-col">
      <DialogHeader>
        <DialogTitle>Import Campaign Template</DialogTitle>
        <DialogDescription>
          Select a campaign template to import into this assessment. This will create all groups and activities defined in the campaign.
        </DialogDescription>
      </DialogHeader>

      <div class="flex-1 overflow-hidden flex flex-col gap-4 py-4">
        <!-- Table -->
        <div class="flex-1 overflow-y-auto min-h-0 rounded-md border">
          <div v-if="loading && campaignTemplates.length === 0" class="flex items-center justify-center h-64">
            <Loader2 class="h-8 w-8 animate-spin text-muted-foreground" />
          </div>

          <Table v-else>
            <TableHeader>
              <TableRow v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
                <TableHead
                  v-for="header in headerGroup.headers"
                  :key="header.id"
                >
                  <div class="flex flex-col gap-2 pb-2">
                    <!-- Regular Headers -->
                    <div
                      v-if="!header.isPlaceholder"
                      class="cursor-pointer select-none flex items-center gap-2"
                      @click="header.column.id !== 'item_count' ? handleSortChange(header.column.id) : undefined"
                    >
                      {{ header.column.columnDef.header }}
                      <span v-if="header.column.id !== 'item_count'" class="text-xs">
                        {{ sortBy === header.column.id ? (sortOrder === 'asc' ? '↑' : '↓') : '↕' }}
                      </span>
                    </div>
                    <!-- Column Filter -->
                    <div v-if="header.column.getCanFilter() && !header.isPlaceholder">
                      <Input
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
                    isSelected(row.id) ? 'bg-primary/10 border-primary' : ''
                  ]"
                  @click="selectRow(row.id)"
                >
                  <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                    <!-- Description Cell -->
                    <template v-if="cell.column.id === 'description'">
                      {{ row.original.description || '-' }}
                    </template>
                    <!-- Item Count Cell -->
                    <template v-else-if="cell.column.id === 'item_count'">
                      {{ row.original.items.length }}
                    </template>
                    <!-- Regular Cells -->
                    <template v-else>
                      {{ row.original[cell.column.id as keyof CampaignTemplateRead] }}
                    </template>
                  </TableCell>
                </TableRow>
              </template>
              <template v-else>
                <TableRow>
                  <TableCell :colspan="columns.length" class="h-24 text-center">
                    {{ loading ? 'Loading...' : 'No campaign templates found.' }}
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
        <Button @click="handleImport" :disabled="importing || !selectedId">
          <Loader2 v-if="importing" class="mr-2 h-4 w-4 animate-spin" />
          {{ importing ? 'Importing...' : 'Import Campaign' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
