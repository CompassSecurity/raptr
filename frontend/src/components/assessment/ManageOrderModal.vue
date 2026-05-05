<script setup lang="ts">
import {
    ChevronDown,
    ChevronRight,
    Folder,
    FolderOpen,
    GripVertical,
    Loader2,
} from '@lucide/vue';
import { ref, watch } from 'vue';
import { toast } from 'vue-sonner';
import draggable from 'vuedraggable';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
    activityGroupService,
    activityService,
} from '@/services/activityService';
import type { ActivityGroupRead, ActivityRead } from '@/types/utils';

const props = defineProps<{
    open: boolean;
    assessmentId: string;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

// State
const saving = ref(false);
const loadingGroups = ref(false);
const groups = ref<ActivityGroupRead[]>([]);
const expandedGroups = ref<Set<string>>(new Set());
const groupActivities = ref<Map<string, ActivityRead[]>>(new Map());
const loadingActivities = ref<Set<string>>(new Set());

// Track initial order to detect changes
const initialGroupOrder = ref<string[]>([]);
const initialActivityOrders = ref<Map<string, string[]>>(new Map());
// Track initial group membership to detect cross-group moves
const initialActivityGroup = ref<Map<string, string>>(new Map());

// Initialize data when modal opens
watch(
    () => props.open,
    async (isOpen) => {
        if (isOpen) {
            await fetchGroups();
        } else {
            expandedGroups.value.clear();
            groupActivities.value.clear();
            initialActivityGroup.value.clear();
        }
    },
    { immediate: true },
);

async function fetchGroups() {
    loadingGroups.value = true;
    try {
        const allGroups = await activityGroupService.getGroups(
            props.assessmentId,
            {
                sort_by: 'activity_group_position',
                sort_order: 'asc',
            },
        );
        // Filter out deleted (server already sorts by position)
        groups.value = allGroups.filter((g) => !g.deleted);
        initialGroupOrder.value = groups.value.map((g) => g.id);
    } catch (e) {
        toast.error('Failed to load activity groups');
    } finally {
        loadingGroups.value = false;
    }
}

async function toggleGroup(groupId: string) {
    if (expandedGroups.value.has(groupId)) {
        expandedGroups.value.delete(groupId);
    } else {
        expandedGroups.value.add(groupId);
        if (!groupActivities.value.has(groupId)) {
            await fetchActivitiesForGroup(groupId);
        }
    }
}

async function fetchActivitiesForGroup(groupId: string) {
    loadingActivities.value.add(groupId);
    try {
        const activities = await activityGroupService.getGroupActivities(
            props.assessmentId,
            groupId,
        );
        // Already filtered to non-deleted by backend, sort by position
        const sorted = activities.sort(
            (a, b) => (a.activity_position ?? 0) - (b.activity_position ?? 0),
        );
        groupActivities.value.set(groupId, sorted);
        initialActivityOrders.value.set(
            groupId,
            sorted.map((a) => a.id),
        );
        sorted.forEach((a) => {
            initialActivityGroup.value.set(a.id, groupId);
        });
    } catch (e) {
        toast.error('Failed to load activities');
    } finally {
        loadingActivities.value.delete(groupId);
    }
}

function getGroupActivities(groupId: string): ActivityRead[] {
    return groupActivities.value.get(groupId) ?? [];
}

function setGroupActivities(groupId: string, activities: ActivityRead[]) {
    groupActivities.value.set(groupId, activities);
}

function hasChanges(): boolean {
    // Check group order
    const currentGroupOrder = groups.value.map((g) => g.id);
    if (
        JSON.stringify(currentGroupOrder) !==
        JSON.stringify(initialGroupOrder.value)
    )
        return true;

    // Check activity orders and group membership
    for (const [groupId, activities] of groupActivities.value) {
        const currentOrder = activities.map((a) => a.id);
        const initial = initialActivityOrders.value.get(groupId);
        if (initial && JSON.stringify(currentOrder) !== JSON.stringify(initial))
            return true;
        // Check if any activity moved into this group from another
        for (const a of activities) {
            if (initialActivityGroup.value.get(a.id) !== groupId) return true;
        }
    }

    return false;
}

async function handleSave() {
    if (!hasChanges()) {
        emit('update:open', false);
        return;
    }

    saving.value = true;
    try {
        // First, move activities that changed groups
        const movePromises: Promise<unknown>[] = [];
        for (const [groupId, activities] of groupActivities.value) {
            for (const activity of activities) {
                if (initialActivityGroup.value.get(activity.id) !== groupId) {
                    movePromises.push(
                        activityService.bulkMoveToGroup(
                            props.assessmentId,
                            [activity.id],
                            groupId,
                        ),
                    );
                }
            }
        }
        if (movePromises.length > 0) {
            await Promise.all(movePromises);
        }

        // Then reorder groups and activities within groups
        const reorderPromises: Promise<unknown>[] = [];

        const currentGroupOrder = groups.value.map((g) => g.id);
        if (
            JSON.stringify(currentGroupOrder) !==
            JSON.stringify(initialGroupOrder.value)
        ) {
            reorderPromises.push(
                activityGroupService.reorderGroups(
                    props.assessmentId,
                    currentGroupOrder,
                ),
            );
        }

        for (const [groupId, activities] of groupActivities.value) {
            const currentOrder = activities.map((a) => a.id);
            const initial = initialActivityOrders.value.get(groupId);
            // Reorder if the list changed (different order OR different members)
            if (
                !initial ||
                JSON.stringify(currentOrder) !== JSON.stringify(initial)
            ) {
                reorderPromises.push(
                    activityGroupService.reorderActivities(
                        props.assessmentId,
                        groupId,
                        currentOrder,
                    ),
                );
            }
        }

        await Promise.all(reorderPromises);
        toast.success('Order updated successfully');
        emit('success');
        emit('update:open', false);
    } catch (e: any) {
        const detail = e?.response?.data?.detail;
        toast.error(detail || 'Failed to update order');
    } finally {
        saving.value = false;
    }
}
</script>

<template>
    <Dialog :open="open" @update:open="$emit('update:open', $event)">
        <DialogContent class="!w-[600px] !max-w-[600px] h-[70vh] flex flex-col">
            <DialogHeader>
                <DialogTitle>Manage Order</DialogTitle>
                <DialogDescription>
                    Drag and drop to reorder activity groups and activities. Drag activities between groups to move them.
                </DialogDescription>
            </DialogHeader>

            <div class="flex-1 flex flex-col min-h-0 overflow-hidden">
                <div v-if="loadingGroups" class="flex items-center justify-center py-8">
                    <Loader2 class="h-5 w-5 animate-spin text-muted-foreground" />
                </div>

                <div v-else-if="groups.length === 0" class="p-6 border border-dashed rounded-lg bg-muted/30 text-center flex-1 flex items-center justify-center">
                    <p class="text-sm text-muted-foreground">No activity groups found.</p>
                </div>

                <ScrollArea v-else class="h-full w-full border rounded-lg">
                    <draggable
                        v-model="groups"
                        item-key="id"
                        handle=".group-drag-handle"
                        ghost-class="opacity-30"
                        animation="200"
                        :force-fallback="true"
                        :scroll="true"
                        class="divide-y"
                    >
                        <template #item="{ element: group }">
                            <div>
                                <!-- Group row -->
                                <div
                                    class="flex items-center gap-2 px-3 py-2.5 bg-muted/30 hover:bg-muted/50 select-none"
                                >
                                    <GripVertical class="h-4 w-4 text-muted-foreground cursor-grab group-drag-handle shrink-0" />
                                    <button
                                        class="flex items-center gap-2 flex-1 min-w-0 text-left"
                                        @click="toggleGroup(group.id)"
                                    >
                                        <ChevronDown v-if="expandedGroups.has(group.id)" class="h-4 w-4 shrink-0" />
                                        <ChevronRight v-else class="h-4 w-4 shrink-0" />
                                        <FolderOpen v-if="expandedGroups.has(group.id)" class="h-4 w-4 text-muted-foreground shrink-0" />
                                        <Folder v-else class="h-4 w-4 text-muted-foreground shrink-0" />
                                        <span class="text-sm font-medium truncate">{{ group.name }}</span>
                                    </button>
                                </div>

                                <!-- Activities within group (expandable) -->
                                <div v-if="expandedGroups.has(group.id)" class="bg-background">
                                    <div v-if="loadingActivities.has(group.id)" class="flex items-center justify-center py-4">
                                        <Loader2 class="h-4 w-4 animate-spin text-muted-foreground" />
                                    </div>
                                    <draggable
                                        v-else
                                        :model-value="getGroupActivities(group.id)"
                                        @update:model-value="setGroupActivities(group.id, $event)"
                                        item-key="id"
                                        handle=".activity-drag-handle"
                                        ghost-class="opacity-30"
                                        animation="200"
                                        :force-fallback="true"
                                        :scroll="true"
                                        :group="{ name: 'activities' }"
                                        class="min-h-[36px]"
                                    >
                                        <template #item="{ element: activity, index }">
                                            <div class="flex items-center gap-2 px-3 py-2 pl-10 hover:bg-muted/30 border-t border-dashed select-none">
                                                <GripVertical class="h-3.5 w-3.5 text-muted-foreground cursor-grab activity-drag-handle shrink-0" />
                                                <span class="text-xs text-muted-foreground w-5 shrink-0">{{ index + 1 }}.</span>
                                                <span class="text-sm truncate">{{ activity.name }}</span>
                                            </div>
                                        </template>
                                        <template #footer>
                                            <p v-if="getGroupActivities(group.id).length === 0" class="px-10 py-2 text-xs text-muted-foreground">
                                                Drop activities here
                                            </p>
                                        </template>
                                    </draggable>
                                </div>
                            </div>
                        </template>
                    </draggable>
                </ScrollArea>
            </div>

            <DialogFooter>
                <Button variant="outline" @click="$emit('update:open', false)">Cancel</Button>
                <Button @click="handleSave" :disabled="saving">
                    <Loader2 v-if="saving" class="h-4 w-4 mr-2 animate-spin" />
                    Save
                </Button>
            </DialogFooter>
        </DialogContent>
    </Dialog>
</template>
