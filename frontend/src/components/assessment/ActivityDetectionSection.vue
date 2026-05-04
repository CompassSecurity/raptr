<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next';
import { computed } from 'vue';
import ActivityAssetsManager from '@/components/assessment/ActivityAssetsManager.vue';
import { Badge } from '@/components/ui/badge';
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
import { Switch } from '@/components/ui/switch';
import { usePreferencesStore } from '@/stores/preferences';
import type { ActivityRead, AssetRead } from '@/types/utils';
import { formatDateTime } from '@/utils/dateFormatter';
import { schemas } from '@/types/zod';

const props = defineProps<{
    assessmentId: string;
    uploadImage: (file: File) => Promise<string>;
    resolveImageUrl: (url: string) => Promise<string>;
    readonly?: boolean;
    availableAssets?: AssetRead[];
}>();

const emit = defineEmits<(e: 'assets-changed') => void>();

const formData = defineModel<Partial<ActivityRead>>('formData', {
    required: true,
});

const severityOptions = schemas.ActivitySeverity.options;
const preferencesStore = usePreferencesStore();

// Formatted date strings for readonly display
function readonlyDate(value: string | null | undefined): string {
    return formatDateTime(
        value,
        preferencesStore.effectiveTimezone,
        preferencesStore.dateFormat,
        preferencesStore.timeFormat,
    );
}

// Writable computed properties for detection toggles
const logged = computed({
    get: () => !!formData.value.logged,
    set: (val) => {
        const newData = { ...formData.value, logged: val };
        if (val) {
            newData.log_sources = newData.log_sources || [];
        } else {
            newData.log_time = null;
            newData.log_sources = [];
        }
        formData.value = newData;
    },
});

const alerted = computed({
    get: () => !!formData.value.alerted,
    set: (val) => {
        const newData = { ...formData.value, alerted: val };
        if (val) {
            newData.alert_sources = newData.alert_sources || [];
        } else {
            newData.alert_time = null;
            newData.alert_severity = null;
            newData.alert_sources = [];
            newData.evaluation = {
                ...newData.evaluation!,
                event_to_alert_data: '',
                event_to_alert_evaluation_result: 'n/a',
                alert_to_stakeholder_data: '',
                alert_to_stakeholder_evaluation_result: 'n/a',
                alert_severity_data: '',
                alert_severity_evaluation_result: 'n/a',
            };
        }
        formData.value = newData;
    },
});

const prevented = computed({
    get: () => !!formData.value.prevented,
    set: (val) => {
        const newData = { ...formData.value, prevented: val };
        if (val) {
            newData.prevention_sources = newData.prevention_sources || [];
        } else {
            newData.prevent_time = null;
            newData.prevention_sources = [];
        }
        formData.value = newData;
    },
});

const stakeholderNotificationCreated = computed({
    get: () => !!formData.value.stakeholder_notification_created,
    set: (val) => {
        const newData = {
            ...formData.value,
            stakeholder_notification_created: val,
        };
        if (val) {
            newData.stakeholder_notification_sources =
                newData.stakeholder_notification_sources || [];
        } else {
            newData.stakeholder_notification_time = null;
            newData.stakeholder_notification_severity = null;
            newData.stakeholder_notification_sources = [];
            newData.evaluation = {
                ...newData.evaluation!,
                alert_to_stakeholder_data: '',
                alert_to_stakeholder_evaluation_result: 'n/a',
                stakeholder_notification_severity_data: '',
                stakeholder_notification_severity_evaluation_result: 'n/a',
            };
        }
        formData.value = newData;
    },
});
</script>

<template>
    <Collapsible defaultOpen>
        <Card class="border-l-4 border-l-blue-500 shadow-sm">
            <CollapsibleTrigger as-child>
                <CardHeader class="cursor-pointer hover:bg-muted/50 transition-colors">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <CardTitle class="text-lg text-blue-700 dark:text-blue-400">Activity Detection</CardTitle>
                        </div>
                        <ChevronDown class="h-5 w-5 text-muted-foreground transition-transform duration-200 [[data-state=open]_&]:rotate-180" />
                    </div>
                </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
                <CardContent class="space-y-6 pt-6">
                    <!-- 1. Logged -->
                    <div class="space-y-4 p-4 rounded-lg border">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <Label class="text-sm font-semibold" for="switch_logged">Activity Logged</Label>
                            </div>
                            <template v-if="readonly">
                                <Badge :class="logged ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'">{{ logged ? 'Yes' : 'No' }}</Badge>
                            </template>
                            <template v-else>
                                <Switch id="switch_logged" v-model="logged" />
                            </template>
                        </div>

                        <div v-if="logged" class="space-y-4 pt-2 border-t">
                            <div class="space-y-2 w-full sm:w-1/2 pr-2">
                                <Label class="text-sm font-medium">Log Time</Label>
                                <template v-if="readonly">
                                    <div class="text-sm px-3 py-2 rounded-md border bg-muted/30 min-h-[36px] flex items-center">{{ readonlyDate(formData.log_time) }}</div>
                                </template>
                                <template v-else>
                                    <DateTimePicker
                                        :model-value="formData.log_time ?? undefined"
                                        @update:model-value="formData.log_time = $event ?? null"
                                    />
                                </template>
                            </div>
                            <ActivityAssetsManager
                                :sources="formData.log_sources ?? []"
                                :targets="[]"
                                :tools="[]"
                                @update:sources="formData.log_sources = $event"
                                @update:targets="() => {}"
                                @update:tools="() => {}"
                                :assessment-id="assessmentId"
                                :available-assets="availableAssets"
                                :show-only-sources="true"
                                sources-label="Log Sources"
                                :compact="true"
                                :readonly="readonly"
                                @assets-changed="emit('assets-changed')"
                            />
                        </div>

                        <div class="space-y-2" :class="{ 'pt-2 border-t': !logged }">
                            <MarkdownEditor :on-upload="uploadImage" :resolve-image-url="resolveImageUrl"
                                :model-value="formData.log_notes ?? ''"
                                @update:model-value="formData.log_notes = $event"
                                label="Log Notes"
                                placeholder="Document logging observations..."
                                :disabled="readonly"
                            />
                        </div>
                    </div>

                    <!-- 2. Prevented -->
                    <div class="space-y-4 p-4 rounded-lg border">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <Label class="text-sm font-semibold" for="switch_prevented">Activity Prevented</Label>
                            </div>
                            <template v-if="readonly">
                                <Badge :class="prevented ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'">{{ prevented ? 'Yes' : 'No' }}</Badge>
                            </template>
                            <template v-else>
                                <Switch id="switch_prevented" v-model="prevented" />
                            </template>
                        </div>

                        <div v-if="prevented" class="space-y-4 pt-2 border-t">
                            <div class="space-y-2 w-full sm:w-1/2 pr-2">
                                <Label class="text-sm font-medium">Prevention Time</Label>
                                <template v-if="readonly">
                                    <div class="text-sm px-3 py-2 rounded-md border bg-muted/30 min-h-[36px] flex items-center">{{ readonlyDate(formData.prevent_time) }}</div>
                                </template>
                                <template v-else>
                                    <DateTimePicker
                                        :model-value="formData.prevent_time ?? undefined"
                                        @update:model-value="formData.prevent_time = $event ?? null"
                                    />
                                </template>
                            </div>
                            <ActivityAssetsManager
                                :sources="formData.prevention_sources ?? []"
                                :targets="[]"
                                :tools="[]"
                                @update:sources="formData.prevention_sources = $event"
                                @update:targets="() => {}"
                                @update:tools="() => {}"
                                :assessment-id="assessmentId"
                                :available-assets="availableAssets"
                                :show-only-sources="true"
                                sources-label="Prevention Systems"
                                :compact="true"
                                :readonly="readonly"
                                @assets-changed="emit('assets-changed')"
                            />
                        </div>

                        <div class="space-y-2" :class="{ 'pt-2 border-t': !prevented }">
                            <MarkdownEditor :on-upload="uploadImage" :resolve-image-url="resolveImageUrl"
                                :model-value="formData.prevent_notes ?? ''"
                                @update:model-value="formData.prevent_notes = $event"
                                label="Prevention Notes"
                                placeholder="Document prevention observations..."
                                :disabled="readonly"
                            />
                        </div>
                    </div>

                    <!-- 3. Alerted -->
                    <div class="space-y-4 p-4 rounded-lg border">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <Label class="text-sm font-semibold" for="switch_alerted">Alert Generated</Label>
                            </div>
                            <template v-if="readonly">
                                <Badge :class="alerted ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'">{{ alerted ? 'Yes' : 'No' }}</Badge>
                            </template>
                            <template v-else>
                                <Switch id="switch_alerted" v-model="alerted" />
                            </template>
                        </div>

                        <div v-if="alerted" class="space-y-4 pt-2 border-t">
                            <div class="space-y-4">
                                <div class="space-y-2 w-full sm:w-1/2 pr-2">
                                    <Label class="text-sm font-medium">Alert Time</Label>
                                    <template v-if="readonly">
                                        <div class="text-sm px-3 py-2 rounded-md border bg-muted/30 min-h-[36px] flex items-center">{{ readonlyDate(formData.alert_time) }}</div>
                                    </template>
                                    <template v-else>
                                        <DateTimePicker
                                            :model-value="formData.alert_time ?? undefined"
                                            @update:model-value="formData.alert_time = $event ?? null"
                                        />
                                    </template>
                                </div>
                                <div class="space-y-2 w-full sm:w-1/2 pr-2">
                                    <Label class="text-sm font-medium">Alert Severity</Label>
                                    <template v-if="readonly">
                                        <div class="text-sm px-3 py-2 rounded-md border bg-muted/30 min-h-[36px] flex items-center">{{ formData.alert_severity || '—' }}</div>
                                    </template>
                                    <template v-else>
                                        <Select v-model="formData.alert_severity">
                                            <SelectTrigger class="w-full">
                                                <SelectValue :placeholder="formData.alert_severity || '\xa0'" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem v-for="opt in severityOptions" :key="opt" :value="opt">
                                                    {{ opt }}
                                                </SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </template>
                                </div>
                            </div>
                            <ActivityAssetsManager
                                :sources="formData.alert_sources ?? []"
                                :targets="[]"
                                :tools="[]"
                                @update:sources="formData.alert_sources = $event"
                                @update:targets="() => {}"
                                @update:tools="() => {}"
                                :assessment-id="assessmentId"
                                :available-assets="availableAssets"
                                :show-only-sources="true"
                                sources-label="Detection Systems"
                                :compact="true"
                                :readonly="readonly"
                                @assets-changed="emit('assets-changed')"
                            />
                        </div>

                        <div class="space-y-2" :class="{ 'pt-2 border-t': !alerted }">
                            <MarkdownEditor :on-upload="uploadImage" :resolve-image-url="resolveImageUrl"
                                :model-value="formData.alert_notes ?? ''"
                                @update:model-value="formData.alert_notes = $event"
                                label="Alert Notes"
                                placeholder="Document alert observations..."
                                :disabled="readonly"
                            />
                        </div>
                    </div>

                    <!-- 4. Stakeholder Notification -->
                    <div class="space-y-4 p-4 rounded-lg border">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <Label class="text-sm font-semibold" for="switch_stakeholder">Stakeholder Notification Created</Label>
                            </div>
                            <template v-if="readonly">
                                <Badge :class="stakeholderNotificationCreated ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'">{{ stakeholderNotificationCreated ? 'Yes' : 'No' }}</Badge>
                            </template>
                            <template v-else>
                                <Switch id="switch_stakeholder" v-model="stakeholderNotificationCreated" />
                            </template>
                        </div>

                        <div v-if="stakeholderNotificationCreated" class="space-y-4 pt-2 border-t">
                            <div class="space-y-4">
                                <div class="space-y-2 w-full sm:w-1/2 pr-2">
                                    <Label class="text-sm font-medium">Notification Time</Label>
                                    <template v-if="readonly">
                                        <div class="text-sm px-3 py-2 rounded-md border bg-muted/30 min-h-[36px] flex items-center">{{ readonlyDate(formData.stakeholder_notification_time) }}</div>
                                    </template>
                                    <template v-else>
                                        <DateTimePicker
                                            :model-value="formData.stakeholder_notification_time ?? undefined"
                                            @update:model-value="formData.stakeholder_notification_time = $event ?? null"
                                        />
                                    </template>
                                </div>
                                <div class="space-y-2 w-full sm:w-1/2 pr-2">
                                    <Label class="text-sm font-medium">Notification Severity</Label>
                                    <template v-if="readonly">
                                        <div class="text-sm px-3 py-2 rounded-md border bg-muted/30 min-h-[36px] flex items-center">{{ formData.stakeholder_notification_severity || '—' }}</div>
                                    </template>
                                    <template v-else>
                                        <Select v-model="formData.stakeholder_notification_severity">
                                            <SelectTrigger class="w-full">
                                                <SelectValue :placeholder="formData.stakeholder_notification_severity || '\xa0'" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem v-for="opt in severityOptions" :key="opt" :value="opt">
                                                    {{ opt }}
                                                </SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </template>
                                </div>
                            </div>
                            <ActivityAssetsManager
                                :sources="formData.stakeholder_notification_sources ?? []"
                                :targets="[]"
                                :tools="[]"
                                @update:sources="formData.stakeholder_notification_sources = $event"
                                @update:targets="() => {}"
                                @update:tools="() => {}"
                                :assessment-id="assessmentId"
                                :available-assets="availableAssets"
                                :show-only-sources="true"
                                sources-label="Notification Systems"
                                :compact="true"
                                :readonly="readonly"
                                @assets-changed="emit('assets-changed')"
                            />
                        </div>

                        <div class="space-y-2" :class="{ 'pt-2 border-t': !stakeholderNotificationCreated }">
                            <MarkdownEditor :on-upload="uploadImage" :resolve-image-url="resolveImageUrl"
                                :model-value="formData.stakeholder_notification_notes ?? ''"
                                @update:model-value="formData.stakeholder_notification_notes = $event"
                                label="Notification Notes"
                                placeholder="Document stakeholder notification details..."
                                :disabled="readonly"
                            />
                        </div>
                    </div>
                </CardContent>
            </CollapsibleContent>
        </Card>
    </Collapsible>
</template>
