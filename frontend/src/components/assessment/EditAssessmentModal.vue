<script setup lang="ts">
import { toTypedSchema } from '@vee-validate/zod';
import { useForm } from 'vee-validate';
import { ref, watch } from 'vue';
import { toast } from 'vue-sonner';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useAssessmentListStore } from '@/stores/assessmentList';
import type { components } from '@/types/schema';
import { schemas } from '@/types/zod';

type AssessmentRead = components['schemas']['AssessmentRead'];

const props = defineProps<{
    open: boolean;
    assessment: AssessmentRead | null;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

const assessmentStore = useAssessmentListStore();
const loading = ref(false);

const { AssessmentBase } = schemas;

// Use the Zod schema for validation
const formSchema = toTypedSchema(
    AssessmentBase.extend({
        name: z.string().min(1, 'Name is required'),
        description: z.string().min(1, 'Description is required'),
    }),
);

const form = useForm({
    validationSchema: formSchema,
});

// Watch for modal opening to populate form with current assessment data
watch(
    () => props.open,
    (isOpen) => {
        if (isOpen && props.assessment) {
            form.resetForm({
                values: {
                    name: props.assessment.name,
                    description: props.assessment.description,
                    assessment_type: props.assessment.assessment_type,
                },
            });
        }
    },
    { immediate: true },
);

const onSubmit = form.handleSubmit(async (values) => {
    if (!props.assessment) return;

    loading.value = true;
    try {
        const payload = {
            ...values,
            assessment_type: values.assessment_type || 'PurpleTeam',
        };

        await assessmentStore.updateAssessment(props.assessment.id, payload);
        toast.success('Assessment updated successfully');

        emit('success');
        emit('update:open', false);
    } catch (error) {
        // Error handled by global interceptor
    } finally {
        loading.value = false;
    }
});
</script>

<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-2xl">
      <DialogHeader>
        <DialogTitle>Edit Assessment</DialogTitle>
      </DialogHeader>

      <form @submit="onSubmit" class="space-y-4">
        <FormField v-slot="{ componentField }" name="name">
          <FormItem>
            <FormLabel>Name</FormLabel>
            <FormControl>
              <Input type="text" placeholder="Assessment Name" v-bind="componentField" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <FormField v-slot="{ componentField }" name="description">
          <FormItem>
            <FormLabel>Description</FormLabel>
            <FormControl>
              <Textarea placeholder="Describe the assessment..." v-bind="componentField" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <FormField v-slot="{ componentField }" name="assessment_type">
          <FormItem>
            <FormLabel>Type</FormLabel>
            <Select v-bind="componentField">
              <FormControl>
                <SelectTrigger class="w-full">
                  <SelectValue placeholder="Select a type" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="PurpleTeam">Purple Team</SelectItem>
                <SelectItem value="RedTeam">Red Team</SelectItem>
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        </FormField>

        <DialogFooter>
          <Button type="submit" :disabled="loading">
            {{ loading ? 'Saving...' : 'Save changes' }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
