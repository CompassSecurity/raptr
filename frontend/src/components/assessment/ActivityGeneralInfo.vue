<script setup lang="ts">
import { ChevronDown } from '@lucide/vue';
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { toast } from 'vue-sonner';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import MarkdownEditor from '@/components/ui/MarkdownEditor.vue';
import ReadonlyField from '@/components/ui/ReadonlyField.vue';
import SearchableSelect from '@/components/ui/SearchableSelect.vue';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
    TagsInput,
    TagsInputInput,
    TagsInputItem,
    TagsInputItemDelete,
    TagsInputItemText,
} from '@/components/ui/tags-input';
import { useMitre } from '@/composables/useMitre';
import { tagService } from '@/services/tagService';
import type { ActivityGroupRead, ActivityRead, TagRead } from '@/types/utils';
import {
    zActivityPriority,
    zActivityState,
    zActivitySeverity,
} from '@/types/zod.gen';

const props = defineProps<{
    assessmentId: string;
    availableActivityGroups: ActivityGroupRead[];
    availableTags: TagRead[];
    uploadImage: (file: File) => Promise<string>;
    resolveImageUrl: (url: string) => Promise<string>;
    readonly?: boolean;
    tagsReadonly?: boolean;
    stateEditable?: boolean;
}>();

const emit = defineEmits<(e: 'tag-created', tag: TagRead) => void>();

const formData = defineModel<Partial<ActivityRead>>('formData', {
    required: true,
});

// MITRE data
const { getTechniqueOptions, getTacticOptionsForTechnique } = useMitre();

// Schema options
const priorityOptions = zActivityPriority.options;
const stateOptions = zActivityState.options;
const severityOptions = zActivitySeverity.options;

// When stateEditable is true (blue team), limit to blue-allowed states
const BLUE_STATE_OPTIONS = ['Waiting Red', 'Waiting Blue'];
const availableStateOptions = computed(() => {
    if (props.stateEditable) return BLUE_STATE_OPTIONS;
    return stateOptions;
});

// Computed options for dropdowns
const availableTacticOptions = computed(() => {
    return getTacticOptionsForTechnique();
});

const availableTechniqueOptions = computed(() => {
    return getTechniqueOptions(formData.value.mitre_tactic);
});

const activityGroupOptions = computed(() => {
    return props.availableActivityGroups.map((g) => ({
        label: g.is_default ? `${g.name} (Default)` : g.name,
        value: g.id,
    }));
});

// Readonly display labels
const displayTactic = computed(() => {
    if (!formData.value.mitre_tactic) return null;
    const opt = availableTacticOptions.value.find(
        (o) => o.value === formData.value.mitre_tactic,
    );
    return opt?.label || formData.value.mitre_tactic;
});

const displayTechnique = computed(() => {
    if (!formData.value.mitre_technique) return null;
    const opt = availableTechniqueOptions.value.find(
        (o) => o.value === formData.value.mitre_technique,
    );
    return opt?.label || formData.value.mitre_technique;
});

const displayGroup = computed(() => {
    if (!formData.value.activity_group_id) return null;
    const opt = activityGroupOptions.value.find(
        (o) => o.value === formData.value.activity_group_id,
    );
    return opt?.label || formData.value.activity_group_id;
});

// MITRE change handlers
function handleTacticChange(newTacticId: string | null) {
    formData.value.mitre_tactic = newTacticId || undefined;
    formData.value.mitre_technique = undefined;
}

function handleTechniqueChange(newTechniqueId: string | null) {
    formData.value.mitre_technique = newTechniqueId || undefined;
}

// Tag state — computed getter/setter bridges string[] (TagsInput) ↔ TagRead[] (formData)
const showTagSuggestions = ref(false);
const tagSearchQuery = ref('');

const currentTagNames = computed({
    get: () => (formData.value.tags || []).map((t) => t.name),
    set: async (newNames: string[]) => {
        const oldNames = (formData.value.tags || []).map((t) => t.name);
        const oldSet = new Set(oldNames);
        const newSet = new Set(newNames);

        // Remove tags no longer in the list
        if (formData.value.tags) {
            formData.value.tags = formData.value.tags.filter((t) =>
                newSet.has(t.name),
            );
        }

        // Add new tags
        for (const name of newNames) {
            if (oldSet.has(name)) continue;
            await addTag(name);
        }
    },
});

async function addTag(name: string) {
    if (formData.value.tags?.some((t) => t.name === name)) return;

    let tag = props.availableTags.find(
        (t) => t.name.toLowerCase() === name.toLowerCase(),
    );

    if (!tag) {
        try {
            const color =
                '#' +
                Math.floor(Math.random() * 16777215)
                    .toString(16)
                    .padStart(6, '0');
            tag = await tagService.createTag(props.assessmentId, {
                name,
                color,
            });
            emit('tag-created', tag);
        } catch (e) {
            toast.error(`Failed to create tag: ${name}`);
            return;
        }
    }

    if (formData.value.tags) {
        formData.value.tags = [...formData.value.tags, tag];
    } else {
        formData.value.tags = [tag];
    }
}

function getTagColor(name: string) {
    const tag =
        formData.value.tags?.find((t) => t.name === name) ||
        props.availableTags.find((t) => t.name === name);
    return tag?.color || '#808080';
}

// Tag Suggestions
const filteredTagSuggestions = computed(() => {
    const query = tagSearchQuery.value.toLowerCase();
    const currentNames = new Set(
        currentTagNames.value.map((n) => n.toLowerCase()),
    );

    return props.availableTags
        .filter((tag) => {
            if (currentNames.has(tag.name.toLowerCase())) return false;
            if (!query) return true;
            return tag.name.toLowerCase().includes(query);
        })
        .slice(0, 10);
});

function selectTagSuggestion(name: string) {
    if (!currentTagNames.value.includes(name)) {
        currentTagNames.value = [...currentTagNames.value, name];
    }
    tagSearchQuery.value = '';
    showTagSuggestions.value = false;
}

function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.tags-input-container')) {
        showTagSuggestions.value = false;
    }
}

onMounted(() => {
    document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
    <Collapsible defaultOpen>
        <Card>
            <CollapsibleTrigger as-child>
                <CardHeader class="cursor-pointer hover:bg-muted/50 transition-colors">
                    <div class="flex items-center justify-between">
                        <CardTitle class="text-lg">General Information</CardTitle>
                        <ChevronDown class="h-5 w-5 text-muted-foreground transition-transform duration-200 [[data-state=open]_&]:rotate-180" />
                    </div>
                </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
                <CardContent class="space-y-6">
                <!-- Activity Name -->
                <div class="space-y-2">
                    <Label class="text-sm font-medium">Activity Name</Label>
                    <template v-if="readonly">
                        <div class="text-sm px-3 py-2 rounded-md border bg-muted/30 min-h-[36px] flex items-center text-base font-medium">{{ formData.name || '—' }}</div>
                    </template>
                    <template v-else>
                        <Input
                            v-model="formData.name"
                            placeholder="Enter activity name"
                            class="text-base"
                        />
                    </template>
                </div>

                <!-- MITRE ATT&CK -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <template v-if="readonly">
                        <ReadonlyField label="MITRE Tactic" :model-value="displayTactic" />
                        <ReadonlyField label="MITRE Technique" :model-value="displayTechnique" />
                    </template>
                    <template v-else>
                        <div class="space-y-2">
                            <Label class="text-sm font-medium">MITRE Tactic</Label>
                            <SearchableSelect
                                :model-value="formData.mitre_tactic"
                                :options="availableTacticOptions"
                                placeholder="Select a tactic"
                                search-placeholder="Search tactics..."
                                @update:model-value="handleTacticChange"
                            />
                        </div>
                        <div class="space-y-2">
                            <Label class="text-sm font-medium">MITRE Technique</Label>
                            <SearchableSelect
                                :model-value="formData.mitre_technique"
                                :options="availableTechniqueOptions"
                                placeholder="Select a technique"
                                search-placeholder="Search techniques..."
                                @update:model-value="handleTechniqueChange"
                            />
                        </div>
                    </template>
                </div>

                <!-- Priority & Activity Group -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <template v-if="readonly">
                        <ReadonlyField label="Priority" :model-value="formData.priority as string" />
                        <ReadonlyField label="Activity Group" :model-value="displayGroup" />
                    </template>
                    <template v-else>
                        <div class="space-y-2">
                            <Label class="text-sm font-medium">Priority</Label>
                            <Select :model-value="formData.priority ?? undefined" @update:model-value="formData.priority = $event as any">
                                <SelectTrigger class="w-full">
                                    <SelectValue :placeholder="formData.priority ?? '\xa0'" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem v-for="opt in priorityOptions" :key="opt" :value="opt">
                                        {{ opt }}
                                    </SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div class="space-y-2">
                            <Label class="text-sm font-medium">Activity Group</Label>
                            <SearchableSelect
                                :model-value="formData.activity_group_id"
                                :options="activityGroupOptions"
                                placeholder="Select a group"
                                search-placeholder="Search groups..."
                                :clearable="false"
                                @update:model-value="formData.activity_group_id = $event || null"
                            />
                        </div>
                    </template>
                </div>

                <div class="space-y-4">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <MarkdownEditor :on-upload="uploadImage" :resolve-image-url="resolveImageUrl"
                                :model-value="formData.activity_rationale ?? ''"
                                @update:model-value="formData.activity_rationale = $event"
                                label="Activity Rationale"
                                placeholder="Explain the purpose and reasoning behind this activity"
                                :disabled="readonly"
                            />
                        </div>
                        <div class="space-y-2">
                            <MarkdownEditor :on-upload="uploadImage" :resolve-image-url="resolveImageUrl"
                                :model-value="formData.activity_requirements ?? ''"
                                @update:model-value="formData.activity_requirements = $event"
                                label="Activity Requirements"
                                placeholder="List any prerequisites or requirements"
                                :disabled="readonly"
                            />
                        </div>
                    </div>
                </div>

                <div class="border-t"></div>

                <!-- Expected Outcomes & Status Side by Side -->
                <div class="flex flex-col lg:flex-row gap-8">
                    <!-- Left: Expected Outcomes -->
                    <div class="space-y-4 flex-1">
                        <Label class="text-sm font-medium">Expected Outcomes</Label>
                        <div class="space-y-4">
                            <div class="space-y-2">
                                <Label class="text-sm font-medium">Expected Severity</Label>
                                <template v-if="readonly">
                                    <div class="text-sm px-3 py-2 rounded-md border bg-muted/30 min-h-[36px] flex items-center">{{ formData.expected_severity || '—' }}</div>
                                </template>
                                <template v-else>
                                    <Select :model-value="formData.expected_severity ?? undefined" @update:model-value="formData.expected_severity = $event as any">
                                        <SelectTrigger class="w-full">
                                            <SelectValue :placeholder="formData.expected_severity ?? '\xa0'" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem v-for="opt in severityOptions" :key="opt" :value="opt">
                                                {{ opt }}
                                            </SelectItem>
                                        </SelectContent>
                                    </Select>
                                </template>
                            </div>
                            <template v-if="readonly">
                                <div class="flex items-center justify-between border rounded-lg p-3.5">
                                    <Label class="text-sm font-normal">Expected Logging</Label>
                                    <Badge :class="formData.expected_logging ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'">{{ formData.expected_logging ? 'Yes' : 'No' }}</Badge>
                                </div>
                                <div class="flex items-center justify-between border rounded-lg p-3.5">
                                    <Label class="text-sm font-normal">Expected Prevention</Label>
                                    <Badge :class="formData.expected_prevention ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'">{{ formData.expected_prevention ? 'Yes' : 'No' }}</Badge>
                                </div>
                                <div class="flex items-center justify-between border rounded-lg p-3.5">
                                    <Label class="text-sm font-normal">Expected Alert Creation</Label>
                                    <Badge :class="formData.expected_alert_creation ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'">{{ formData.expected_alert_creation ? 'Yes' : 'No' }}</Badge>
                                </div>
                                <div class="flex items-center justify-between border rounded-lg p-3.5">
                                    <Label class="text-sm font-normal">Expected Stakeholder Notification</Label>
                                    <Badge :class="formData.expected_stakeholder_notification ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'">{{ formData.expected_stakeholder_notification ? 'Yes' : 'No' }}</Badge>
                                </div>
                            </template>
                            <template v-else>
                                <div class="flex items-center space-x-3 border rounded-lg p-3.5 hover:bg-accent/50 transition-colors">
                                    <Switch
                                        id="exp_log"
                                        v-model="formData.expected_logging"
                                    />
                                    <Label htmlFor="exp_log" class="cursor-pointer text-sm font-normal">Expected Logging</Label>
                                </div>
                                <div class="flex items-center space-x-3 border rounded-lg p-3.5 hover:bg-accent/50 transition-colors">
                                    <Switch
                                        id="exp_prev"
                                        v-model="formData.expected_prevention"
                                    />
                                    <Label htmlFor="exp_prev" class="cursor-pointer text-sm font-normal">Expected Prevention</Label>
                                </div>
                                <div class="flex items-center space-x-3 border rounded-lg p-3.5 hover:bg-accent/50 transition-colors">
                                    <Switch
                                        id="exp_alert"
                                        v-model="formData.expected_alert_creation"
                                    />
                                    <Label htmlFor="exp_alert" class="cursor-pointer text-sm font-normal">Expected Alert Creation</Label>
                                </div>
                                <div class="flex items-center space-x-3 border rounded-lg p-3.5 hover:bg-accent/50 transition-colors">
                                    <Switch
                                        id="exp_stakeholder"
                                        v-model="formData.expected_stakeholder_notification"
                                    />
                                    <Label htmlFor="exp_stakeholder" class="cursor-pointer text-sm font-normal">Expected Stakeholder Notification</Label>
                                </div>
                            </template>
                        </div>
                    </div>

                    <!-- Vertical Separator -->
                    <div class="hidden lg:block w-px bg-border self-stretch"></div>

                    <!-- Right: Status & Configuration -->
                    <div class="space-y-4 flex-1">
                        <Label class="text-sm font-medium">Status</Label>
                        <div class="space-y-4">
                            <div class="space-y-2">
                                <Label class="text-sm font-medium">State</Label>
                                <template v-if="readonly && !stateEditable">
                                    <div class="text-sm px-3 py-2 rounded-md border bg-muted/30 min-h-[36px] flex items-center">{{ formData.state || '—' }}</div>
                                </template>
                                <template v-else>
                                    <Select :model-value="formData.state ?? undefined" @update:model-value="formData.state = $event as any">
                                        <SelectTrigger class="w-full">
                                            <SelectValue :placeholder="formData.state ?? '\xa0'" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem v-for="opt in availableStateOptions" :key="opt" :value="opt">
                                                {{ opt }}
                                            </SelectItem>
                                        </SelectContent>
                                    </Select>
                                </template>
                            </div>
                            <template v-if="readonly">
                                <div class="flex items-center justify-between border rounded-lg p-3.5">
                                    <Label class="text-sm font-medium">Visible</Label>
                                    <Badge :class="formData.visible ? 'bg-green-600 text-white' : 'bg-muted text-muted-foreground'">{{ formData.visible ? 'Yes' : 'No' }}</Badge>
                                </div>
                            </template>
                            <template v-else>
                                <div class="flex items-center space-x-3 border rounded-lg p-3.5 hover:bg-accent/50 transition-colors">
                                    <Switch id="visible" v-model="formData.visible" />
                                    <Label htmlFor="visible" class="cursor-pointer text-sm font-medium">Visible</Label>
                                </div>
                            </template>

                            <div class="space-y-2 relative tags-input-container">
                                <Label class="text-sm font-medium">Tags</Label>
                                <TagsInput v-model="currentTagNames" :disabled="tagsReadonly ?? readonly" @focus="showTagSuggestions = true" class="min-h-[38px]">
                                    <TagsInputItem
                                        v-for="item in currentTagNames"
                                        :key="item"
                                        :value="item"
                                        :style="{
                                            backgroundColor: getTagColor(item),
                                            color: '#fff',
                                        }"
                                    >
                                        <TagsInputItemText />
                                        <TagsInputItemDelete v-if="!(tagsReadonly ?? readonly)" />
                                    </TagsInputItem>
                                    <TagsInputInput
                                        v-if="!(tagsReadonly ?? readonly)"
                                        placeholder="Add tag..."
                                        @focus="showTagSuggestions = true"
                                        v-model="tagSearchQuery"
                                    />
                                </TagsInput>
                                <!-- Tag Suggestions Dropdown -->
                                <div
                                    v-if="!(tagsReadonly ?? readonly) && showTagSuggestions && filteredTagSuggestions.length > 0"
                                    class="absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-lg"
                                >
                                    <ScrollArea class="max-h-[200px]">
                                        <button
                                            v-for="tag in filteredTagSuggestions"
                                            :key="tag.id"
                                            type="button"
                                            class="w-full text-left px-3 py-2 hover:bg-accent text-sm flex items-center gap-2"
                                            @click="selectTagSuggestion(tag.name)"
                                        >
                                            <span
                                                class="h-3 w-3 rounded-full"
                                                :style="{ backgroundColor: tag.color }"
                                            ></span>
                                            <span>{{ tag.name }}</span>
                                        </button>
                                    </ScrollArea>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </CardContent>
            </CollapsibleContent>
        </Card>
    </Collapsible>
</template>
