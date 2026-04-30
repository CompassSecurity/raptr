<script setup lang="ts">
import { AlertTriangle } from 'lucide-vue-next';
import { computed, ref, watch } from 'vue';
import { Badge } from '@/components/ui/badge';
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
import type { ActivityRead } from '@/types/utils';
import {
    buildMergedResult,
    computeConflicts,
    type FieldConflict,
    type FieldDisplayLookups,
    formatFieldValue,
} from '@/utils/conflictUtils';

const props = defineProps<{
    open: boolean;
    myVersion: Partial<ActivityRead>;
    serverVersion: ActivityRead;
    originalVersion: Partial<ActivityRead>;
    displayLookups?: FieldDisplayLookups;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (
        e: 'resolved',
        mergedData: Record<string, unknown>,
        newUpdatedAt: string,
    ): void;
    (e: 'cancel'): void;
}>();

const conflicts = ref<FieldConflict[]>([]);
const autoMerged = ref<Record<string, unknown>>({});

// Compute conflicts when dialog opens
watch(
    () => props.open,
    (isOpen) => {
        if (isOpen) {
            const result = computeConflicts(
                props.myVersion as Record<string, unknown>,
                props.serverVersion as Record<string, unknown>,
                props.originalVersion as Record<string, unknown>,
            );
            conflicts.value = result.conflicts;
            autoMerged.value = result.autoMerged;
        }
    },
    { immediate: true },
);

// Group conflicts by section
const groupedConflicts = computed(() => {
    const groups: Record<string, FieldConflict[]> = {};
    for (const c of conflicts.value) {
        if (!groups[c.section]) groups[c.section] = [];
        groups[c.section]!.push(c);
    }
    return groups;
});

function setChoice(field: string, choice: 'mine' | 'theirs') {
    const conflict = conflicts.value.find((c) => c.field === field);
    if (conflict) conflict.choice = choice;
}

function setAllChoices(choice: 'mine' | 'theirs') {
    for (const c of conflicts.value) {
        c.choice = choice;
    }
}

function handleResolve() {
    const merged = buildMergedResult(autoMerged.value, conflicts.value);
    emit('resolved', merged, props.serverVersion.updated_at as string);
    emit('update:open', false);
}

function handleCancel() {
    emit('cancel');
    emit('update:open', false);
}
</script>

<template>
    <Dialog :open="open" @update:open="$emit('update:open', $event)">
        <DialogContent class="!max-w-4xl max-h-[60vh] overflow-hidden gap-0 p-0">
            <DialogHeader class="px-6 pt-6 pb-4 shrink-0">
                <div class="flex items-center gap-2">
                    <AlertTriangle class="h-5 w-5 text-amber-500" />
                    <DialogTitle class="text-lg">Conflict Detected</DialogTitle>
                </div>
                <DialogDescription>
                    This activity was modified by another user while you were editing.
                    Review the differences below and choose which version to keep for each field.
                </DialogDescription>
            </DialogHeader>

            <ScrollArea class="max-h-[calc(60vh-12rem)] px-6">
                <div class="space-y-4 pb-4">
                    <!-- Bulk actions -->
                    <div class="flex items-center justify-between text-sm">
                        <span class="text-muted-foreground">
                            {{ conflicts.length }} differing field{{ conflicts.length > 1 ? 's' : '' }}
                        </span>
                        <div class="flex gap-2">
                            <Button variant="outline" size="sm" @click="setAllChoices('mine')">
                                Keep All Mine
                            </Button>
                            <Button variant="outline" size="sm" @click="setAllChoices('theirs')">
                                Use All Theirs
                            </Button>
                        </div>
                    </div>

                    <!-- Grouped conflicts -->
                    <div v-for="(fields, section) in groupedConflicts" :key="section" class="space-y-3">
                        <h4 class="text-sm font-semibold text-muted-foreground border-b pb-1">
                            {{ section }}
                        </h4>

                        <div
                            v-for="conflict in fields"
                            :key="conflict.field"
                            class="rounded-lg border p-3 space-y-2"
                            :class="{ 'opacity-60': conflict.status === 'removed' }"
                        >
                            <div class="flex items-center gap-2">
                                <div class="font-medium text-sm" :class="{ 'line-through': conflict.status === 'removed' }">
                                    {{ conflict.label }}
                                </div>
                                <Badge v-if="conflict.status === 'removed'" variant="outline" class="text-xs text-red-600 dark:text-red-400 border-red-300 dark:border-red-700">
                                    Removed — your edit will be dropped
                                </Badge>
                                <Badge v-else-if="conflict.status === 'added'" variant="outline" class="text-xs text-green-600 dark:text-green-400 border-green-300 dark:border-green-700">
                                    Newly added
                                </Badge>
                            </div>

                            <!-- My version -->
                            <label
                                class="flex items-start gap-3 p-2 rounded-md transition-colors"
                                :class="[
                                    conflict.status === 'removed' ? 'cursor-not-allowed' : 'cursor-pointer',
                                    conflict.choice === 'mine'
                                        ? 'bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800'
                                        : 'hover:bg-muted/50',
                                ]"
                            >
                                <input
                                    type="radio"
                                    :name="`conflict-${conflict.field}`"
                                    :checked="conflict.choice === 'mine'"
                                    :disabled="conflict.status === 'removed'"
                                    class="mt-1 accent-blue-600"
                                    @change="setChoice(conflict.field, 'mine')"
                                />
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center gap-2 mb-1">
                                        <Badge variant="outline" class="text-xs text-blue-600 dark:text-blue-400 border-blue-300 dark:border-blue-700">
                                            Your version
                                        </Badge>
                                    </div>
                                    <p class="text-sm text-muted-foreground break-words whitespace-pre-wrap" :class="{ 'line-through': conflict.status === 'removed' }">
                                        {{ formatFieldValue(conflict.myValue, conflict.field, displayLookups) }}
                                    </p>
                                </div>
                            </label>

                            <!-- Server version -->
                            <label
                                class="flex items-start gap-3 p-2 rounded-md transition-colors"
                                :class="[
                                    conflict.status === 'removed' ? 'cursor-not-allowed' : 'cursor-pointer',
                                    conflict.choice === 'theirs'
                                        ? 'bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800'
                                        : 'hover:bg-muted/50',
                                ]"
                            >
                                <input
                                    type="radio"
                                    :name="`conflict-${conflict.field}`"
                                    :checked="conflict.choice === 'theirs'"
                                    :disabled="conflict.status === 'removed'"
                                    class="mt-1 accent-amber-600"
                                    @change="setChoice(conflict.field, 'theirs')"
                                />
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center gap-2 mb-1">
                                        <Badge variant="outline" class="text-xs text-amber-600 dark:text-amber-400 border-amber-300 dark:border-amber-700">
                                            Server version
                                        </Badge>
                                    </div>
                                    <p class="text-sm text-muted-foreground break-words whitespace-pre-wrap">
                                        {{ formatFieldValue(conflict.serverValue, conflict.field, displayLookups) }}
                                    </p>
                                </div>
                            </label>
                        </div>
                    </div>
                </div>
            </ScrollArea>

            <DialogFooter class="px-6 pb-6 pt-4 gap-2 border-t shrink-0">
                <Button variant="outline" @click="handleCancel">Cancel</Button>
                <Button @click="handleResolve">Resolve & Save</Button>
            </DialogFooter>
        </DialogContent>
    </Dialog>
</template>
