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
    List,
    PlayCircle,
    Search,
    XCircle,
} from 'lucide-vue-next';
import { computed, ref, toRefs } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
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
import { usePreferencesStore } from '@/stores/preferences';
import type { ActivitySortField, ActivityState } from '@/types/utils';

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
const preferencesStore = usePreferencesStore();
const route = useRoute();
const { collapsed } = toRefs(props);
const searchQuery = ref(preferencesStore.activityTableFilters.name || '');

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

    // Remove empty groups
    for (const [groupId, data] of groups) {
        if (data.activities.length === 0) {
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
                    <template v-for="[groupId, groupData] in groupedActivities" :key="groupId">
                        <!-- Group Header -->
                        <div 
                            v-if="!collapsed"
                            class="flex items-center gap-2 px-1 py-1 text-sm font-medium mt-2 first:mt-0 select-none group"
                        >
                            <Button
                                variant="ghost"
                                size="icon"
                                class="h-6 w-6 shrink-0 z-10 p-0"
                                @click.prevent="toggleGroup(groupId)"
                            >
                                <ChevronRight v-if="!expandedGroups.has(groupId)" class="h-4 w-4 shrink-0 transition-transform" />
                                <ChevronDown v-else class="h-4 w-4 shrink-0 transition-transform" />
                            </Button>
                            
                            <RouterLink
                                v-if="groupId !== 'ungrouped'"
                                :to="{ name: 'assessment-group-detail', params: { id: assessmentId, groupId: groupId } }"
                                :class="cn(
                                    'flex flex-1 items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted/50 transition-colors',
                                    route.params.groupId === groupId ? 'bg-muted/80 text-foreground' : 'text-muted-foreground'
                                )"
                            >
                                <Folder v-if="!expandedGroups.has(groupId)" class="h-4 w-4 shrink-0" />
                                <FolderOpen v-else class="h-4 w-4 shrink-0" />
                                <EyeOff
                                    v-if="!groupData.group.visible"
                                    class="h-3.5 w-3.5 text-muted-foreground/50 shrink-0 flex-none"
                                    title="Group not visible to blue/spectator"
                                />
                                <span class="truncate">{{ groupData.group.name }}</span>
                            </RouterLink>
                            <div v-else class="flex flex-1 items-center gap-2 rounded-md px-2 py-1.5 text-muted-foreground">
                                <Folder v-if="!expandedGroups.has(groupId)" class="h-4 w-4 shrink-0" />
                                <FolderOpen v-else class="h-4 w-4 shrink-0" />
                                <span class="truncate">{{ groupData.group.name }}</span>
                            </div>
                        </div>
                        
                        <!-- Group Activities -->
                        <template v-if="expandedGroups.has(groupId) || collapsed">
                            <RouterLink
                                v-for="activity in groupData.activities"
                                :key="activity.id"
                                :to="{ name: 'assessment-activity-detail', params: { id: assessmentId, activityId: activity.id } }"
                                :class="cn(
                                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors',
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
                            </RouterLink>
                        </template>
                    </template>
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
                    </RouterLink>
                </template>
            </nav>
        </ScrollArea>
    </aside>
</template>
