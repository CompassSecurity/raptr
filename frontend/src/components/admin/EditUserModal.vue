<script setup lang="ts">
import { toTypedSchema } from '@vee-validate/zod';
import { useForm } from 'vee-validate';
import { watch } from 'vue';
import { toast } from 'vue-sonner';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
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
import { useAdminStore } from '@/stores/admin';
import type { UserRead } from '@/types/utils';

const props = defineProps<{
    open: boolean;
    user: UserRead | null;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

const adminStore = useAdminStore();

import { schemas } from '@/types/zod';

// Edit User Form
const editFormSchema = toTypedSchema(schemas.UserBase);

const form = useForm({
    validationSchema: editFormSchema,
});

const { handleSubmit, isSubmitting } = form;

watch(
    () => props.open,
    (isOpen) => {
        if (isOpen && props.user) {
            form.resetForm({
                values: {
                    email: props.user.email,
                    role: props.user.role,
                    disabled: props.user.disabled,
                },
            });
        }
    },
    { immediate: true },
);

const onSubmit = handleSubmit(async (values) => {
    if (!props.user) return;
    try {
        await adminStore.updateUser(props.user.id, values);
        toast.success('User updated successfully');
        emit('success');
        emit('update:open', false);
    } catch (error) {
        // Error handled globally
    }
});
</script>

<template>
    <Dialog :open="open" @update:open="$emit('update:open', $event)">
        <DialogContent>
            <DialogHeader>
                <DialogTitle>Edit User</DialogTitle>
                <DialogDescription>
                    Update user details. Click save when you're done.
                </DialogDescription>
            </DialogHeader>
            
            <form @submit="onSubmit" class="space-y-4">
                <FormField v-slot="{ componentField }" name="email">
                    <FormItem>
                        <FormLabel>Email</FormLabel>
                        <FormControl>
                            <Input placeholder="user@example.com" v-bind="componentField" />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                </FormField>

                    <FormField v-slot="{ componentField }" name="role">
                    <FormItem>
                        <FormLabel>Role</FormLabel>
                        <Select v-bind="componentField">
                            <FormControl>
                                <SelectTrigger class="w-full">
                                    <SelectValue placeholder="Select a role" />
                                </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                                <SelectItem value="user">User</SelectItem>
                                <SelectItem value="admin">Admin</SelectItem>
                            </SelectContent>
                        </Select>
                        <FormMessage />
                    </FormItem>
                </FormField>
                    
                <FormField v-slot="{ componentField }" name="disabled">
                    <FormItem>
                        <FormLabel>Status</FormLabel>
                        <Select v-bind="componentField" :model-value="componentField.modelValue ? 'true' : 'false'" @update:model-value="(val) => componentField['onUpdate:modelValue']?.(val === 'true')">
                            <FormControl>
                                <SelectTrigger class="w-full">
                                    <SelectValue placeholder="Select status" />
                                </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                                <SelectItem value="false">Active</SelectItem>
                                <SelectItem value="true">Disabled</SelectItem>
                            </SelectContent>
                        </Select>
                        <FormMessage />
                    </FormItem>
                </FormField>
                
                <DialogFooter>
                    <Button type="submit" :disabled="isSubmitting">
                        {{ isSubmitting ? 'Saving...' : 'Save Changes' }}
                    </Button>
                </DialogFooter>
            </form>
        </DialogContent>
    </Dialog>
</template>
