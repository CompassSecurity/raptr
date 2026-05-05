<script setup lang="ts">
import { GripVertical, Loader2, Plus, Search, Trash2 } from '@lucide/vue';
import { computed, ref, watch } from 'vue';
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
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { activityService } from '@/services/activityService';
import { assessmentService } from '@/services/assessmentService';
import { evaluationTemplateService } from '@/services/evaluationTemplateService';
import type {
    DynamicEvaluationQuestionAssign,
    EvaluationTemplateRead,
} from '@/types/utils';

const props = withDefaults(
    defineProps<{
        open: boolean;
        assessmentId: string;
        activityId?: string;
        /** 'activity' = per-activity dynamic questions, 'assessment' = assessment default templates */
        mode?: 'activity' | 'assessment';
        /** Current questions — works with both dynamic question reads and simple {evaluation_template_id, position} dicts */
        currentQuestions: {
            evaluation_template_id: string;
            position?: number | null;
        }[];
    }>(),
    {
        mode: 'activity',
        activityId: '',
    },
);

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

// State
const saving = ref(false);
const loadingTemplates = ref(false);
const searchQuery = ref('');
const availableTemplates = ref<EvaluationTemplateRead[]>([]);

// Assigned questions as local mutable list with template info
interface AssignedQuestion {
    evaluation_template_id: string;
    name: string;
    description: string | null;
}

const assignedQuestions = ref<AssignedQuestion[]>([]);

// Computed text for dialog based on mode
const dialogTitle = computed(() =>
    props.mode === 'assessment'
        ? 'Manage Default Evaluation Templates'
        : 'Manage Evaluation Questions',
);
const dialogDescription = computed(() =>
    props.mode === 'assessment'
        ? 'Configure the default evaluation templates applied to new activities in this assessment.'
        : 'Add, remove, and reorder dynamic evaluation questions for this activity.',
);

// Fetch all available evaluation templates
async function fetchTemplates() {
    loadingTemplates.value = true;
    try {
        const response = await evaluationTemplateService.getAll({
            limit: 1000,
        });
        availableTemplates.value = response.items;
    } catch (e) {
        console.error('Failed to fetch evaluation templates:', e);
        toast.error('Failed to load evaluation templates');
    } finally {
        loadingTemplates.value = false;
    }
}

// Initialize assigned questions from props when modal opens
watch(
    () => props.open,
    (isOpen) => {
        if (isOpen) {
            fetchTemplates();
            // Build assigned list from current questions, sorted by position
            const sorted = [...props.currentQuestions].sort(
                (a, b) => (a.position ?? 0) - (b.position ?? 0),
            );
            assignedQuestions.value = sorted.map((q) => ({
                evaluation_template_id: q.evaluation_template_id,
                name: '', // will be populated once templates load
                description: null,
            }));
        } else {
            searchQuery.value = '';
        }
    },
    { immediate: true },
);

// Update names once templates are loaded
watch(
    [() => availableTemplates.value, () => assignedQuestions.value],
    () => {
        const templateMap = new Map(
            availableTemplates.value.map((t) => [t.id, t]),
        );
        for (const q of assignedQuestions.value) {
            const template = templateMap.get(q.evaluation_template_id);
            if (template) {
                q.name = template.evaluation_criteria || template.name;
                q.description = template.description ?? null;
            }
        }
    },
    { deep: true },
);

// IDs already assigned
const assignedIds = computed(
    () => new Set(assignedQuestions.value.map((q) => q.evaluation_template_id)),
);

// Filtered unassigned templates for the "Add" list
const filteredTemplates = computed(() => {
    return availableTemplates.value
        .filter((t) => !assignedIds.value.has(t.id))
        .filter((t) => {
            if (!searchQuery.value) return true;
            const q = searchQuery.value.toLowerCase();
            return (
                t.name.toLowerCase().includes(q) ||
                t.evaluation_criteria.toLowerCase().includes(q) ||
                (t.description?.toLowerCase().includes(q) ?? false)
            );
        });
});

function addQuestion(template: EvaluationTemplateRead) {
    assignedQuestions.value.push({
        evaluation_template_id: template.id,
        name: template.evaluation_criteria || template.name,
        description: template.description ?? null,
    });
}

function removeQuestion(index: number) {
    assignedQuestions.value.splice(index, 1);
}

async function handleSave() {
    saving.value = true;
    try {
        const payload: DynamicEvaluationQuestionAssign[] =
            assignedQuestions.value.map((q, idx) => ({
                evaluation_template_id: q.evaluation_template_id,
                position: idx,
            }));

        if (props.mode === 'assessment') {
            await assessmentService.updateDefaultEvaluationTemplates(
                props.assessmentId,
                payload,
            );
            toast.success('Default evaluation templates updated');
        } else {
            await activityService.assignDynamicEvaluationQuestions(
                props.assessmentId,
                props.activityId!,
                payload,
            );
            toast.success('Dynamic questions updated');
        }

        emit('success');
        emit('update:open', false);
    } catch (e: any) {
        const detail = e?.response?.data?.detail;
        toast.error(detail || 'Failed to save evaluation templates');
    } finally {
        saving.value = false;
    }
}
</script>

<template>
    <Dialog :open="open" @update:open="$emit('update:open', $event)">
        <DialogContent class="!w-[700px] !max-w-[700px] h-[70vh] flex flex-col">
            <DialogHeader>
                <DialogTitle>{{ dialogTitle }}</DialogTitle>
                <DialogDescription>
                    {{ dialogDescription }}
                </DialogDescription>
            </DialogHeader>

            <div class="flex-1 flex flex-col gap-4 min-h-0 overflow-hidden">
                <!-- Assigned Questions (drag-and-drop) -->
                <div class="flex-1 flex flex-col min-h-0">
                    <h4 class="text-sm font-medium mb-2">Assigned Questions</h4>
                    <div v-if="assignedQuestions.length === 0" class="p-6 border border-dashed rounded-lg bg-muted/30 text-center flex-1 flex items-center justify-center">
                        <p class="text-sm text-muted-foreground">No questions assigned. Add templates from below.</p>
                    </div>
                    <ScrollArea v-else class="flex-1 border rounded-lg">
                        <draggable
                            v-model="assignedQuestions"
                            item-key="evaluation_template_id"
                            handle=".drag-handle"
                            ghost-class="opacity-30"
                            animation="200"
                            class="divide-y"
                        >
                            <template #item="{ element, index }">
                                <div class="flex items-center gap-2 px-3 py-2.5 hover:bg-muted/50 group">
                                    <GripVertical class="h-4 w-4 text-muted-foreground cursor-grab drag-handle shrink-0" />
                                    <span class="text-xs text-muted-foreground w-5 shrink-0">{{ index + 1 }}.</span>
                                    <div class="flex-1 min-w-0">
                                        <p class="text-sm font-medium truncate">{{ element.name || 'Loading...' }}</p>
                                        <p v-if="element.description" class="text-xs text-muted-foreground truncate">{{ element.description }}</p>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        class="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive"
                                        @click="removeQuestion(index)"
                                    >
                                        <Trash2 class="h-3.5 w-3.5" />
                                    </Button>
                                </div>
                            </template>
                        </draggable>
                    </ScrollArea>
                </div>

                <!-- Available Templates -->
                <div class="shrink-0 max-h-[35%] flex flex-col min-h-0">
                    <h4 class="text-sm font-medium mb-2">Available Templates</h4>
                    <div class="relative mb-2">
                        <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            v-model="searchQuery"
                            placeholder="Search templates..."
                            class="pl-9 h-9"
                        />
                    </div>
                    <div v-if="loadingTemplates" class="flex items-center justify-center py-4">
                        <Loader2 class="h-5 w-5 animate-spin text-muted-foreground" />
                    </div>
                    <ScrollArea v-else class="flex-1 border rounded-lg min-h-0">
                        <div v-if="filteredTemplates.length === 0" class="p-4 text-center">
                            <p class="text-sm text-muted-foreground">
                                {{ availableTemplates.length === 0 ? 'No evaluation templates available' : 'All templates assigned or no matches' }}
                            </p>
                        </div>
                        <div v-else class="divide-y">
                            <div
                                v-for="template in filteredTemplates"
                                :key="template.id"
                                class="flex items-center gap-2 px-3 py-2 hover:bg-muted/50"
                            >
                                <div class="flex-1 min-w-0">
                                    <p class="text-sm truncate">{{ template.evaluation_criteria || template.name }}</p>
                                    <p v-if="template.description" class="text-xs text-muted-foreground truncate">{{ template.description }}</p>
                                </div>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    class="h-7 shrink-0"
                                    @click="addQuestion(template)"
                                >
                                    <Plus class="h-3.5 w-3.5 mr-1" />
                                    Add
                                </Button>
                            </div>
                        </div>
                    </ScrollArea>
                </div>
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
