<script setup lang="ts">
import {
    ArrowDown,
    ArrowUp,
    ArrowUpDown,
    Check,
    ChevronDown,
    ChevronRight,
    Copy,
    Eye,
    EyeOff,
    Folder,
    FolderInput,
    FolderOpen,
    MoreHorizontal,
    Pencil,
    Settings2,
    Trash2,
    Undo2,
} from 'lucide-vue-next';
import { storeToRefs } from 'pinia';
import { computed, ref, watch } from 'vue';
import DateTimeDisplay from '@/components/DateTimeDisplay.vue';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
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
import { tagService } from '@/services/tagService';
import { useAuthStore } from '@/stores/auth';
import { usePreferencesStore } from '@/stores/preferences';
import type {
    ActivityGroupRead,
    ActivityRead,
    ColumnFilterValue,
    PaginationState,
    TagRead,
} from '@/types/utils';
import { schemas } from '@/types/zod';

const authStore = useAuthStore();
const preferencesStore = usePreferencesStore();
const { columnVisibility, activityTableFilters: filters } =
    storeToRefs(preferencesStore);

const props = defineProps<{
    activities: ActivityRead[];
    groups: ActivityGroupRead[];
    pagination?: PaginationState;
    pageSize?: number;
    viewMode?: 'grouped' | 'flat';
    showDeleted?: boolean;
    assessmentId?: string;
}>();

const emit = defineEmits<{
    (e: 'page-change', page: number): void;
    (e: 'page-size-change', size: number): void;
    (
        e: 'sort-change',
        column: string | null,
        direction: 'asc' | 'desc' | null,
    ): void;
    (
        e: 'column-filter-change',
        columnId: string,
        value: ColumnFilterValue,
    ): void;
    (e: 'delete', activity: ActivityRead): void;
    (e: 'duplicate', activity: ActivityRead): void;
    (e: 'move-to-group', activity: ActivityRead): void;
    (e: 'toggle-visibility', activity: ActivityRead): void;
    (e: 'row-click', activity: ActivityRead): void;
    (e: 'group-edit', group: ActivityGroupRead): void;
    (e: 'group-delete', group: ActivityGroupRead): void;
    (e: 'group-toggle-visibility', group: ActivityGroupRead): void;
    (e: 'bulk-delete', activityIds: string[]): void;
    (e: 'bulk-move-to-group', activityIds: string[]): void;
    (e: 'bulk-toggle-visibility', activityIds: string[]): void;
}>();

// Multi-select state
const selectedIds = ref<Set<string>>(new Set());

const selectedCount = computed(() => selectedIds.value.size);

// Fetch tags for filtering
const availableTags = ref<TagRead[]>([]);
watch(
    () => props.assessmentId,
    async (newId) => {
        if (newId) {
            try {
                const resp = await tagService.getTags(newId, { limit: 1000 });
                availableTags.value = resp.items;
            } catch (e) {
                console.error(e);
            }
        }
    },
    { immediate: true },
);

const visibleActivityIds = computed(() => {
    if (props.viewMode === 'flat') {
        return flatViewActivities.value.map((a) => a.id);
    }
    // Grouped: all non-deleted activities
    const ids: string[] = [];
    for (const [, data] of groupedActivities.value) {
        data.activities.forEach((a) => {
            ids.push(a.id);
        });
    }
    return ids;
});

const allSelected = computed(() => {
    if (visibleActivityIds.value.length === 0) return false;
    return visibleActivityIds.value.every((id) => selectedIds.value.has(id));
});

const someSelected = computed(() => {
    if (visibleActivityIds.value.length === 0) return false;
    const count = visibleActivityIds.value.filter((id) =>
        selectedIds.value.has(id),
    ).length;
    return count > 0 && count < visibleActivityIds.value.length;
});

function toggleSelectAll(value: boolean | 'indeterminate') {
    if (value === true) {
        visibleActivityIds.value.forEach((id) => {
            selectedIds.value.add(id);
        });
        selectedIds.value = new Set(selectedIds.value);
    } else {
        selectedIds.value = new Set();
    }
}

function isGroupSelected(activities: ActivityRead[]) {
    if (activities.length === 0) return false;
    return activities.every((a) => selectedIds.value.has(a.id));
}

function isGroupIndeterminate(activities: ActivityRead[]) {
    if (activities.length === 0) return false;
    const selectedCount = activities.filter((a) =>
        selectedIds.value.has(a.id),
    ).length;
    return selectedCount > 0 && selectedCount < activities.length;
}

function toggleGroupSelect(activities: ActivityRead[], select: boolean) {
    if (select) {
        activities.forEach((a) => {
            selectedIds.value.add(a.id);
        });
    } else {
        activities.forEach((a) => {
            selectedIds.value.delete(a.id);
        });
    }
    selectedIds.value = new Set(selectedIds.value);
}

function toggleSelect(activityId: string) {
    if (selectedIds.value.has(activityId)) {
        selectedIds.value.delete(activityId);
    } else {
        selectedIds.value.add(activityId);
    }
    selectedIds.value = new Set(selectedIds.value);
}

// Clear selection when activities change
watch(
    () => props.activities,
    () => {
        selectedIds.value = new Set();
    },
);

// Create a map for quick group lookups
const groupsMap = computed(() => new Map(props.groups.map((g) => [g.id, g])));

// Track which groups are expanded (auto-expand all groups)
const expandedGroups = ref<Set<string>>(new Set());

// Auto-expand all groups when groups load
watch(
    () => props.groups,
    (groups) => {
        groups.forEach((g) => {
            expandedGroups.value.add(g.id);
        });
    },
    { immediate: true },
);

const toggleGroup = (groupId: string) => {
    if (expandedGroups.value.has(groupId)) {
        expandedGroups.value.delete(groupId);
    } else {
        expandedGroups.value.add(groupId);
    }
};

// Server-side filter state uses persisted store (mapped above)

// Debounce text filter changes
let filterTimeouts: Record<string, ReturnType<typeof setTimeout>> = {};

const handleTextFilter = (columnId: string, value: string) => {
    (filters.value as any)[columnId] = value;

    if (filterTimeouts[columnId]) {
        clearTimeout(filterTimeouts[columnId]);
    }
    filterTimeouts[columnId] = setTimeout(() => {
        emit('column-filter-change', columnId, value || '');
    }, 300);
};

const toggleFilter = (
    type: 'priority' | 'state' | 'tags' | 'visible',
    value: any,
) => {
    if (type === 'visible') {
        if (filters.value.visible === value) {
            filters.value.visible = null;
            emit('column-filter-change', type, '');
        } else {
            filters.value.visible = value;
            emit('column-filter-change', type, value);
        }
    } else {
        const target = filters.value[type] as string[];
        const index = target.indexOf(value);
        if (index === -1) {
            target.push(value);
        } else {
            target.splice(index, 1);
        }
        // Emit the updated filter array
        emit('column-filter-change', type, [
            ...(filters.value[type] as string[]),
        ]);
    }
};

const clearFilter = (type: 'priority' | 'state' | 'tags' | 'visible') => {
    if (type === 'visible') {
        filters.value.visible = null;
        emit('column-filter-change', type, '');
    } else {
        (filters.value as any)[type] = [];
        emit('column-filter-change', type, []);
    }
};

// Column visibility state (persisted via preferences store, except 'actions' which is permission-based)
const visibleColumns = computed(() => {
    const cols: Record<string, boolean> = { ...columnVisibility.value };
    cols.actions = authStore.hasAdminOrRedAccess(props.assessmentId);
    return cols;
});

const columnLabels: Record<string, string> = {
    name: 'Activity Name',
    activity_group: 'Activity Group',
    mitre_tactic: 'MITRE Tactic',
    mitre_technique: 'MITRE Technique',
    priority: 'Priority',
    state: 'State',
    start_time: 'Start Time',
    end_time: 'End Time',
    tags: 'Tags',
    created_at: 'Created At',
    updated_at: 'Updated At',
    activity_coverage_score: 'Coverage Score',
    visible: 'Visible',
    actions: 'Actions',
};

const selectableColumns = computed(() => {
    const columns = { ...columnLabels };
    if (!authStore.hasAdminOrRedAccess(props.assessmentId)) {
        delete columns.actions;
    }
    return columns;
});

const toggleColumn = (key: string) => {
    columnVisibility.value[key] = !columnVisibility.value[key];
};

// Filter options
const priorityOptions = schemas.ActivityPriority.options;
const stateOptions = schemas.ActivityState.options;

// Sort state
const sortColumn = ref<string>('');
const sortDirection = ref<'asc' | 'desc'>('asc');

const handleSort = (column: string) => {
    if (sortColumn.value === column) {
        if (sortDirection.value === 'asc') {
            sortDirection.value = 'desc';
            emit('sort-change', column, 'desc');
        } else {
            sortColumn.value = ''; // Reset sort
            sortDirection.value = 'asc';
            emit('sort-change', null, null);
        }
    } else {
        sortColumn.value = column;
        sortDirection.value = 'asc';
        emit('sort-change', column, 'asc');
    }
};

// Check if any filters are active
const isFiltered = computed(() => {
    return (
        filters.value.name !== '' ||
        filters.value.mitre_tactic !== '' ||
        filters.value.mitre_technique !== '' ||
        filters.value.priority.length > 0 ||
        filters.value.state.length > 0 ||
        filters.value.tags.length > 0 ||
        filters.value.visible !== null
    );
});

// Group activities by group_id (filtering and sorting is now server-side)
const groupedActivities = computed(() => {
    const groups: Map<
        string,
        { group: ActivityGroupRead | null; activities: ActivityRead[] }
    > = new Map();

    // First, initialize all groups (including empty ones), filtering out deleted groups if needed
    const visibleGroups = props.showDeleted
        ? props.groups
        : props.groups.filter((group) => !group.deleted);

    visibleGroups.forEach((group) => {
        groups.set(group.id, {
            group: group,
            activities: [],
        });
    });

    // Filter activities by showDeleted locally (the rest is server-side)
    const visibleActivities = props.showDeleted
        ? props.activities
        : props.activities.filter((activity) => !activity.deleted);

    // Add activities to their groups
    visibleActivities.forEach((activity) => {
        const groupId = activity.activity_group_id;
        if (!groupId) return;
        if (!groups.has(groupId)) {
            groups.set(groupId, {
                group: groupsMap.value.get(groupId) || null,
                activities: [],
            });
        }
        groups.get(groupId)!.activities.push(activity);
    });

    // If filters are active, remove groups with no activities
    if (isFiltered.value) {
        for (const [groupId, data] of groups) {
            if (data.activities.length === 0) {
                groups.delete(groupId);
            }
        }
    }

    return groups;
});

// Filter activities for flat view
const flatViewActivities = computed(() => {
    if (props.showDeleted) {
        return props.activities;
    }
    return props.activities.filter((activity) => !activity.deleted);
});

// Total column count (for colspan on group headers & empty state)
const totalColumns = computed(() => {
    let count = Object.values(visibleColumns.value).filter(Boolean).length;
    if (authStore.hasAdminOrRedAccess(props.assessmentId)) count += 1; // checkbox column
    return count;
});

// Helper functions for badge variants
const getPriorityVariant = (priority: string | null | undefined) => {
    if (!priority) return 'outline';
    switch (priority) {
        case 'Critical':
            return 'destructive';
        case 'High':
            return 'default';
        case 'Medium':
            return 'secondary';
        case 'Low':
            return 'outline';
        default:
            return 'outline';
    }
};

const stateColors: Record<string, string> = {
    Pending: '#737373', // muted gray
    'Waiting Red': '#ef4444', // red-500
    'Waiting Blue': '#3b82f6', // blue-500
    Ready: '#14b8a6', // teal-500
    'In Progress': '#f97316', // orange-500
    'In Evaluation': '#a855f7', // purple-500
    Completed: '#16a34a', // green-600
    Cancelled: '#eab308', // yellow-500
};

const getStateColor = (state: string | null | undefined) => {
    if (!state) return '#737373';
    return stateColors[state] || '#737373';
};
</script>

<template>
  <div class="space-y-4">
    <!-- Toolbar -->
    <div class="flex items-center justify-between">
      <!-- Bulk Actions (shown when items selected) -->
      <div v-if="selectedCount > 0" class="flex items-center gap-2">
        <span class="text-sm text-muted-foreground">{{ selectedCount }} selected</span>
        <Button variant="outline" size="sm" class="h-8" @click="emit('bulk-move-to-group', [...selectedIds])">
          <FolderInput class="mr-2 h-4 w-4" />
          Move to Group
        </Button>
        <Button variant="outline" size="sm" class="h-8" @click="emit('bulk-toggle-visibility', [...selectedIds])">
          <Eye class="mr-2 h-4 w-4" />
          Toggle Visibility
        </Button>
        <Button variant="outline" size="sm" class="h-8 text-destructive hover:text-destructive" @click="emit('bulk-delete', [...selectedIds])">
          <Trash2 class="mr-2 h-4 w-4" />
          Delete
        </Button>
        <Button variant="ghost" size="sm" class="h-8" @click="selectedIds = new Set()">
          Clear
        </Button>
      </div>
      <div v-else />

      <!-- Column visibility -->
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button variant="outline" size="sm" class="ml-auto h-8 lg:flex">
            <Settings2 class="mr-2 h-4 w-4" />
            Columns
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" class="w-[200px]">
          <DropdownMenuLabel>Toggle columns</DropdownMenuLabel>
          <DropdownMenuItem
            v-for="(label, key) in selectableColumns"
            :key="key"
            @click.prevent="toggleColumn(key)"
            class="cursor-pointer"
          >
            <Check
              :class="[
                'mr-2 h-4 w-4',
                visibleColumns[key] ? 'opacity-100' : 'opacity-0'
              ]"
            />
            {{ label }}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>

    <!-- Table -->
    <div class="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead v-if="authStore.hasAdminOrRedAccess(props.assessmentId)" class="w-12 p-0">
              <div 
                class="w-full h-full min-h-[2.5rem] flex items-center justify-center cursor-pointer hover:bg-muted/50"
                @click.stop="toggleSelectAll(allSelected ? false : true)"
              >
                <Checkbox
                  :model-value="allSelected || (someSelected && 'indeterminate')"
                  class="pointer-events-none"
                  aria-label="Select all"
                />
              </div>
            </TableHead>
            <TableHead class="min-w-[200px] w-auto" v-if="visibleColumns.name">
              <div class="flex flex-col gap-2 pt-2 pb-2">
                <div 
                  class="flex items-center gap-2 cursor-pointer select-none hover:text-foreground"
                  @click="handleSort('name')"
                >
                  <span>Activity Name</span>
                  <component 
                    :is="sortColumn === 'name' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown" 
                    class="h-3 w-3"
                  />
                </div>
                <Input :model-value="filters.name" @update:model-value="handleTextFilter('name', $event as string)" class="h-8 text-xs font-normal" placeholder="Filter..." @click.stop />
              </div>
            </TableHead>
            <TableHead v-if="visibleColumns.activity_group">
              <div class="flex flex-col gap-2 pt-2 pb-2">
                <div 
                  class="flex items-center gap-2 cursor-pointer select-none hover:text-foreground"
                  @click="handleSort('activity_group.name')"
                >
                  <span>Activity Group</span>
                  <component 
                    :is="sortColumn === 'activity_group.name' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown" 
                    class="h-3 w-3"
                  />
                </div>
              </div>
            </TableHead>
            <TableHead v-if="visibleColumns.mitre_tactic">
              <div class="flex flex-col gap-2 pt-2 pb-2">
                <div 
                  class="flex items-center gap-2 cursor-pointer select-none hover:text-foreground"
                  @click="handleSort('mitre_tactic')"
                >
                  <span>MITRE Tactic</span>
                  <component 
                    :is="sortColumn === 'mitre_tactic' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown" 
                    class="h-3 w-3"
                  />
                </div>
                <Input :model-value="filters.mitre_tactic" @update:model-value="handleTextFilter('mitre_tactic', $event as string)" class="h-8 text-xs font-normal" placeholder="Filter..." @click.stop />
              </div>
            </TableHead>
            <TableHead v-if="visibleColumns.mitre_technique">
              <div class="flex flex-col gap-2 pt-2 pb-2">
                <div 
                  class="flex items-center gap-2 cursor-pointer select-none hover:text-foreground"
                  @click="handleSort('mitre_technique')"
                >
                  <span>MITRE Technique</span>
                  <component 
                    :is="sortColumn === 'mitre_technique' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown" 
                    class="h-3 w-3"
                  />
                </div>
                 <Input :model-value="filters.mitre_technique" @update:model-value="handleTextFilter('mitre_technique', $event as string)" class="h-8 text-xs font-normal" placeholder="Filter..." @click.stop />
              </div>
            </TableHead>
            <TableHead v-if="visibleColumns.priority">
              <div class="flex flex-col gap-2 pt-2 pb-2">
                <div
                  class="flex items-center gap-2 cursor-pointer select-none hover:text-foreground"
                  @click="handleSort('priority')"
                >
                  <span>Priority</span>
                  <component
                    :is="sortColumn === 'priority' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown"
                    class="h-3 w-3"
                  />
                </div>
                <div @click.stop="">
                   <DropdownMenu>
                    <DropdownMenuTrigger as-child>
                      <Button variant="ghost" size="sm" class="h-8 w-full justify-between px-2 text-xs font-normal border">
                        {{ filters.priority.length > 0 ? `${filters.priority.length} Selected` : 'All' }}
                        <ChevronDown class="h-3 w-3 opacity-50" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start" class="w-[150px]">
                      <DropdownMenuLabel>Filter Priority</DropdownMenuLabel>
                      <DropdownMenuItem
                        v-for="option in priorityOptions"
                        :key="option"
                        @select.prevent="toggleFilter('priority', option)"
                        class="cursor-pointer"
                      >
                         <Check
                          :class="[
                            'mr-2 h-4 w-4',
                            filters.priority.includes(option) ? 'opacity-100' : 'opacity-0'
                          ]"
                        />
                        {{ option }}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                         v-if="filters.priority.length > 0"
                         @select.prevent="clearFilter('priority')"
                         class="cursor-pointer justify-center text-muted-foreground border-t mt-1"
                      >
                        Clear filters
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </TableHead>
            <TableHead v-if="visibleColumns.state">
              <div class="flex flex-col gap-2 pt-2 pb-2">
                <div
                  class="flex items-center gap-2 cursor-pointer select-none hover:text-foreground"
                  @click="handleSort('state')"
                >
                  <span>State</span>
                  <component
                    :is="sortColumn === 'state' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown"
                    class="h-3 w-3"
                  />
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger as-child>
                    <Button variant="ghost" size="sm" class="h-8 w-full justify-between px-2 text-xs font-normal border">
                      {{ filters.state.length > 0 ? `${filters.state.length} Selected` : 'All' }}
                      <ChevronDown class="h-3 w-3 opacity-50" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" class="w-[150px]">
                    <DropdownMenuLabel>Filter State</DropdownMenuLabel>
                    <DropdownMenuItem
                      v-for="option in stateOptions"
                      :key="option"
                      @select.prevent="toggleFilter('state', option)"
                      class="cursor-pointer"
                    >
                       <Check
                        :class="[
                          'mr-2 h-4 w-4',
                          filters.state.includes(option) ? 'opacity-100' : 'opacity-0'
                        ]"
                      />
                      {{ option }}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                       v-if="filters.state.length > 0"
                       @select.prevent="clearFilter('state')"
                       class="cursor-pointer justify-center text-muted-foreground border-t mt-1"
                    >
                      Clear filters
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </TableHead>
            <TableHead v-if="visibleColumns.start_time">
              <div
                class="flex items-center gap-2 cursor-pointer select-none pb-2 hover:text-foreground"
                @click="handleSort('activity_start_time')"
              >
                <span>Start Time</span>
                <component
                  :is="sortColumn === 'activity_start_time' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown"
                  class="h-3 w-3"
                />
              </div>
            </TableHead>
            <TableHead v-if="visibleColumns.end_time">
              <div
                class="flex items-center gap-2 cursor-pointer select-none pb-2 hover:text-foreground"
                @click="handleSort('activity_end_time')"
              >
                <span>End Time</span>
                <component
                  :is="sortColumn === 'activity_end_time' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown"
                  class="h-3 w-3"
                />
              </div>
            </TableHead>
            <TableHead v-if="visibleColumns.tags">
              <div class="flex flex-col gap-2 pt-2 pb-2">
                <div 
                  class="flex items-center gap-2 cursor-pointer select-none hover:text-foreground"
                  @click="handleSort('tags')"
                >
                  <span>Tags</span>
                  <component 
                    :is="sortColumn === 'tags' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown" 
                    class="h-3 w-3"
                  />
                </div>
                <div @click.stop="">
                  <DropdownMenu>
                    <DropdownMenuTrigger as-child>
                      <Button variant="ghost" size="sm" class="h-8 w-full justify-between px-2 text-xs font-normal border">
                        {{ filters.tags.length > 0 ? `${filters.tags.length} Selected` : 'All' }}
                        <ChevronDown class="h-3 w-3 opacity-50" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start" class="w-[200px]">
                      <DropdownMenuLabel>Filter Tags</DropdownMenuLabel>
                      <DropdownMenuItem
                        v-for="tag in availableTags"
                        :key="tag.id"
                        @select.prevent="toggleFilter('tags', tag.id)"
                        class="cursor-pointer"
                      >
                        <Check
                          :class="[
                            'mr-2 h-4 w-4',
                            filters.tags.includes(tag.id) ? 'opacity-100' : 'opacity-0'
                          ]"
                        />
                        <div class="flex items-center gap-2">
                          <div class="w-2 h-2 rounded-full" :style="{ backgroundColor: tag.color }"></div>
                          {{ tag.name }}
                        </div>
                      </DropdownMenuItem>
                      <DropdownMenuItem
                         v-if="filters.tags.length > 0"
                         @select.prevent="clearFilter('tags')"
                         class="cursor-pointer justify-center text-muted-foreground border-t mt-1"
                      >
                        Clear filters
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </TableHead>
            <TableHead v-if="visibleColumns.created_at">
              <div
                class="flex items-center gap-2 cursor-pointer select-none hover:text-foreground"
                @click="handleSort('created_at')"
              >
                <span>Created At</span>
                <component
                  :is="sortColumn === 'created_at' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown"
                  class="h-3 w-3"
                />
              </div>
            </TableHead>
            <TableHead v-if="visibleColumns.updated_at">
              <div
                class="flex items-center gap-2 cursor-pointer select-none hover:text-foreground"
                @click="handleSort('updated_at')"
              >
                <span>Updated At</span>
                <component
                  :is="sortColumn === 'updated_at' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown"
                  class="h-3 w-3"
                />
              </div>
            </TableHead>
            <TableHead v-if="visibleColumns.activity_coverage_score">
              <div class="flex flex-col gap-2 pt-2 pb-2">
                <div 
                  class="flex items-center gap-2 cursor-pointer select-none hover:text-foreground"
                  @click="handleSort('activity_coverage_score')"
                >
                  <span>Coverage Score</span>
                  <component 
                    :is="sortColumn === 'activity_coverage_score' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown" 
                    class="h-3 w-3"
                  />
                </div>
              </div>
            </TableHead>
            <TableHead class="w-[100px]" v-if="visibleColumns.visible">
              <div class="flex flex-col gap-2 pt-2 pb-2">
                <div
                  class="flex items-center justify-center gap-2 cursor-pointer select-none hover:text-foreground"
                  @click="handleSort('visible')"
                >
                  <span>Visible</span>
                  <component
                    :is="sortColumn === 'visible' ? (sortDirection === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown"
                    class="h-3 w-3"
                  />
                </div>
                <div @click.stop="">
                  <DropdownMenu>
                    <DropdownMenuTrigger as-child>
                      <Button variant="ghost" size="sm" class="h-8 w-full justify-between px-2 text-xs font-normal border">
                        {{ filters.visible === true ? 'Visible' : (filters.visible === false ? 'Hidden' : 'All') }}
                        <ChevronDown class="h-3 w-3 opacity-50" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" class="w-[150px]">
                      <DropdownMenuLabel>Filter Visibility</DropdownMenuLabel>
                      <DropdownMenuItem
                        @select.prevent="toggleFilter('visible', true)"
                        class="cursor-pointer"
                      >
                        <Check
                          :class="[
                            'mr-2 h-4 w-4',
                            filters.visible === true ? 'opacity-100' : 'opacity-0'
                          ]"
                        />
                        Visible
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        @select.prevent="toggleFilter('visible', false)"
                        class="cursor-pointer"
                      >
                        <Check
                          :class="[
                            'mr-2 h-4 w-4',
                            filters.visible === false ? 'opacity-100' : 'opacity-0'
                          ]"
                        />
                        Hidden
                      </DropdownMenuItem>
                      <DropdownMenuItem
                         v-if="filters.visible !== null"
                         @select.prevent="clearFilter('visible')"
                         class="cursor-pointer justify-center text-muted-foreground border-t mt-1"
                      >
                        Clear filters
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </TableHead>
            <TableHead class="w-[80px]" v-if="visibleColumns.actions">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <!-- Grouped View -->
          <template v-if="viewMode === 'grouped'">
            <template v-for="[groupId, groupData] in groupedActivities" :key="groupId">
              <!-- Group Header Row -->
              <TableRow
                :class="[
                  'bg-muted/50 hover:bg-muted font-medium',
                  { 'opacity-50': groupData.group?.deleted }
                ]"
              >
                <TableCell :colspan="totalColumns" class="p-0">
                  <div class="flex items-stretch min-h-[2.5rem]">
                    <div 
                      v-if="groupData.activities.length > 0 && authStore.hasAdminOrRedAccess(props.assessmentId)"
                      class="flex w-12 shrink-0 items-center justify-center cursor-pointer hover:bg-muted transition-colors border-r border-transparent hover:border-border/50"
                      @click.stop="toggleGroupSelect(groupData.activities, !isGroupSelected(groupData.activities))"
                    >
                      <Checkbox
                        :model-value="isGroupSelected(groupData.activities) ? true : (isGroupIndeterminate(groupData.activities) ? 'indeterminate' : false)"
                        class="pointer-events-none"
                        aria-label="Select group"
                      />
                    </div>
                    
                    <div class="flex flex-1 items-center gap-2 px-2 py-2 cursor-pointer" @click="toggleGroup(groupId)">
                      <ChevronRight v-if="!expandedGroups.has(groupId)" class="h-4 w-4" />
                    <ChevronDown v-else class="h-4 w-4" />
                    <Folder v-if="!expandedGroups.has(groupId)" class="h-4 w-4 text-muted-foreground" />
                    <FolderOpen v-else class="h-4 w-4 text-muted-foreground" />
                    <span :class="{ 'line-through text-muted-foreground': groupData.group?.deleted }">
                      {{ groupData.group?.name ?? 'Ungrouped' }}
                    </span>
                    <Badge v-if="groupData.group?.deleted" variant="destructive" class="text-xs">Deleted</Badge>

                    <!-- Group actions (pushed to the right) -->
                    <div v-if="groupData.group && authStore.hasAdminOrRedAccess(props.assessmentId)" class="ml-auto flex items-center gap-1" @click.stop>
                      <button
                        v-if="!groupData.group.deleted && groupData.group.id !== 'ungrouped'"
                        @click.stop="emit('group-toggle-visibility', groupData.group!)"
                        class="hover:bg-muted-foreground/10 rounded p-1 transition-colors"
                        :title="groupData.group.visible ? 'Hide group' : 'Show group'"
                      >
                        <Eye v-if="groupData.group.visible" class="h-4 w-4 text-muted-foreground" />
                        <EyeOff v-else class="h-4 w-4 text-muted-foreground" />
                      </button>
                      <DropdownMenu v-if="groupData.group.id !== 'ungrouped'">
                        <DropdownMenuTrigger as-child>
                          <Button variant="ghost" class="h-8 w-8 p-0" @click.stop>
                            <span class="sr-only">Open group menu</span>
                            <MoreHorizontal class="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Group Actions</DropdownMenuLabel>
                          <template v-if="groupData.group.deleted">
                            <DropdownMenuItem @click="emit('group-delete', groupData.group!)">
                              <Undo2 class="mr-2 h-4 w-4" />
                              Restore
                            </DropdownMenuItem>
                          </template>
                          <template v-else>
                            <DropdownMenuItem @click="emit('group-edit', groupData.group!)">
                              <Pencil class="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem v-if="!groupData.group.is_default" class="text-destructive" @click="emit('group-delete', groupData.group!)">
                              <Trash2 class="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </template>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                   </div>
                  </div>
                </TableCell>
              </TableRow>

              <!-- Activity Rows (only shown when group is expanded) -->
              <template v-if="expandedGroups.has(groupId)">
                <TableRow
                  v-for="activity in groupData.activities"
                  :key="activity.id"
                  :class="[
                    'hover:bg-muted/50 cursor-pointer',
                    { 'opacity-50': activity.deleted },
                    selectedIds.has(activity.id) ? 'bg-muted/50' : ''
                  ]"
                  @click="emit('row-click', activity)"
                >
                  <TableCell 
                    v-if="authStore.hasAdminOrRedAccess(props.assessmentId)"
                    @click.stop="toggleSelect(activity.id)"
                  >
                    <Checkbox
                      :model-value="selectedIds.has(activity.id)"
                      class="pointer-events-none"
                      aria-label="Select row"
                    />
                  </TableCell>

                  <TableCell v-if="visibleColumns.name">
                    <div class="flex items-center gap-2 pl-8">
                      <span
                        :class="[
                          'font-medium break-words whitespace-normal',
                          { 'line-through text-muted-foreground': activity.deleted }
                        ]"
                      >
                        {{ activity.name }}
                      </span>
                      <Badge v-if="activity.deleted" variant="destructive" class="text-xs">Deleted</Badge>
                    </div>
                  </TableCell>
                  <TableCell v-if="visibleColumns.activity_group">
                    <div 
                      :class="[
                        'flex items-center gap-1.5 text-sm w-full',
                        (activity.activity_group_id && !groupsMap.get(activity.activity_group_id)?.visible) ? 'text-muted-foreground' : ''
                      ]"
                    >
                      <span class="truncate">{{ groupsMap.get(activity.activity_group_id!)?.name ?? 'Ungrouped' }}</span>
                      <EyeOff
                        v-if="activity.activity_group_id && !groupsMap.get(activity.activity_group_id)?.visible"
                        class="h-3.5 w-3.5 text-muted-foreground/70 shrink-0 flex-none"
                        title="Group is hidden"
                      />
                    </div>
                  </TableCell>
                  <TableCell v-if="visibleColumns.mitre_tactic">
                    <div class="text-sm">{{ activity.mitre_tactic }}</div>
                  </TableCell>
                  <TableCell v-if="visibleColumns.mitre_technique">
                    <div class="text-sm">{{ activity.mitre_technique }}</div>
                  </TableCell>
                  <TableCell v-if="visibleColumns.priority">
                    <Badge :variant="getPriorityVariant(activity.priority)">
                      {{ activity.priority }}
                    </Badge>
                  </TableCell>
                  <TableCell v-if="visibleColumns.state">
                    <Badge variant="outline" :style="{ borderColor: getStateColor(activity.state), color: getStateColor(activity.state) }">
                      {{ activity.state }}
                    </Badge>
                  </TableCell>
                  <TableCell v-if="visibleColumns.start_time">
                    <DateTimeDisplay v-if="activity.activity_start_time" :date="activity.activity_start_time" />
                    <span v-else class="text-muted-foreground">-</span>
                  </TableCell>
                  <TableCell v-if="visibleColumns.end_time">
                    <DateTimeDisplay v-if="activity.activity_end_time" :date="activity.activity_end_time" />
                    <span v-else class="text-muted-foreground">-</span>
                  </TableCell>
                  <TableCell v-if="visibleColumns.tags">
                    <div class="flex flex-wrap gap-1">
                      <Badge v-for="tag in activity.tags" :key="tag.id" variant="outline" :style="{ borderColor: tag.color, color: tag.color }">
                        {{ tag.name }}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell v-if="visibleColumns.created_at">
                    <DateTimeDisplay v-if="activity.created_at" :date="activity.created_at" />
                    <span v-else class="text-muted-foreground">-</span>
                  </TableCell>
                  <TableCell v-if="visibleColumns.updated_at">
                    <DateTimeDisplay v-if="activity.updated_at" :date="activity.updated_at" />
                    <span v-else class="text-muted-foreground">-</span>
                  </TableCell>
                  <TableCell v-if="visibleColumns.activity_coverage_score">
                    <span :class="{
                      'text-green-600': (activity.evaluation?.activity_coverage_score ?? 0) === 100,
                      'text-yellow-500': (activity.evaluation?.activity_coverage_score ?? 0) >= 25 && (activity.evaluation?.activity_coverage_score ?? 0) < 100,
                      'text-red-500': (activity.evaluation?.activity_coverage_score ?? 0) < 25,
                    }">{{ activity.evaluation?.activity_coverage_score ?? 0 }}%</span>
                  </TableCell>
                  <TableCell v-if="visibleColumns.visible">
                    <div class="flex items-center justify-center">
                      <button
                        v-if="authStore.hasAdminOrRedAccess(props.assessmentId)"
                        @click.stop="emit('toggle-visibility', activity)"
                        class="hover:bg-muted rounded p-1 transition-colors"
                        :title="activity.visible ? 'Hide activity' : 'Show activity'"
                      >
                        <Eye v-if="activity.visible" class="h-4 w-4 text-muted-foreground" />
                        <EyeOff v-else class="h-4 w-4 text-muted-foreground" />
                      </button>
                      <template v-else>
                        <Eye v-if="activity.visible" class="h-4 w-4 text-muted-foreground" />
                        <EyeOff v-else class="h-4 w-4 text-muted-foreground" />
                      </template>
                    </div>
                  </TableCell>
                  <TableCell class="text-right" v-if="visibleColumns.actions">
                    <DropdownMenu>
                      <DropdownMenuTrigger as-child>
                        <Button variant="ghost" class="h-8 w-8 p-0" @click.stop>
                          <span class="sr-only">Open menu</span>
                          <MoreHorizontal class="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <template v-if="authStore.hasAdminOrRedAccess(props.assessmentId)">
                          <template v-if="activity.deleted">
                            <DropdownMenuItem @click="emit('delete', activity)">
                              <Undo2 class="mr-2 h-4 w-4" />
                              Restore
                            </DropdownMenuItem>
                          </template>
                          <template v-else>

                            <DropdownMenuItem @click="emit('duplicate', activity)">
                              <Copy class="mr-2 h-4 w-4" />
                              Clone
                            </DropdownMenuItem>
                            <DropdownMenuItem @click="emit('move-to-group', activity)">
                              <FolderInput class="mr-2 h-4 w-4" />
                              Move to Group
                            </DropdownMenuItem>
                            <DropdownMenuItem class="text-destructive" @click="emit('delete', activity)">
                              <Trash2 class="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </template>
                        </template>

                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              </template>
            </template>
          </template>

          <!-- Flat View -->
          <template v-else>
            <TableRow
              v-for="activity in flatViewActivities"
              :key="activity.id"
              :class="[
                'hover:bg-muted/50 cursor-pointer',
                { 'opacity-50': activity.deleted },
                selectedIds.has(activity.id) ? 'bg-muted/50' : ''
              ]"
              @click="emit('row-click', activity)"
            >
              <TableCell 
                v-if="authStore.hasAdminOrRedAccess(props.assessmentId)"
                @click.stop="toggleSelect(activity.id)"
              >
                <Checkbox
                  :model-value="selectedIds.has(activity.id)"
                  class="pointer-events-none"
                  aria-label="Select row"
                />
              </TableCell>
              <TableCell v-if="visibleColumns.name">
                <div class="flex items-center gap-2">
                  <span
                    :class="[
                      'font-medium break-words whitespace-normal',
                      { 'line-through text-muted-foreground': activity.deleted }
                    ]"
                  >
                    {{ activity.name }}
                  </span>
                  <Badge v-if="activity.deleted" variant="destructive" class="text-xs">Deleted</Badge>
                </div>
              </TableCell>
              <TableCell v-if="visibleColumns.activity_group">
                <div
                  :class="[
                    'flex items-center gap-1.5 text-sm w-full',
                    (activity.activity_group_id && !groupsMap.get(activity.activity_group_id)?.visible) ? 'text-muted-foreground' : ''
                  ]"
                >
                  <span class="truncate">{{ groupsMap.get(activity.activity_group_id ?? '')?.name ?? 'Ungrouped' }}</span>
                  <EyeOff
                    v-if="activity.activity_group_id && !groupsMap.get(activity.activity_group_id)?.visible"
                    class="h-3.5 w-3.5 text-muted-foreground/70 shrink-0 flex-none"
                    title="Group is hidden"
                  />
                </div>
              </TableCell>
              <TableCell v-if="visibleColumns.mitre_tactic">
                <div class="text-sm">{{ activity.mitre_tactic }}</div>
              </TableCell>
              <TableCell v-if="visibleColumns.mitre_technique">
                <div class="text-sm">{{ activity.mitre_technique }}</div>
              </TableCell>
              <TableCell v-if="visibleColumns.priority">
                <Badge :variant="getPriorityVariant(activity.priority)">
                  {{ activity.priority }}
                </Badge>
              </TableCell>
              <TableCell v-if="visibleColumns.state">
                <Badge variant="outline" :style="{ borderColor: getStateColor(activity.state), color: getStateColor(activity.state) }">
                  {{ activity.state }}
                </Badge>
              </TableCell>
              <TableCell v-if="visibleColumns.start_time">
                <DateTimeDisplay v-if="activity.activity_start_time" :date="activity.activity_start_time" />
                <span v-else class="text-muted-foreground">-</span>
              </TableCell>
              <TableCell v-if="visibleColumns.end_time">
                <DateTimeDisplay v-if="activity.activity_end_time" :date="activity.activity_end_time" />
                <span v-else class="text-muted-foreground">-</span>
              </TableCell>
              <TableCell v-if="visibleColumns.tags">
                <div class="flex flex-wrap gap-1">
                  <Badge v-for="tag in activity.tags" :key="tag.id" variant="outline" :style="{ borderColor: tag.color, color: tag.color }">
                    {{ tag.name }}
                  </Badge>
                </div>
              </TableCell>
              <TableCell v-if="visibleColumns.created_at">
                <DateTimeDisplay v-if="activity.created_at" :date="activity.created_at" />
                <span v-else class="text-muted-foreground">-</span>
              </TableCell>
              <TableCell v-if="visibleColumns.updated_at">
                <DateTimeDisplay v-if="activity.updated_at" :date="activity.updated_at" />
                <span v-else class="text-muted-foreground">-</span>
              </TableCell>
              <TableCell v-if="visibleColumns.activity_coverage_score">
                <span :class="{
                  'text-green-600': (activity.evaluation?.activity_coverage_score ?? 0) === 100,
                  'text-yellow-500': (activity.evaluation?.activity_coverage_score ?? 0) >= 25 && (activity.evaluation?.activity_coverage_score ?? 0) < 100,
                  'text-red-500': (activity.evaluation?.activity_coverage_score ?? 0) < 25,
                }">{{ activity.evaluation?.activity_coverage_score ?? 0 }}%</span>
              </TableCell>
              <TableCell v-if="visibleColumns.visible">
                <div class="flex items-center justify-center">
                  <button
                    v-if="authStore.hasAdminOrRedAccess(props.assessmentId)"
                    @click.stop="emit('toggle-visibility', activity)"
                    class="hover:bg-muted rounded p-1 transition-colors"
                    :title="activity.visible ? 'Hide activity' : 'Show activity'"
                  >
                    <Eye v-if="activity.visible" class="h-4 w-4 text-muted-foreground" />
                    <EyeOff v-else class="h-4 w-4 text-muted-foreground" />
                  </button>
                  <template v-else>
                    <Eye v-if="activity.visible" class="h-4 w-4 text-muted-foreground" />
                    <EyeOff v-else class="h-4 w-4 text-muted-foreground" />
                  </template>
                </div>
              </TableCell>
              <TableCell class="text-right" v-if="visibleColumns.actions">
                <DropdownMenu>
                  <DropdownMenuTrigger as-child>
                    <Button variant="ghost" class="h-8 w-8 p-0" @click.stop>
                      <span class="sr-only">Open menu</span>
                      <MoreHorizontal class="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                    <template v-if="authStore.hasAdminOrRedAccess(props.assessmentId)">
                      <template v-if="activity.deleted">
                        <DropdownMenuItem @click="emit('delete', activity)">
                          <Undo2 class="mr-2 h-4 w-4" />
                          Restore
                        </DropdownMenuItem>
                      </template>
                      <template v-else>

                        <DropdownMenuItem @click="emit('duplicate', activity)">
                          <Copy class="mr-2 h-4 w-4" />
                          Duplicate
                        </DropdownMenuItem>
                        <DropdownMenuItem @click="emit('move-to-group', activity)">
                          <FolderInput class="mr-2 h-4 w-4" />
                          Move to Group
                        </DropdownMenuItem>
                        <DropdownMenuItem class="text-destructive" @click="emit('delete', activity)">
                          <Trash2 class="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </template>
                    </template>

                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          </template>

          <!-- Empty State -->
          <TableRow v-if="activities.length === 0">
            <TableCell :colspan="totalColumns" class="h-24 text-center">
              No activities found.
            </TableCell>
          </TableRow>
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
