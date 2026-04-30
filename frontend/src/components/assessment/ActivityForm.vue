<script setup lang="ts">
import { BookOpen, ChevronDown, Copy, History } from 'lucide-vue-next';
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { toast } from 'vue-sonner';
import ActivityAssetsManager from '@/components/assessment/ActivityAssetsManager.vue';
import ActivityAttachments from '@/components/assessment/ActivityAttachments.vue';
import ActivityDetectionSection from '@/components/assessment/ActivityDetectionSection.vue';
import ActivityEvaluation from '@/components/assessment/ActivityEvaluation.vue';
import ActivityGeneralInfo from '@/components/assessment/ActivityGeneralInfo.vue';
import ActivityHistoryModal from '@/components/assessment/ActivityHistoryModal.vue';
import ConflictResolutionDialog from '@/components/assessment/ConflictResolutionDialog.vue';
import KnowledgeBaseModal from '@/components/assessment/KnowledgeBaseModal.vue';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from '@/components/ui/collapsible';
import DateTimePicker from '@/components/ui/DateTimePicker.vue';
import { Label } from '@/components/ui/label';
import MarkdownEditor from '@/components/ui/MarkdownEditor.vue';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import { useActivityEvaluation } from '@/composables/useActivityEvaluation';
import {
    activityGroupService,
    activityService,
} from '@/services/activityService';
import { api } from '@/services/api';
import { assetService } from '@/services/assetService';
import { evaluationTemplateService } from '@/services/evaluationTemplateService';
import { fileService } from '@/services/fileService';
import { tagService } from '@/services/tagService';
import type {
    AclRole,
    ActivityGroupRead,
    ActivityRead,
    AssetRead,
    TagRead,
} from '@/types/utils';
import { schemas } from '@/types/zod';

const props = defineProps<{
    activity: ActivityRead;
    assessmentId: string;
    role?: AclRole | null;
}>();

const emit = defineEmits<{
    (e: 'saved'): void;
    (e: 'cloned', activityId: string): void;
}>();

const saving = ref(false);

// Role-based restrictions
const BLUE_EDITABLE_STATES = ['Waiting Blue', 'Waiting Red'];

const isSpectator = computed(() => props.role === 'spectator');
const isBlue = computed(() => props.role === 'blue');
const blueCanEdit = computed(
    () =>
        isBlue.value &&
        BLUE_EDITABLE_STATES.includes(formData.value.state as string),
);

// Per-section readonly flags
const generalReadonly = computed(() => isSpectator.value || isBlue.value);
const stateEditable = computed(() => blueCanEdit.value);
const redTeamReadonly = computed(() => isSpectator.value || isBlue.value);
const detectionReadonly = computed(
    () => isSpectator.value || (isBlue.value && !blueCanEdit.value),
);
const evaluationReadonly = computed(() => isSpectator.value || isBlue.value);
const attachmentsReadonly = computed(() => isSpectator.value || isBlue.value);
const tagsReadonly = computed(
    () => isSpectator.value || (isBlue.value && !blueCanEdit.value),
);

// Save button logic
const showSaveButton = computed(() => !isSpectator.value);
const saveDisabledHint = computed(() => {
    if (isBlue.value && !blueCanEdit.value) {
        return `Activity must be in "${BLUE_EDITABLE_STATES.join('" or "')}" state to edit`;
    }
    return '';
});
// State dropdown options for header
const BLUE_STATE_OPTIONS = ['Waiting Red', 'Waiting Blue'];
const headerStateOptions = computed(() => {
    if (stateEditable.value) return BLUE_STATE_OPTIONS;
    return schemas.ActivityState.options;
});
const headerStateDisabled = computed(
    () => isSpectator.value || (isBlue.value && !stateEditable.value),
);

const showKBModal = ref(false);
const showHistoryModal = ref(false);
const attachmentRefreshKey = ref(0);

// Local state for the form
const formData = ref<Partial<ActivityRead>>({});
const originalData = ref<Partial<ActivityRead>>({}); // Snapshot for 3-way merge

// Conflict resolution state
const showConflictDialog = ref(false);
const serverConflictVersion = ref<ActivityRead | null>(null);

// Supporting data
const availableActivityGroups = ref<ActivityGroupRead[]>([]);
const availableTags = ref<TagRead[]>([]);
const availableAssets = ref<AssetRead[]>([]);

// Evaluation composable (parent needs evaluationPayload for save)
const { evaluationPayload } = useActivityEvaluation(formData);

// Template names for dynamic question conflict display
const evaluationTemplateNames = ref<Map<string, string>>(new Map());

// Build display lookups for conflict dialog (resolve IDs to names)
const conflictDisplayLookups = computed(() => {
    const groupMap = new Map<string, string>();
    for (const g of availableActivityGroups.value) {
        groupMap.set(String(g.id), g.name);
    }
    return { activity_group_id: groupMap };
});

// Initialize form data
watch(
    () => props.activity,
    (newVal) => {
        if (newVal) {
            // Smart Update: If we are already editing this activity, only update specific fields
            // that might have changed externally (e.g. via modals) without overwriting user's unsaved text
            if (formData.value.id === newVal.id) {
                // Update dynamic questions
                if (formData.value.evaluation && newVal.evaluation) {
                    const newQuestions =
                        newVal.evaluation.dynamic_questions || [];
                    const currentQuestions =
                        formData.value.evaluation.dynamic_questions || [];

                    formData.value.evaluation.dynamic_questions =
                        newQuestions.map((newQ: any) => {
                            const existingQ = currentQuestions.find(
                                (oldQ: any) =>
                                    oldQ.evaluation_template_id ===
                                    newQ.evaluation_template_id,
                            );
                            if (existingQ) {
                                return {
                                    ...newQ,
                                    data: existingQ.data,
                                    evaluation_result:
                                        existingQ.evaluation_result,
                                };
                            }
                            return newQ;
                        });
                }

                // Update KB articles
                formData.value.linked_knowledge_base_articles = JSON.parse(
                    JSON.stringify(newVal.linked_knowledge_base_articles || []),
                );

                // Always sync updated_at so the next save sends the correct version
                formData.value.updated_at = newVal.updated_at;

                // Refresh original snapshot so conflict detection compares against the latest saved state
                originalData.value = JSON.parse(JSON.stringify(newVal));
                return;
            }

            // Full Initialization (Switching activities or first load)
            formData.value = JSON.parse(JSON.stringify(newVal));
            originalData.value = JSON.parse(JSON.stringify(newVal)); // Save original snapshot
            // Ensure arrays are initialized
            formData.value.sources = formData.value.sources || [];
            formData.value.targets = formData.value.targets || [];
            formData.value.tools = formData.value.tools || [];
            formData.value.tags = formData.value.tags || [];
            formData.value.alert_sources = formData.value.alert_sources || [];
            formData.value.prevention_sources =
                formData.value.prevention_sources || [];
            formData.value.stakeholder_notification_sources =
                formData.value.stakeholder_notification_sources || [];
            formData.value.log_sources = formData.value.log_sources || [];
            // Ensure booleans are properly initialized (API might send null)
            formData.value.logged = formData.value.logged ?? false;
            formData.value.alerted = formData.value.alerted ?? false;
            formData.value.prevented = formData.value.prevented ?? false;
            formData.value.stakeholder_notification_created =
                formData.value.stakeholder_notification_created ?? false;
        }
    },
    { immediate: true, deep: true },
);

// Fetch supporting data
onMounted(async () => {
    try {
        const [groupsRes, tagsRes, assetsRes] = await Promise.all([
            activityGroupService.getGroups(props.assessmentId),
            tagService.getTags(props.assessmentId, { limit: 1000 }),
            assetService.getAssets(props.assessmentId, { limit: 1000 }),
        ]);
        availableActivityGroups.value = groupsRes.filter((g) => !g.deleted);
        availableTags.value = tagsRes.items;
        availableAssets.value = assetsRes.items;
    } catch (e) {
        console.error('Failed to fetch supporting data', e);
    }
});

// Tag creation handler from child
function handleTagCreated(tag: TagRead) {
    availableTags.value.push(tag);
}

// Asset list changed handler from child
async function handleAssetsChanged() {
    try {
        const data = await assetService.getAssets(props.assessmentId, {
            limit: 1000,
        });
        availableAssets.value = data.items;
    } catch (e) {
        console.error('Failed to refresh assets', e);
    }
}

// Dynamic questions updated handler from child
async function handleDynamicQuestionsUpdated() {
    emit('saved');
}

// Markdown editor image upload — returns the download URL for embedding
async function uploadImageForMarkdown(file: File): Promise<string> {
    if (!props.activity.id) throw new Error('No activity ID');
    const result = await fileService.uploadFile(
        props.assessmentId,
        props.activity.id,
        file,
    );
    attachmentRefreshKey.value++;
    return result.url;
}

// Resolve API image URLs to blob URLs with auth
async function resolveImageUrl(url: string): Promise<string> {
    const apiPath = url.replace(/^\/api\/v1/, '');
    const response = await api.get(apiPath, { responseType: 'blob' });
    return URL.createObjectURL(response.data);
}

async function handleSave() {
    if (!formData.value.id || !formData.value.name) return;

    saving.value = true;
    try {
        const activityId = formData.value.id;

        const updatePayload = {
            ...formData.value,
            mitre_tactic: formData.value.mitre_tactic || '',
            mitre_technique: formData.value.mitre_technique || '',
            activity_start_time: formData.value.activity_start_time || null,
            activity_end_time: formData.value.activity_end_time || null,
            prevent_time: formData.value.prevent_time || null,
            alert_time: formData.value.alert_time || null,
            stakeholder_notification_time:
                formData.value.stakeholder_notification_time || null,
            log_time: formData.value.log_time || null,
            provider: formData.value.provider || '',
            visible: formData.value.visible || false,
            logged: formData.value.logged || false,
            prevented: formData.value.prevented || false,
            alerted: formData.value.alerted || false,
            stakeholder_notification_created:
                formData.value.stakeholder_notification_created || false,
            expected_logging: formData.value.expected_logging || false,
            expected_prevention: formData.value.expected_prevention || false,
            expected_alert_creation:
                formData.value.expected_alert_creation || false,
            expected_stakeholder_notification:
                formData.value.expected_stakeholder_notification || false,
            priority: formData.value.priority || null,
            state: formData.value.state || 'Pending',
            expected_severity: formData.value.expected_severity || null,
            alert_severity: formData.value.alert_severity || null,
            stakeholder_notification_severity:
                formData.value.stakeholder_notification_severity || null,
            activity_rationale: formData.value.activity_rationale || '',
            activity_requirements: formData.value.activity_requirements || '',
            activity_actions: formData.value.activity_actions || '',
            activity_notes: formData.value.activity_notes || '',
            log_notes: formData.value.log_notes || '',
            alert_notes: formData.value.alert_notes || '',
            prevent_notes: formData.value.prevent_notes || '',
            stakeholder_notification_notes:
                formData.value.stakeholder_notification_notes || '',
            tags: (formData.value.tags || []).map((t) => t.id),
            activity_group_id: formData.value.activity_group_id || null,
            sources: (formData.value.sources || []).map((a) => a.id),
            targets: (formData.value.targets || []).map((a) => a.id),
            tools: (formData.value.tools || []).map((a) => a.id),
            prevention_sources: (formData.value.prevention_sources || []).map(
                (a) => a.id,
            ),
            alert_sources: (formData.value.alert_sources || []).map(
                (a) => a.id,
            ),
            stakeholder_notification_sources: (
                formData.value.stakeholder_notification_sources || []
            ).map((a) => a.id),
            log_sources: (formData.value.log_sources || []).map((a) => a.id),
            evaluation: evaluationPayload.value,
        };

        await activityService.updateActivity(
            props.assessmentId,
            activityId,
            updatePayload as any,
        );

        toast.success('Activity updated successfully');
        emit('saved');
    } catch (error) {
        const axiosError = error as any;
        if (axiosError?.response?.status === 409) {
            // Fetch latest server version for conflict resolution
            try {
                const latest = await activityService.getActivity(
                    props.assessmentId,
                    formData.value.id!,
                );

                // Fetch template names for dynamic questions so the conflict dialog can show them
                const allQuestions = [
                    ...(formData.value.evaluation?.dynamic_questions || []),
                    ...(latest.evaluation?.dynamic_questions || []),
                ] as any[];
                const templateIds = [
                    ...new Set(
                        allQuestions
                            .map((q: any) => q.evaluation_template_id)
                            .filter(Boolean),
                    ),
                ];
                const nameMap = new Map<string, string>();
                await Promise.all(
                    templateIds.map(async (id: string) => {
                        try {
                            const tmpl =
                                await evaluationTemplateService.getById(id);
                            nameMap.set(id, tmpl.name);
                        } catch {
                            /* ignore */
                        }
                    }),
                );
                evaluationTemplateNames.value = nameMap;

                // Enrich question objects with name so conflict labels are readable
                const enrichQuestions = (qs: any[]) =>
                    qs.map((q: any) => ({
                        ...q,
                        name: nameMap.get(q.evaluation_template_id) || q.name,
                    }));
                if (formData.value.evaluation?.dynamic_questions) {
                    formData.value.evaluation = {
                        ...formData.value.evaluation,
                        dynamic_questions: enrichQuestions(
                            formData.value.evaluation
                                .dynamic_questions as any[],
                        ),
                    };
                }
                if (latest.evaluation?.dynamic_questions) {
                    latest.evaluation = {
                        ...latest.evaluation,
                        dynamic_questions: enrichQuestions(
                            latest.evaluation.dynamic_questions as any[],
                        ),
                    } as any;
                }
                if (originalData.value.evaluation?.dynamic_questions) {
                    originalData.value.evaluation = {
                        ...originalData.value.evaluation,
                        dynamic_questions: enrichQuestions(
                            originalData.value.evaluation
                                .dynamic_questions as any[],
                        ),
                    } as any;
                }

                serverConflictVersion.value = latest;
                showConflictDialog.value = true;
            } catch (fetchErr) {
                console.error(
                    'Failed to fetch latest activity for merge',
                    fetchErr,
                );
                toast.error(
                    'Conflict detected but failed to load latest version',
                );
            }
        } else {
            console.error(error);
            toast.error('Failed to update activity');
        }
    } finally {
        saving.value = false;
    }
}

async function handleConflictResolved(
    mergedData: Record<string, unknown>,
    newUpdatedAt: string,
) {
    showConflictDialog.value = false;

    // Apply merged scalar fields to formData
    for (const [key, value] of Object.entries(mergedData)) {
        (formData.value as Record<string, unknown>)[key] = value;
    }
    // Update updated_at to the server's latest so the retry passes concurrency check
    formData.value.updated_at = newUpdatedAt;

    // Update original snapshot to the server version so future saves work correctly
    if (serverConflictVersion.value) {
        originalData.value = JSON.parse(
            JSON.stringify(serverConflictVersion.value),
        );
    }

    // Wait for Vue watchers (tag name sync in ActivityGeneralInfo) to settle
    await nextTick();

    // Retry save with merged data
    await handleSave();
}

const isCloning = ref(false);
async function handleCloneActivity() {
    if (!formData.value.id || isCloning.value) return;

    isCloning.value = true;
    try {
        const clonedActivity = await activityService.cloneActivity(
            props.assessmentId,
            formData.value.id,
        );
        toast.success('Activity cloned successfully');
        emit('cloned', clonedActivity.id);
    } catch (error: any) {
        toast.error('Failed to clone activity');
        console.error(error);
    } finally {
        isCloning.value = false;
    }
}
</script>

<template>
    <div class="w-full px-4 mx-auto space-y-8 pb-24">
        <!-- Sticky Header -->
        <div class="sticky top-0 z-10 bg-background pb-4 border-b">
            <div class="flex justify-between items-start pt-2">
                <div>
                    <h2 class="text-3xl font-bold tracking-tight">{{ formData.name || 'Activity Details' }}</h2>
                    <p class="text-sm text-muted-foreground mt-1" v-if="formData.mitre_tactic || formData.mitre_technique">
                        <span v-if="formData.mitre_tactic">{{ formData.mitre_tactic }}</span>
                        <span v-if="formData.mitre_tactic && formData.mitre_technique"> • </span>
                        <span v-if="formData.mitre_technique">{{ formData.mitre_technique }}</span>
                    </p>
                </div>
                <div class="flex items-center gap-2">
                    <Select
                        :model-value="formData.state ?? undefined"
                        @update:model-value="formData.state = $event as any"
                        :disabled="headerStateDisabled"
                    >
                        <SelectTrigger class="w-[160px]">
                            <SelectValue :placeholder="formData.state ?? '\xa0'" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem v-for="opt in headerStateOptions" :key="opt" :value="opt">
                                {{ opt }}
                            </SelectItem>
                        </SelectContent>
                    </Select>
                    <Button v-if="!isSpectator && !isBlue" variant="outline" size="lg" @click="showKBModal = true">
                        <BookOpen class="mr-2 h-4 w-4" />
                        Knowledge Base
                    </Button>
                    <Button v-if="!isSpectator && !isBlue && formData.id" variant="outline" size="lg" @click="showHistoryModal = true">
                        <History class="mr-2 h-4 w-4" />
                        History
                    </Button>
                    <Button v-if="!isSpectator && !isBlue && formData.id" variant="outline" size="lg" @click="handleCloneActivity" :disabled="isCloning">
                        <Copy class="mr-2 h-4 w-4" />
                        Clone Activity
                    </Button>
                    <div v-if="showSaveButton">
                        <TooltipProvider v-if="saveDisabledHint">
                            <Tooltip>
                                <TooltipTrigger as-child>
                                    <span tabindex="0">
                                        <Button @click="handleSave" :disabled="true" size="lg">
                                            Save Changes
                                        </Button>
                                    </span>
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p>{{ saveDisabledHint }}</p>
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                        <Button v-else @click="handleSave" :disabled="saving" size="lg">
                            <span v-if="!saving">Save Changes</span>
                            <span v-else class="flex items-center gap-2">
                                <span class="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
                                Saving...
                            </span>
                        </Button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Form Content (disabled override applies here, not to the header) -->
        <div class="form-content space-y-8">
        <ActivityGeneralInfo
            v-model:form-data="formData"
            :assessment-id="assessmentId"
            :available-activity-groups="availableActivityGroups"
            :available-tags="availableTags"
            :upload-image="uploadImageForMarkdown"
            :resolve-image-url="resolveImageUrl"
            :readonly="generalReadonly"
            :tags-readonly="tagsReadonly"
            :state-editable="stateEditable"
            @tag-created="handleTagCreated"
        />

        <!-- Red Team / Activity Details -->
        <Collapsible defaultOpen>
            <Card class="border-l-4 border-l-red-500 shadow-sm">
                <CollapsibleTrigger as-child>
                    <CardHeader class="cursor-pointer hover:bg-muted/50 transition-colors">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <CardTitle class="text-lg text-red-700 dark:text-red-400">Activity Details</CardTitle>
                            </div>
                            <ChevronDown class="h-5 w-5 text-muted-foreground transition-transform duration-200 [[data-state=open]_&]:rotate-180" />
                        </div>
                    </CardHeader>
                </CollapsibleTrigger>
                <CollapsibleContent>
                    <CardContent class="space-y-6">
                    <ActivityAssetsManager
                        :sources="formData.sources ?? []"
                        :targets="formData.targets ?? []"
                        :tools="formData.tools ?? []"
                        @update:sources="formData.sources = $event"
                        @update:targets="formData.targets = $event"
                        @update:tools="formData.tools = $event"
                        :assessment-id="assessmentId"
                        :available-assets="availableAssets"
                        :readonly="redTeamReadonly"
                        @assets-changed="handleAssetsChanged"
                    />

                    <div class="border-t pt-6"></div>

                    <div class="space-y-3">
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div class="space-y-2">
                                <Label class="text-sm font-medium">Start Time</Label>
                                <DateTimePicker
                                    :model-value="formData.activity_start_time ?? undefined"
                                    @update:model-value="formData.activity_start_time = $event ?? null"
                                    :disabled="redTeamReadonly"
                                />
                            </div>
                            <div class="space-y-2">
                                <Label class="text-sm font-medium">End Time</Label>
                                <DateTimePicker
                                    :model-value="formData.activity_end_time ?? undefined"
                                    @update:model-value="formData.activity_end_time = $event ?? null"
                                    :disabled="redTeamReadonly"
                                />
                            </div>
                        </div>
                    </div>
                    <div class="border-t pt-6"></div>
                    <div class="space-y-2">
                        <MarkdownEditor :on-upload="uploadImageForMarkdown" :resolve-image-url="resolveImageUrl"
                            :model-value="formData.activity_actions ?? ''"
                            @update:model-value="formData.activity_actions = $event"
                            label="Activity Actions"
                            placeholder="Describe the actions taken during this activity"
                            :disabled="redTeamReadonly"
                        />
                    </div>
                    <div class="space-y-2">
                        <MarkdownEditor :on-upload="uploadImageForMarkdown" :resolve-image-url="resolveImageUrl"
                            :model-value="formData.activity_notes ?? ''"
                            @update:model-value="formData.activity_notes = $event"
                            label="Activity Notes"
                            placeholder="Additional notes or observations"
                            :disabled="redTeamReadonly"
                        />
                    </div>
                    </CardContent>
                </CollapsibleContent>
            </Card>
        </Collapsible>

        <!-- Blue Team Detection -->
        <ActivityDetectionSection
            v-model:form-data="formData"
            :assessment-id="assessmentId"
            :upload-image="uploadImageForMarkdown"
            :resolve-image-url="resolveImageUrl"
            :readonly="detectionReadonly"
            :available-assets="availableAssets"
            @assets-changed="handleAssetsChanged"
        />

        <!-- Evaluation & Metrics -->
        <ActivityEvaluation
            v-model:form-data="formData"
            :assessment-id="assessmentId"
            :activity-id="formData.id ?? ''"
            :upload-image="uploadImageForMarkdown"
            :resolve-image-url="resolveImageUrl"
            :readonly="evaluationReadonly"
            @questions-updated="handleDynamicQuestionsUpdated"
        />

        <!-- Attachments -->
        <ActivityAttachments
            :assessment-id="assessmentId"
            :activity-id="formData.id ?? ''"
            :refresh-key="attachmentRefreshKey"
            :readonly="attachmentsReadonly"
        />
        </div>
    </div>

    <KnowledgeBaseModal
        v-model:open="showKBModal"
        :linked-articles="formData.linked_knowledge_base_articles || []"
        :mitre-technique-id="formData.mitre_technique"
        :assessment-id="assessmentId"
    />

    <ConflictResolutionDialog
        v-if="serverConflictVersion"
        v-model:open="showConflictDialog"
        :my-version="formData"
        :server-version="serverConflictVersion"
        :original-version="originalData"
        :display-lookups="conflictDisplayLookups"
        @resolved="handleConflictResolved"
        @cancel="showConflictDialog = false"
    />

    <ActivityHistoryModal
        v-if="formData.id"
        v-model:open="showHistoryModal"
        :assessment-id="assessmentId"
        :activity-id="formData.id"
    />
</template>

<style scoped>
/* Override disabled opacity so readonly fields remain fully readable and selectable.
   Scoped to .form-content so the save button retains its normal disabled appearance. */
.form-content :deep([disabled]),
.form-content :deep([data-disabled]),
.form-content :deep([data-disabled=true]) {
    opacity: 1 !important;
    cursor: default !important;
}
</style>
