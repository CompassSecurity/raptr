<script setup lang="ts">
import { ChevronDown, Settings2 } from '@lucide/vue';
import { computed, ref, watch } from 'vue';
import ManageDynamicQuestionsModal from '@/components/assessment/ManageDynamicQuestionsModal.vue';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from '@/components/ui/collapsible';
import EvalResultToggle from '@/components/ui/EvalResultToggle.vue';
import { Label } from '@/components/ui/label';
import MarkdownEditor from '@/components/ui/MarkdownEditor.vue';
import type { EvalResult } from '@/composables/useActivityEvaluation';
import {
    evalBadgeClass,
    useActivityEvaluation,
} from '@/composables/useActivityEvaluation';
import { evaluationTemplateService } from '@/services/evaluationTemplateService';
import type { ActivityRead, EvaluationTemplateRead } from '@/types/utils';

const props = defineProps<{
    assessmentId: string;
    activityId: string;
    uploadImage: (file: File) => Promise<string>;
    resolveImageUrl: (url: string) => Promise<string>;
    readonly?: boolean;
}>();

const emit = defineEmits<(e: 'questions-updated') => void>();

const formData = defineModel<Partial<ActivityRead>>('formData', {
    required: true,
});

const showDynamicQuestionsModal = ref(false);

// Evaluation composable
const {
    loggedEvaluation,
    preventedEvaluation,
    alertedEvaluation,
    stakeholderNotifiedEvaluation,
    activityCoverageScore,
    eventToAlertEvalStatus,
    alertToStakeholderEvalStatus,
    alertSeverityEvalStatus,
    stakeholderSeverityEvalStatus,
} = useActivityEvaluation(formData);

// Dynamic questions
const evaluationTemplates = ref<Record<string, EvaluationTemplateRead>>({});
const loadingTemplates = ref(false);

const sortedDynamicQuestions = computed(() => {
    const questions = formData.value.evaluation?.dynamic_questions || [];
    return [...questions].sort(
        (a: any, b: any) => (a.position ?? 0) - (b.position ?? 0),
    );
});

async function fetchEvaluationTemplates() {
    const questions = formData.value.evaluation?.dynamic_questions || [];
    if (questions.length === 0) return;

    const missingIds = questions
        .map((q: any) => q.evaluation_template_id)
        .filter((id: string) => id && !evaluationTemplates.value[id]);

    if (missingIds.length === 0) return;

    loadingTemplates.value = true;
    try {
        for (const id of missingIds) {
            const template = await evaluationTemplateService.getById(id);
            evaluationTemplates.value[id] = template;
        }
    } catch (e) {
        console.error('Failed to fetch evaluation templates:', e);
    } finally {
        loadingTemplates.value = false;
    }
}

watch(
    () => formData.value.evaluation?.dynamic_questions,
    () => {
        fetchEvaluationTemplates();
    },
    { immediate: true, deep: true },
);

function updateDynamicQuestion(templateId: string, field: string, value: any) {
    if (!formData.value.evaluation) return;
    const questions = [
        ...(formData.value.evaluation.dynamic_questions || []),
    ] as any[];
    const idx = questions.findIndex(
        (q: any) => q.evaluation_template_id === templateId,
    );
    if (idx >= 0) {
        questions[idx] = { ...questions[idx], [field]: value };
        formData.value.evaluation = {
            ...formData.value.evaluation,
            dynamic_questions: questions,
        };
    }
}

async function handleDynamicQuestionsUpdated() {
    emit('questions-updated');
}
</script>

<template>
    <Collapsible defaultOpen>
        <Card class="border-l-4 border-l-purple-500 shadow-sm">
            <CollapsibleTrigger as-child>
                <CardHeader class="cursor-pointer hover:bg-muted/50 transition-colors">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <CardTitle class="text-lg">Evaluation & Metrics</CardTitle>
                        </div>
                        <ChevronDown class="h-5 w-5 text-muted-foreground transition-transform duration-200 [[data-state=open]_&]:rotate-180" />
                    </div>
                </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
                <CardContent class="space-y-8 pt-6">
                    <!-- Section 1: Detection Evaluation -->
                    <div class="space-y-6">
                        <h3 class="text-sm font-semibold">Detection Evaluation</h3>

                        <!-- 4 Evaluation Badges -->
                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            <div class="flex flex-col items-center gap-2 p-4 rounded-lg border text-center">
                                <span class="text-xs font-medium text-muted-foreground">Logged</span>
                                <Badge :class="evalBadgeClass(loggedEvaluation)">{{ loggedEvaluation }}</Badge>
                            </div>
                            <div class="flex flex-col items-center gap-2 p-4 rounded-lg border text-center">
                                <span class="text-xs font-medium text-muted-foreground">Prevented</span>
                                <Badge :class="evalBadgeClass(preventedEvaluation)">{{ preventedEvaluation }}</Badge>
                            </div>
                            <div class="flex flex-col items-center gap-2 p-4 rounded-lg border text-center">
                                <span class="text-xs font-medium text-muted-foreground">Alerted</span>
                                <Badge :class="evalBadgeClass(alertedEvaluation)">{{ alertedEvaluation }}</Badge>
                            </div>
                            <div class="flex flex-col items-center gap-2 p-4 rounded-lg border text-center">
                                <span class="text-xs font-medium text-muted-foreground">Stakeholder Notified</span>
                                <Badge :class="evalBadgeClass(stakeholderNotifiedEvaluation)">{{ stakeholderNotifiedEvaluation }}</Badge>
                            </div>
                        </div>

                        <!-- Coverage Score -->
                        <div class="p-4 rounded-lg border">
                            <div class="flex items-center justify-between">
                                <div>
                                    <span class="text-sm font-medium">Activity Coverage Score</span>
                                    <p class="text-xs text-muted-foreground mt-0.5">Based on expected outcomes vs actual results</p>
                                </div>
                                <div class="text-3xl font-bold" :class="{
                                    'text-green-600': activityCoverageScore === 100,
                                    'text-yellow-500': activityCoverageScore >= 25 && activityCoverageScore < 100,
                                    'text-red-600': activityCoverageScore < 25,
                                }">
                                    {{ activityCoverageScore }}%
                                </div>
                            </div>
                        </div>

                        <div class="border-t"></div>

                        <!-- Time-based Evaluations -->
                        <h3 class="text-sm font-semibold">Timing & Severity Evaluation</h3>

                        <!-- Event to Alert -->
                        <div class="space-y-3 p-4 rounded-lg border">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <Label class="text-sm font-medium">Event to Alert Time</Label>
                                    <Badge :class="evalBadgeClass(eventToAlertEvalStatus)">{{ eventToAlertEvalStatus }}</Badge>
                                </div>
                                <EvalResultToggle
                                    v-if="!readonly"
                                    :model-value="(formData.evaluation as any)?.event_to_alert_evaluation_result || 'n/a'"
                                    @update:model-value="formData.evaluation = { ...formData.evaluation!, ['event_to_alert_evaluation_result']: $event as any }"
                                />
                            </div>
                            <MarkdownEditor :on-upload="uploadImage" :resolve-image-url="resolveImageUrl"
                                :model-value="formData.evaluation?.event_to_alert_data ?? ''"
                                @update:model-value="formData.evaluation = { ...formData.evaluation!, event_to_alert_data: $event }"
                                placeholder="Set End Time and Alert Time to auto-calculate, or enter manually"
                                :disabled="readonly"
                            />
                        </div>

                        <!-- Alert to Stakeholder -->
                        <div class="space-y-3 p-4 rounded-lg border">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <Label class="text-sm font-medium">Alert to Stakeholder Notification Time</Label>
                                    <Badge :class="evalBadgeClass(alertToStakeholderEvalStatus)">{{ alertToStakeholderEvalStatus }}</Badge>
                                </div>
                                <EvalResultToggle
                                    v-if="!readonly"
                                    :model-value="(formData.evaluation as any)?.alert_to_stakeholder_evaluation_result || 'n/a'"
                                    @update:model-value="formData.evaluation = { ...formData.evaluation!, ['alert_to_stakeholder_evaluation_result']: $event as any }"
                                />
                            </div>
                            <MarkdownEditor :on-upload="uploadImage" :resolve-image-url="resolveImageUrl"
                                :model-value="formData.evaluation?.alert_to_stakeholder_data ?? ''"
                                @update:model-value="formData.evaluation = { ...formData.evaluation!, alert_to_stakeholder_data: $event }"
                                placeholder="Set Alert Time and Notification Time to auto-calculate, or enter manually"
                                :disabled="readonly"
                            />
                        </div>

                        <!-- Alert Severity -->
                        <div class="space-y-3 p-4 rounded-lg border">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <Label class="text-sm font-medium">Alert Severity Evaluation</Label>
                                    <Badge :class="evalBadgeClass(alertSeverityEvalStatus)">{{ alertSeverityEvalStatus }}</Badge>
                                </div>
                                <EvalResultToggle
                                    v-if="!readonly"
                                    :model-value="(formData.evaluation as any)?.alert_severity_evaluation_result || 'n/a'"
                                    @update:model-value="formData.evaluation = { ...formData.evaluation!, ['alert_severity_evaluation_result']: $event as any }"
                                />
                            </div>
                            <MarkdownEditor :on-upload="uploadImage" :resolve-image-url="resolveImageUrl"
                                :model-value="formData.evaluation?.alert_severity_data ?? ''"
                                @update:model-value="formData.evaluation = { ...formData.evaluation!, alert_severity_data: $event }"
                                placeholder="Set Expected Severity and Alert Severity to auto-populate, or enter manually"
                                :disabled="readonly"
                            />
                        </div>

                        <!-- Stakeholder Notification Severity -->
                        <div class="space-y-3 p-4 rounded-lg border">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <Label class="text-sm font-medium">Stakeholder Notification Severity Evaluation</Label>
                                    <Badge :class="evalBadgeClass(stakeholderSeverityEvalStatus)">{{ stakeholderSeverityEvalStatus }}</Badge>
                                </div>
                                <EvalResultToggle
                                    v-if="!readonly"
                                    :model-value="(formData.evaluation as any)?.stakeholder_notification_severity_evaluation_result || 'n/a'"
                                    @update:model-value="formData.evaluation = { ...formData.evaluation!, ['stakeholder_notification_severity_evaluation_result']: $event as any }"
                                />
                            </div>
                            <MarkdownEditor :on-upload="uploadImage" :resolve-image-url="resolveImageUrl"
                                :model-value="formData.evaluation?.stakeholder_notification_severity_data ?? ''"
                                @update:model-value="formData.evaluation = { ...formData.evaluation!, stakeholder_notification_severity_data: $event }"
                                placeholder="Set Expected Severity and Notification Severity to auto-populate, or enter manually"
                                :disabled="readonly"
                            />
                        </div>
                    </div>

                    <div class="border-t"></div>

                    <!-- Section 2: Dynamic Template Questions -->
                    <div class="space-y-4">
                        <div class="flex items-center justify-between">
                            <h3 class="text-sm font-semibold">Template Questions</h3>
                            <Button v-if="!readonly" variant="outline" size="sm" class="h-7 text-xs" @click="showDynamicQuestionsModal = true">
                                <Settings2 class="h-3.5 w-3.5 mr-1" />
                                Manage Questions
                            </Button>
                        </div>
                        <div v-if="sortedDynamicQuestions.length === 0" class="p-6 border border-dashed rounded-lg bg-muted/30 text-center">
                            <p class="text-sm text-muted-foreground">No dynamic evaluation questions assigned to this activity</p>
                        </div>
                        <div v-else class="space-y-3">
                            <div
                                v-for="question in sortedDynamicQuestions"
                                :key="question.evaluation_template_id"
                                class="space-y-3 p-4 rounded-lg border"
                            >
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center gap-2">
                                        <Label class="text-sm font-medium">
                                            {{ evaluationTemplates[question.evaluation_template_id]?.evaluation_criteria || 'Loading...' }}
                                        </Label>
                                        <Badge :class="evalBadgeClass((question.evaluation_result || 'n/a').toUpperCase() as EvalResult)">
                                            {{ (question.evaluation_result || 'n/a').toUpperCase() }}
                                        </Badge>
                                    </div>
                                    <EvalResultToggle
                                        v-if="!readonly"
                                        :model-value="question.evaluation_result || 'n/a'"
                                        @update:model-value="updateDynamicQuestion(question.evaluation_template_id, 'evaluation_result', $event)"
                                    />
                                </div>
                                <p v-if="evaluationTemplates[question.evaluation_template_id]?.description" class="text-xs text-muted-foreground">
                                    {{ evaluationTemplates[question.evaluation_template_id]?.description }}
                                </p>
                                <MarkdownEditor :on-upload="uploadImage" :resolve-image-url="resolveImageUrl"
                                    :model-value="question.data ?? ''"
                                    @update:model-value="updateDynamicQuestion(question.evaluation_template_id, 'data', $event)"
                                    placeholder="Enter result data..."
                                    :disabled="readonly"
                                />
                            </div>
                        </div>
                    </div>
                </CardContent>
            </CollapsibleContent>
        </Card>
    </Collapsible>

    <ManageDynamicQuestionsModal
        v-model:open="showDynamicQuestionsModal"
        :assessment-id="assessmentId"
        :activity-id="activityId"
        :current-questions="(formData.evaluation?.dynamic_questions as any) ?? []"
        @success="handleDynamicQuestionsUpdated"
    />
</template>
