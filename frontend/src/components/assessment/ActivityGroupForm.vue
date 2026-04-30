<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { toast } from 'vue-sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { activityGroupService } from '@/services/activityService';
import { useAssessmentDetailStore } from '@/stores/assessmentDetail';
import type { AclRole, ActivityGroupRead } from '@/types/utils';

const props = defineProps<{
    group: ActivityGroupRead;
    assessmentId: string;
    role?: AclRole | null;
}>();

const emit = defineEmits<(e: 'saved') => void>();

const store = useAssessmentDetailStore();
const saving = ref(false);

// Role-based restrictions
const isSpectator = computed(() => props.role === 'spectator');
const isBlue = computed(() => props.role === 'blue');

const readonly = computed(() => isSpectator.value || isBlue.value);
const showSaveButton = computed(() => !readonly.value);

// Local state for the form
const formData = ref<Partial<ActivityGroupRead>>({});

// Initialize form data
const initForm = () => {
    formData.value = { ...props.group };
};

watch(
    () => props.group,
    () => {
        initForm();
    },
    { immediate: true },
);

async function save() {
    if (readonly.value) return;

    saving.value = true;
    try {
        await activityGroupService.updateGroup(
            props.assessmentId,
            props.group.id,
            {
                name: formData.value.name || '',
                visible: formData.value.visible ?? false,
            },
        );
        toast.success('Activity group saved successfully');

        // Refresh the groups list in the store
        await store.fetchGroups(props.assessmentId);

        emit('saved');
    } catch (error: any) {
        toast.error('Failed to save activity group');
        console.error(error);
    } finally {
        saving.value = false;
    }
}
</script>

<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center justify-between sticky top-0 z-10 bg-background py-4 border-b -mx-8 px-8 -mt-6 mb-6">
            <div class="flex items-center gap-4">
                <h1 class="text-2xl font-bold tracking-tight">Activity Group: {{ props.group.name }}</h1>
                <div class="flex gap-2">
                    <!-- Read-only badge -->
                    <span v-if="readonly" class="inline-flex items-center rounded-md bg-muted px-2 py-1 text-xs font-medium text-muted-foreground ring-1 ring-inset ring-muted-foreground/20">
                        Read Only
                    </span>
                    <span v-if="group.is_default" class="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10 dark:bg-blue-900/30 dark:text-blue-400 dark:ring-blue-400/30">
                        Default Group
                    </span>
                </div>
            </div>
            
            <div class="flex items-center gap-2">
                <Button 
                    v-if="showSaveButton"
                    @click="save" 
                    :disabled="saving"
                    class="min-w-[100px]"
                >
                    <span v-if="saving" class="flex items-center gap-2">
                        <div class="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"/>
                        Saving...
                    </span>
                    <span v-else>Save Changes</span>
                </Button>
            </div>
        </div>

        <!-- Main Form Content -->
        <div class="grid gap-6">
            <!-- General Details -->
            <Card>
                <CardHeader>
                    <CardTitle>Group Settings</CardTitle>
                </CardHeader>
                <CardContent class="grid gap-6">
                    <div class="grid gap-2">
                        <Label for="group-name">Name</Label>
                        <Input 
                            id="group-name" 
                            v-model="formData.name" 
                            :disabled="readonly"
                            placeholder="e.g. Initial Access"
                        />
                    </div>
                    
                    <div class="flex items-center justify-between rounded-lg border p-4">
                        <div class="space-y-0.5">
                            <Label class="text-base text-foreground">Visible</Label>
                        </div>
                        <Switch
                            v-model="formData.visible"
                            :disabled="readonly"
                        />
                    </div>
                </CardContent>
            </Card>
        </div>
    </div>
</template>
