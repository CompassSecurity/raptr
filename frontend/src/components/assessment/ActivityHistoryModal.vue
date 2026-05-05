<script setup lang="ts">
import { AlertCircle, History, Loader2 } from '@lucide/vue';
import { ref, watch } from 'vue';
// We reuse the ActivityForm component in readonly mode to display the snapshot.
import ActivityForm from '@/components/assessment/ActivityForm.vue';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { activityService } from '@/services/activityService';
import type { ActivityHistoryRead, ActivityRead } from '@/types/utils';

const props = defineProps<{
    open: boolean;
    assessmentId: string;
    activityId: string;
}>();

const emit = defineEmits<{
    'update:open': [value: boolean];
}>();

const selectedVersionId = ref<string | null>(null);

const historyVersions = ref<ActivityHistoryRead[]>([]);
const isLoadingVersions = ref(false);
const isVersionsError = ref(false);

const selectedVersion = ref<ActivityHistoryRead | null>(null);
const isLoadingSnapshot = ref(false);
const isSnapshotError = ref(false);

async function fetchVersions() {
    if (!props.activityId) return;
    isLoadingVersions.value = true;
    isVersionsError.value = false;
    try {
        const data = await activityService.getActivityHistoryList(
            props.assessmentId,
            props.activityId,
        );
        historyVersions.value = data || [];
        if (data?.length && !selectedVersionId.value) {
            selectedVersionId.value = data[0]?.id || null;
        }
    } catch (e) {
        console.error(e);
        isVersionsError.value = true;
    } finally {
        isLoadingVersions.value = false;
    }
}

async function fetchSnapshot() {
    if (!selectedVersionId.value) return;
    isLoadingSnapshot.value = true;
    isSnapshotError.value = false;
    try {
        const data = await activityService.getActivityHistoryVersion(
            props.assessmentId,
            props.activityId,
            selectedVersionId.value,
        );
        selectedVersion.value = data;
    } catch (e) {
        console.error(e);
        isSnapshotError.value = true;
    } finally {
        isLoadingSnapshot.value = false;
    }
}

watch(
    () => props.open,
    (isOpen) => {
        if (isOpen) {
            fetchVersions();
        } else {
            selectedVersionId.value = null;
            selectedVersion.value = null;
        }
    },
);

watch(selectedVersionId, (newId) => {
    if (newId) fetchSnapshot();
});

const formatDate = (dateString: string) => {
    try {
        const d = new Date(dateString);
        return (
            d.toLocaleDateString() +
            ' ' +
            d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        );
    } catch {
        return dateString;
    }
};

const handleOpenChange = (val: boolean) => {
    emit('update:open', val);
};
</script>

<template>
    <Dialog :open="open" @update:open="handleOpenChange">
        <DialogContent aria-describedby="undefined" class="sm:max-w-[95vw] md:max-w-[1200px] w-[95vw] h-[90vh] flex flex-col p-0 gap-0">
            <DialogHeader class="p-4 sm:p-6 border-b shrink-0">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pr-8">
                    <DialogTitle class="flex items-center gap-2 text-xl sm:text-2xl">
                        <History class="h-5 w-5 sm:h-6 sm:w-6 text-muted-foreground" />
                        Activity Shadow Copies
                    </DialogTitle>
                    
                    <div class="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3" v-if="historyVersions && historyVersions.length > 0">
                        <span class="text-sm font-medium text-muted-foreground">Select Version:</span>
                        <Select v-model="selectedVersionId">
                            <SelectTrigger class="w-[280px]">
                                <SelectValue placeholder="Select a version..." />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem v-for="version in historyVersions" :key="version.id" :value="version.id">
                                    Version {{ version.version }} ({{ formatDate(version.saved_at) }}{{ (version as any).saved_by ? ' by ' + (version as any).saved_by.email : '' }})
                                </SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
            </DialogHeader>

            <!-- Loading States -->
            <div v-if="isLoadingVersions" class="flex-1 flex justify-center items-center">
                <Loader2 class="h-8 w-8 animate-spin text-muted-foreground" />
                <span class="ml-2 text-muted-foreground">Loading history...</span>
            </div>
            
            <div v-else-if="isVersionsError || isSnapshotError" class="p-6 flex-1">
                <div class="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-900/20 text-red-800 dark:text-red-200 flex items-start">
                    <AlertCircle class="h-5 w-5 mr-3 mt-0.5" />
                    <div>
                        <h4 class="font-medium text-sm">Error Loading History</h4>
                        <div class="text-sm opacity-90 mt-1">
                            Failed to load the activity history. You may not have the required permissions.
                        </div>
                    </div>
                </div>
            </div>

            <div v-else-if="historyVersions && historyVersions.length === 0" class="flex-1 flex flex-col items-center justify-center p-6 text-center">
                <History class="h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 class="text-lg font-medium">No History Available</h3>
                <p class="text-muted-foreground max-w-sm mt-1">
                    There are no saved versions for this activity yet.
                </p>
            </div>

            <!-- Content Area: The Readonly Activity Form displaying the snapshot -->
            <ScrollArea v-else-if="selectedVersion?.snapshot" class="flex-1 min-h-0">
                <div class="p-4 sm:p-6">
                    <div class="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200 flex items-start">
                        <History class="h-5 w-5 mr-3 mt-0.5 text-blue-500" />
                        <div>
                            <h4 class="font-medium text-sm">Viewing Version {{ selectedVersion.version }}</h4>
                            <div class="text-sm opacity-90 mt-1">
                                Saved on {{ formatDate(selectedVersion.saved_at) }}<span v-if="(selectedVersion as any).saved_by"> by {{ (selectedVersion as any).saved_by.email }}</span>. This is a read-only historical snapshot. Attachments are excluded.
                            </div>
                        </div>
                    </div>

                    <!-- Render a readonly activity form -->
                    <div class="opacity-90 grayscale-[10%]">
                        <ActivityForm
                            :key="selectedVersion.id"
                            :activity="(selectedVersion.snapshot as unknown as ActivityRead)"
                            :assessment-id="assessmentId"
                            role="spectator"
                        />
                    </div>
                </div>
            </ScrollArea>
            
            <div v-else-if="isLoadingSnapshot" class="flex-1 flex justify-center items-center">
                <Loader2 class="h-8 w-8 animate-spin text-muted-foreground" />
                <span class="ml-2 text-muted-foreground">Loading snapshot details...</span>
            </div>
        </DialogContent>
    </Dialog>
</template>
