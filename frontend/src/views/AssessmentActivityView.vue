<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import {
    type NavigationGuardNext,
    onBeforeRouteLeave,
    onBeforeRouteUpdate,
    useRoute,
    useRouter,
} from 'vue-router';
import ActivityForm from '@/components/assessment/ActivityForm.vue';
import ActivityGroupForm from '@/components/assessment/ActivityGroupForm.vue';
import ActivitySidebar from '@/components/assessment/ActivitySidebar.vue';
import {
    AlertDialog,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from '@/components/ui/resizable';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAutoRefresh } from '@/composables/useAutoRefresh';
import { useAssessmentDetailStore } from '@/stores/assessmentDetail';
import { useAuthStore } from '@/stores/auth';

import type { ActivitySortField } from '@/types/utils';

const route = useRoute();
const router = useRouter();
const store = useAssessmentDetailStore();
const authStore = useAuthStore();

const sidebarPanel = ref<any>(null);
const isSidebarCollapsed = ref(false);

const assessmentId = computed(() => route.params.id as string);
const activityId = computed(() => route.params.activityId as string);
const groupId = computed(() => route.params.groupId as string);

// Sorting state
const sortBy = ref<ActivitySortField>('activity_position');
const sortOrder = ref<'asc' | 'desc'>('asc');

const currentActivity = computed(() => {
    return store.activities.find((a) => a.id === activityId.value);
});

const currentGroup = computed(() => {
    return store.groups.find((g) => g.id === groupId.value);
});

const userRole = computed(() =>
    authStore.getAssessmentRole(assessmentId.value),
);

onMounted(async () => {
    await loadData();
});

watch(assessmentId, async (newId, oldId) => {
    if (newId !== oldId) {
        await loadData();
    }
});

// Fetch fresh data if the user directly lands on an activity not loaded yet
watch(activityId, async () => {
    if (assessmentId.value && activityId.value && !currentActivity.value) {
        await fetchActivities();
    }
});

async function loadData() {
    if (assessmentId.value) {
        if (!store.assessment || store.assessment.id !== assessmentId.value) {
            await store.fetchAssessment(assessmentId.value);
        }
        if (
            store.groups.length === 0 ||
            store.assessment?.id !== assessmentId.value
        ) {
            await store.fetchGroups(assessmentId.value);
        }
        // Always fetch the full list when mounting to ignore table filters.
        // The table view mutates this store array based on its column filters.
        await fetchActivities();
    }
}

async function fetchActivities() {
    await store.fetchActivities(assessmentId.value, {
        limit: 1000,
        sort_by: sortBy.value,
        sort_order: sortOrder.value,
    });
}

function handleSortChange(field: ActivitySortField, order: 'asc' | 'desc') {
    sortBy.value = field;
    sortOrder.value = order;
    fetchActivities();
}

// Hook up background background data refresh so the sidebar updates automatically
useAutoRefresh(async () => {
    if (assessmentId.value) {
        await fetchActivities();
    }
});

async function handleActivitySaved() {
    await fetchActivities();
    store.fetchAssessment(assessmentId.value);
}

async function handleActivityCloned(clonedActivityId: string) {
    await fetchActivities();
    router.push({
        name: 'assessment-activity-detail',
        params: { id: assessmentId.value, activityId: clonedActivityId },
    });
}

function handleSidebarToggle() {
    isSidebarCollapsed.value = !isSidebarCollapsed.value;
    const panel = sidebarPanel.value?.panel;
    if (panel) {
        if (isSidebarCollapsed.value) {
            panel.resize(4);
        } else {
            panel.resize(20);
        }
    }
}

const activityFormRef = ref<any>(null);
const showUnsavedDialog = ref(false);
let resolveNavigation: ((value: boolean) => void) | null = null;

function checkUnsavedChanges(): boolean | Promise<boolean> {
    if (activityFormRef.value?.hasUnsavedChanges) {
        showUnsavedDialog.value = true;
        return new Promise((resolve) => {
            resolveNavigation = resolve;
        });
    }
    return true;
}

onBeforeRouteLeave((_to, _from) => {
    return checkUnsavedChanges();
});

onBeforeRouteUpdate((to, from) => {
    if (
        to.params.activityId !== from.params.activityId ||
        to.params.groupId !== from.params.groupId
    ) {
        return checkUnsavedChanges();
    }
    return true;
});

function confirmDiscard() {
    showUnsavedDialog.value = false;
    if (resolveNavigation) {
        resolveNavigation(true);
        resolveNavigation = null;
    }
}

function cancelNavigation() {
    showUnsavedDialog.value = false;
    if (resolveNavigation) {
        resolveNavigation(false);
        resolveNavigation = null;
    }
}
</script>

<template>
    <div class="h-[calc(100vh-65px)] w-full bg-background overflow-hidden">
        <ResizablePanelGroup direction="horizontal" class="h-full w-full rounded-lg border">
            <ResizablePanel ref="sidebarPanel" :default-size="20" :min-size="4" :max-size="40">
                <ActivitySidebar 
                    :assessment-id="assessmentId" 
                    :collapsed="isSidebarCollapsed"
                    :sort-by="sortBy"
                    :sort-order="sortOrder"
                    @toggle="handleSidebarToggle"
                    @sort-change="handleSortChange"
                />
            </ResizablePanel>
            
            <ResizableHandle with-handle />
            
            <ResizablePanel :default-size="80">
                <ScrollArea class="h-full w-full">
                    <main>
                        <div v-if="currentActivity" class="w-full py-6 px-8 max-w-[2500px] mx-auto">
                            <ActivityForm
                                ref="activityFormRef"
                                :activity="currentActivity"
                                :assessment-id="assessmentId"
                                :role="userRole"
                                @saved="handleActivitySaved"
                                @cloned="handleActivityCloned"
                            />
                        </div>
                        <div v-else-if="currentGroup" class="w-full py-6 px-8 max-w-[2500px] mx-auto">
                            <!-- Activity Group Form -->
                            <ActivityGroupForm
                                :group="currentGroup"
                                :assessment-id="assessmentId"
                                :role="userRole"
                                @saved="handleActivitySaved"
                            />
                        </div>
                        <div v-else-if="store.loading" class="flex items-center justify-center h-full">
                            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                        </div>
                        <div v-else class="flex items-center justify-center h-full text-muted-foreground">
                            Select an activity or group to view details
                        </div>
                    </main>
                </ScrollArea>
            </ResizablePanel>
        </ResizablePanelGroup>

        <!-- Unsaved Changes Dialog -->
        <AlertDialog :open="showUnsavedDialog" @update:open="(val) => !val && cancelNavigation()">
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Unsaved Changes</AlertDialogTitle>
                    <AlertDialogDescription>
                        You have unsaved changes in this activity. Are you sure you want to leave? Your changes will be lost.
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel @click="cancelNavigation">Stay on Page</AlertDialogCancel>
                    <Button variant="destructive" @click="confirmDiscard">
                        Discard Changes
                    </Button>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    </div>
</template>
