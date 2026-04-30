<script setup lang="ts">
import { toTypedSchema } from '@vee-validate/zod';
import { useForm } from 'vee-validate';
import { ref } from 'vue';
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
import { activityGroupService } from '@/services/activityService';

const props = defineProps<{
    open: boolean;
    assessmentId: string;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'created'): void;
}>();

const loading = ref(false);

// Use the Zod schema for validation, only requiring name field
const formSchema = toTypedSchema(
    z.object({
        name: z.string().min(1, 'Group name is required'),
    }),
);

const form = useForm({
    validationSchema: formSchema,
    initialValues: {
        name: '',
    },
});

const onSubmit = form.handleSubmit(async (values) => {
    loading.value = true;
    try {
        await activityGroupService.createGroup(props.assessmentId, {
            name: values.name,
            visible: false,
        });
        toast.success('Activity group created successfully');

        emit('created');
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
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle>Create Activity Group</DialogTitle>
      </DialogHeader>

      <form @submit="onSubmit" class="space-y-4">
        <FormField v-slot="{ componentField }" name="name">
          <FormItem>
            <FormLabel>Group Name</FormLabel>
            <FormControl>
              <Input type="text" placeholder="Enter group name" v-bind="componentField" />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            @click="emit('update:open', false)"
            :disabled="loading"
          >
            Cancel
          </Button>
          <Button type="submit" :disabled="loading">
            {{ loading ? 'Creating...' : 'Create Group' }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
