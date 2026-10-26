<script setup lang="ts">
import {
    ArrowDownAZ,
    ArrowUpAZ,
    CheckCircle2,
    ChevronDown,
    ChevronLeft,
    ChevronRight,
    Circle,
    CircleQuestionMark,
    EyeOff,
    Folder,
    FolderOpen,
    Folders,
    GripVertical,
    List,
    PlayCircle,
    Search,
    XCircle,
} from '@lucide/vue';
import { computed, ref, toRefs, watch } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import draggable from 'vuedraggable';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { useAssessmentDetailStore } from '@/stores/assessmentDetail';
import { useAuthStore } from '@/stores/auth';
import { usePreferencesStore } from '@/stores/preferences';
import type {
    ActivityRead,
    ActivitySortField,
    ActivityState,
} from '@/types/utils';

const props = withDefaults(
    defineProps<{
        assessmentId: string;
        collapsed?: boolean;
        sortBy: ActivitySortField;
        sortOrder: 'asc' | 'desc';
    }>(),
    {
        collapsed: false,
    },
);

const emit = defineEmits<{
    (e: 'toggle'): void;
    (e: 'sort-change', field: ActivitySortField, order: 'asc' | 'desc'): void;
}>();

const store = useAssessmentDetailStore();
const authStore = useAuthStore();
const preferencesStore = usePreferencesStore();
const route = useRoute();
const { collapsed } = toRefs(props);
const searchQuery = ref(preferencesStore.activityTableFilters.name || '');

// Tag pills shown per activity before collapsing the rest into "+N"
const MAX_SIDEBAR_TAGS = 2;

const expandedGroups = ref<Set<string>>(new Set(['ungrouped']));

// initialize expanded groups with all available groups initially
store.groups.forEach((g) => {
    expandedGroups.value.add(g.id);
});

// Sorting state managed by parent

const sortOptions: { label: string; value: ActivitySortField }[] = [
    { label: 'Position', value: 'activity_position' },
    { label: 'Name', value: 'name' },
    { label: 'MITRE Tactic', value: 'mitre_tactic' },
    { label: 'MITRE Technique', value: 'mitre_technique' },
    { label: 'Priority', value: 'priority' },
    { label: 'State', value: 'state' },
    { label: 'Visible', value: 'visible' },
    { label: 'Created At', value: 'created_at' },
    { label: 'Updated At', value: 'updated_at' },
];

function toggleSortOrder() {
    const newOrder = props.sortOrder === 'asc' ? 'desc' : 'asc';
    emit('sort-change', props.sortBy, newOrder);
}

function handleSortChange(newSortBy: ActivitySortField) {
    emit('sort-change', newSortBy, props.sortOrder);
}

// Watch props to trigger fetch is handled by parent

// Since we are now server-side sorting for the main list, local filtering based on search query
// still happens on the fetched list. The store fetches ALL (limit 1000) so this is fine.
const filteredActivities = computed(() => {
    return store.activities.filter((activity) => {
        if (activity.deleted) return false;
        if (
            searchQuery.value &&
            !activity.name
                .toLowerCase()
                .includes(searchQuery.value.toLowerCase())
        )
            return false;
        return true;
    });
});

const groupedActivities = computed(() => {
    const groups: Map<string, { group: any; activities: any[] }> = new Map();

    // Initialize groups in sorted order
    store.groups.forEach((group) => {
        if (!group.deleted) {
            groups.set(group.id, { group, activities: [] });
        }
    });

    // Add Ungrouped at bottom
    groups.set('ungrouped', {
        group: { id: 'ungrouped', name: 'Ungrouped' },
        activities: [],
    });

    // Add activities
    filteredActivities.value.forEach((activity) => {
        if (activity.deleted) return;
        const groupId = activity.activity_group_id || 'ungrouped';
        if (groups.has(groupId)) {
            groups.get(groupId)!.activities.push(activity);
        }
    });

    // Remove empty groups only while searching (like the activity table);
    // the synthetic Ungrouped bucket is only shown when it has activities
    for (const [groupId, data] of groups) {
        if (
            data.activities.length === 0 &&
            (searchQuery.value || groupId === 'ungrouped')
        ) {
            groups.delete(groupId);
        }
    }

    return groups;
});

const toggleGroup = (groupId: string) => {
    const newSet = new Set(expandedGroups.value);
    if (newSet.has(groupId)) {
        newSet.delete(groupId);
    } else {
        newSet.add(groupId);
    }
    expandedGroups.value = newSet;
};

// Drag & drop ordering
// vuedraggable reorders the lists it is given, so the grouped view renders a
// local copy that is rebuilt from the store whenever no drag/save is running.
type SidebarGroup = { id: string; group: any; activities: ActivityRead[] };
const groupEntries = ref<SidebarGroup[]>([]);
const dragging = ref(false);
const savingOrder = ref(false);

function syncGroupEntries() {
    groupEntries.value = [...groupedActivities.value].map(([id, data]) => ({
        id,
        group: data.group,
        activities: [...data.activities],
    }));
}

watch(
    groupedActivities,
    () => {
        if (!dragging.value && !savingOrder.value) syncGroupEntries();
    },
    { immediate: true },
);

const canReorder = computed(() =>
    authStore.hasAdminOrRedAccess(props.assessmentId),
);
// Only the unfiltered Position order matches what the server stores
const showsStoredOrder = computed(
    () =>
        props.sortBy === 'activity_position' &&
        props.sortOrder === 'asc' &&
        !searchQuery.value,
);
const dragEnabled = computed(
    () =>
        canReorder.value &&
        !collapsed.value &&
        showsStoredOrder.value &&
        !savingOrder.value,
);
const showReorderHint = computed(
    () => canReorder.value && !collapsed.value && !showsStoredOrder.value,
);

function onDragStart() {
    dragging.value = true;
}

function onDragEnd() {
    dragging.value = false;
    if (!savingOrder.value) syncGroupEntries();
}

// Errors are already shown by the API error handler; the list just reverts
async function saveOrder(action: () => Promise<void>) {
    savingOrder.value = true;
    try {
        await action();
    } catch {
        // Revert below
    } finally {
        savingOrder.value = false;
        syncGroupEntries();
    }
}

function onGroupsChange(event: { moved?: unknown }) {
    if (!event.moved) return;
    const groupIds = groupEntries.value
        .filter((entry) => entry.id !== 'ungrouped')
        .map((entry) => entry.id);
    saveOrder(() => store.reorderGroups(props.assessmentId, groupIds));
}

function onActivitiesChange(
    entry: SidebarGroup,
    event: {
        added?: { element: ActivityRead };
        moved?: { element: ActivityRead };
    },
) {
    const change = event.added ?? event.moved;
    if (!change) return;
    const orderedIds = entry.activities.map((a) => a.id);
    saveOrder(() =>
        store.placeActivity(
            props.assessmentId,
            change.element.id,
            entry.id,
            orderedIds,
            !!event.added,
        ),
    );
}

function toggleCollapse() {
    emit('toggle');
}

const stateIcons: Record<ActivityState, any> = {
    Pending: Circle,
    'Waiting Red': CircleQuestionMark,
    'Waiting Blue': CircleQuestionMark,
    Ready: PlayCircle,
    'In Progress': PlayCircle,
    'In Evaluation': CircleQuestionMark,
    Completed: CheckCircle2,
    Cancelled: XCircle,
};

const stateColors: Record<ActivityState, string> = {
    Pending: 'text-muted-foreground',
    'Waiting Red': 'text-red-500',
    'Waiting Blue': 'text-blue-500',
    Ready: 'text-teal-500',
    'In Progress': 'text-orange-500',
    'In Evaluation': 'text-purple-500',
    Completed: 'text-green-600',
    Cancelled: 'text-yellow-500',
};

function getStateIcon(state: ActivityState | null | undefined) {
    if (!state) return Circle;
    return stateIcons[state] || Circle;
}

function getStateColor(state: ActivityState | null | undefined) {
    if (!state) return 'text-muted-foreground';
    return stateColors[state] || 'text-muted-foreground';
}

const toggleViewMode = () => {
    preferencesStore.setActivityViewMode(
        preferencesStore.activityViewMode === 'grouped' ? 'flat' : 'grouped',
    );
};
</script>

<template>
    <aside 
        :class="cn(
            'relative flex flex-col bg-background transition-all duration-300 h-full w-full overflow-hidden'
        )"
    >
        <div class="flex items-center justify-between p-4 border-b h-14">
            <h2 v-if="!collapsed" class="text-sm font-semibold truncate tracking-tight">
                Activities
            </h2>
            <Button 
                variant="ghost" 
                size="icon" 
                class="ml-auto h-8 w-8" 
                @click="toggleCollapse"
            >
                <ChevronLeft v-if="!collapsed" class="h-4 w-4" />
                <ChevronRight v-else class="h-4 w-4" />
            </Button>
        </div>

        <div v-if="!collapsed" class="p-2 border-b space-y-2">
            <div class="relative">
                <Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input 
                    v-model="searchQuery" 
                    placeholder="Search activities..." 
                    class="pl-8"
                />
            </div>
            
            <!-- Sort controls -->
             <div class="flex items-center gap-1">
                <Select :model-value="sortBy" @update:model-value="handleSortChange($event as ActivitySortField)">
                    <SelectTrigger class="h-8 text-xs flex-1">
                        <SelectValue placeholder="Sort by" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem 
                            v-for="option in sortOptions" 
                            :key="option.value" 
                            :value="option.value"
                            class="text-xs"
                        >
                            {{ option.label }}
                        </SelectItem>
                    </SelectContent>
                </Select>
                <Button 
                    variant="outline" 
                    size="icon" 
                    class="h-8 w-8 shrink-0"
                    @click="toggleSortOrder"
                    title="Toggle sort order"
                >
                    <ArrowUpAZ v-if="sortOrder === 'asc'" class="h-3.5 w-3.5" />
                    <ArrowDownAZ v-else class="h-3.5 w-3.5" />
                </Button>
                <Button 
                    variant="outline" 
                    size="icon" 
                    class="h-8 w-8 shrink-0"
                    @click="toggleViewMode"
                    :title="preferencesStore.activityViewMode === 'grouped' ? 'Switch to list view' : 'Switch to grouped view'"
                >
                    <Folders v-if="preferencesStore.activityViewMode === 'grouped'" class="h-3.5 w-3.5" />
                    <List v-else class="h-3.5 w-3.5" />
                </Button>
            </div>
        </div>

        <ScrollArea class="flex-1 min-h-0">
            <nav class="grid gap-1 px-2 py-2">
                <template v-if="preferencesStore.activityViewMode === 'grouped'">
                    <p v-if="showReorderHint" class="px-2 pb-1 text-[11px] leading-snug text-muted-foreground">
                        Sort by Position (ascending) and clear the search to reorder by drag &amp; drop.
                    </p>
                    <!-- Groups: drag the grip on a group header to reorder groups -->
                    <draggable
                        :list="groupEntries"
                        item-key="id"
                        group="sidebar-groups"
                        handle=".group-drag-handle"
                        :disabled="!dragEnabled"
                        ghost-class="opacity-30"
                        :animation="200"
                        :force-fallback="true"
                        :scroll="true"
                        class="grid gap-1"
                        @start="onDragStart"
                        @end="onDragEnd"
                        @change="onGroupsChange"
                    >
                        <template #item="{ element: entry }">
                            <div :class="['grid gap-1', collapsed ? '' : 'mt-2 first:mt-0']">
                                <!-- Group Header -->
                                <div
                                    v-if="!collapsed"
                                    class="flex items-center gap-2 px-1 py-1 text-sm font-medium select-none group/header"
                                >
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        class="h-6 w-6 shrink-0 z-10 p-0"
                                        @click.prevent="toggleGroup(entry.id)"
                                    >
                                        <ChevronRight v-if="!expandedGroups.has(entry.id)" class="h-4 w-4 shrink-0 transition-transform" />
                                        <ChevronDown v-else class="h-4 w-4 shrink-0 transition-transform" />
                                    </Button>

                                    <!-- draggable="false": stop the browser's native link drag from competing with the grip -->
                                    <RouterLink
                                        v-if="entry.id !== 'ungrouped'"
                                        :to="{ name: 'assessment-group-detail', params: { id: assessmentId, groupId: entry.id } }"
                                        draggable="false"
                                        :class="cn(
                                            'flex flex-1 min-w-0 items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted/50 transition-colors',
                                            route.params.groupId === entry.id ? 'bg-muted/80 text-foreground' : 'text-muted-foreground'
                                        )"
                                    >
                                        <Folder v-if="!expandedGroups.has(entry.id)" class="h-4 w-4 shrink-0" />
                                        <FolderOpen v-else class="h-4 w-4 shrink-0" />
                                        <EyeOff
                                            v-if="!entry.group.visible"
                                            class="h-3.5 w-3.5 text-muted-foreground/50 shrink-0 flex-none"
                                            title="Group not visible to blue/spectator"
                                        />
                                        <span class="truncate">{{ entry.group.name }}</span>
                                    </RouterLink>
                                    <div v-else class="flex flex-1 min-w-0 items-center gap-2 rounded-md px-2 py-1.5 text-muted-foreground">
                                        <Folder v-if="!expandedGroups.has(entry.id)" class="h-4 w-4 shrink-0" />
                                        <FolderOpen v-else class="h-4 w-4 shrink-0" />
                                        <span class="truncate">{{ entry.group.name }}</span>
                                    </div>

                                    <span
                                        v-if="dragEnabled && entry.id !== 'ungrouped'"
                                        class="group-drag-handle mr-2 shrink-0 cursor-grab rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:bg-muted group-hover/header:opacity-100"
                                        title="Drag to reorder group"
                                    >
                                        <GripVertical class="h-4 w-4" />
                                    </span>
                                </div>

                                <!-- Group Activities: drag the grip to reorder or move to another (expanded) group -->
                                <draggable
                                    v-if="expandedGroups.has(entry.id) || collapsed"
                                    :list="entry.activities"
                                    item-key="id"
                                    handle=".activity-drag-handle"
                                    :disabled="!dragEnabled"
                                    :group="{ name: 'sidebar-activities', put: entry.id !== 'ungrouped' ? ['sidebar-activities'] : false }"
                                    ghost-class="opacity-30"
                                    :animation="200"
                                    :force-fallback="true"
                                    :scroll="true"
                                    :class="[
                                        'grid gap-1',
                                        dragging && entry.activities.length === 0 ? 'min-h-9 rounded-md border border-dashed' : ''
                                    ]"
                                    @start="onDragStart"
                                    @end="onDragEnd"
                                    @change="onActivitiesChange(entry, $event)"
                                >
                                    <template #item="{ element: activity }">
                                        <RouterLink
                                            :to="{ name: 'assessment-activity-detail', params: { id: assessmentId, activityId: activity.id } }"
                                            draggable="false"
                                            :class="cn(
                                                'group/item flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors',
                                                route.params.activityId === activity.id ? 'bg-accent text-accent-foreground' : 'transparent',
                                                collapsed ? 'justify-center px-2' : 'pl-8'
                                            )"
                                            :title="collapsed ? activity.name : undefined"
                                        >
                                            <div class="flex items-center gap-1 shrink-0">
                                                <component
                                                    :is="getStateIcon(activity.state)"
                                                    :class="cn('h-4 w-4', getStateColor(activity.state))"
                                                />
                                                <EyeOff
                                                    v-if="!collapsed && !activity.visible"
                                                    class="h-3.5 w-3.5 text-muted-foreground/50 shrink-0 flex-none"
                                                    title="Not visible to blue/spectator"
                                                />
                                            </div>
                                            <div v-if="!collapsed" class="flex flex-col min-w-0 flex-1 gap-0.5 mt-0.5 mb-0.5">
                                                <span class="truncate font-medium leading-none">
                                                    {{ activity.name }}
                                                </span>
                                            </div>
                                            <div
                                                v-if="!collapsed && activity.tags?.length"
                                                class="flex items-center gap-1 shrink-0"
                                                :title="activity.tags.map((t: { name: string }) => t.name).join(', ')"
                                            >
                                                <Badge
                                                    v-for="tag in activity.tags.slice(0, MAX_SIDEBAR_TAGS)"
                                                    :key="tag.id"
                                                    variant="outline"
                                                    class="h-4 max-w-20 px-1.5 text-[10px] leading-none"
                                                    :style="{ borderColor: tag.color, color: tag.color }"
                                                >
                                                    <span class="truncate">{{ tag.name }}</span>
                                                </Badge>
                                                <span v-if="activity.tags.length > MAX_SIDEBAR_TAGS" class="text-[10px] text-muted-foreground">
                                                    +{{ activity.tags.length - MAX_SIDEBAR_TAGS }}
                                                </span>
                                            </div>
                                            <span
                                                v-if="dragEnabled"
                                                class="activity-drag-handle shrink-0 cursor-grab rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:bg-muted group-hover/item:opacity-100"
                                                title="Drag to reorder or move to another group"
                                                @click.prevent.stop
                                            >
                                                <GripVertical class="h-4 w-4" />
                                            </span>
                                        </RouterLink>
                                    </template>
                                </draggable>
                            </div>
                        </template>
                    </draggable>
                </template>
                <template v-else>
                    <RouterLink
                        v-for="activity in filteredActivities"
                        :key="activity.id"
                        :to="{ name: 'assessment-activity-detail', params: { id: assessmentId, activityId: activity.id } }"
                        :class="cn(
                            'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors',
                            route.params.activityId === activity.id ? 'bg-accent text-accent-foreground' : 'transparent',
                            collapsed ? 'justify-center px-2' : ''
                        )"
                        :title="collapsed ? activity.name : undefined"
                    >
                        <div class="flex items-center gap-1 shrink-0">
                            <component
                                :is="getStateIcon(activity.state)"
                                :class="cn('h-4 w-4', getStateColor(activity.state))"
                            />
                            <EyeOff
                                v-if="!collapsed && !activity.visible"
                                class="h-3.5 w-3.5 text-muted-foreground/50 shrink-0 flex-none"
                                title="Not visible to blue/spectator"
                            />
                        </div>
                        <div v-if="!collapsed" class="flex flex-col min-w-0 flex-1 gap-0.5 mt-0.5 mb-0.5">
                            <span class="truncate font-medium leading-none">
                                {{ activity.name }}
                            </span>
                        </div>
                        <div
                            v-if="!collapsed && activity.tags?.length"
                            class="flex items-center gap-1 shrink-0"
                            :title="activity.tags.map((t) => t.name).join(', ')"
                        >
                            <Badge
                                v-for="tag in activity.tags.slice(0, MAX_SIDEBAR_TAGS)"
                                :key="tag.id"
                                variant="outline"
                                class="h-4 max-w-20 px-1.5 text-[10px] leading-none"
                                :style="{ borderColor: tag.color, color: tag.color }"
                            >
                                <span class="truncate">{{ tag.name }}</span>
                            </Badge>
                            <span v-if="activity.tags.length > MAX_SIDEBAR_TAGS" class="text-[10px] text-muted-foreground">
                                +{{ activity.tags.length - MAX_SIDEBAR_TAGS }}
                            </span>
                        </div>
                    </RouterLink>
                </template>
            </nav>
        </ScrollArea>
    </aside>
</template>
