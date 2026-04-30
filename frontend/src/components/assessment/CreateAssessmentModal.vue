<script setup lang="ts">
import { toTypedSchema } from '@vee-validate/zod';
import { useForm } from 'vee-validate';
import { nextTick, ref, watch } from 'vue';
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
import { schemas } from '@/types/zod';

const props = defineProps<{
    open: boolean;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

const assessmentStore = useAssessmentListStore();
const loading = ref(false);
const nameInput = ref<InstanceType<typeof Input> | null>(null);

watch(
    () => props.open,
    async (isOpen) => {
        if (isOpen) {
            await nextTick();
            nameInput.value?.$el?.focus();
        }
    },
);

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
    initialValues: {
        name: '',
        description: '',
        assessment_type: 'PurpleTeam',
    },
});

const onSubmit = form.handleSubmit(async (values) => {
    loading.value = true;
    try {
        const payload = {
            ...values,
            assessment_type: values.assessment_type || 'PurpleTeam',
        };

        await assessmentStore.createAssessment(payload);
        toast.success('Assessment created successfully');

        emit('success');
        emit('update:open', false);
        form.resetForm();
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
        <DialogTitle>New Assessment</DialogTitle>
      </DialogHeader>

      <form @submit="onSubmit" class="space-y-4">
        <FormField v-slot="{ componentField }" name="name">
          <FormItem>
            <FormLabel>Name</FormLabel>
            <FormControl>
              <Input ref="nameInput" type="text" placeholder="Assessment Name" v-bind="componentField" />
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
            <Select v-bind="componentField" default-value="PurpleTeam">
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
            {{ loading ? 'Creating...' : 'Create Assessment' }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
