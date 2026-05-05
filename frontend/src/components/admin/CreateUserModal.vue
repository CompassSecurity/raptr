<script setup lang="ts">
import { toTypedSchema } from '@/utils/zodAdapter';
import { useForm } from 'vee-validate';
import { nextTick, ref, watch } from 'vue';
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

const props = defineProps<{
    open: boolean;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

const adminStore = useAdminStore();

import { zUserCreate } from '@/types/zod.gen';

// Create User Form
const emailInput = ref<InstanceType<typeof Input> | null>(null);
const formSchema = toTypedSchema(zUserCreate);

watch(
    () => props.open,
    async (isOpen) => {
        if (isOpen) {
            resetForm({
                values: {
                    role: 'user',
                    disabled: false,
                },
            });
            await nextTick();
            emailInput.value?.$el?.focus();
        }
    },
);

const { handleSubmit, isSubmitting, resetForm } = useForm({
    validationSchema: formSchema,
    initialValues: {
        role: 'user',
        disabled: false,
    },
});

const onSubmit = handleSubmit(async (values) => {
    try {
        await adminStore.createUser(values);
        toast.success('User created successfully');
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
                <DialogTitle>Create New User</DialogTitle>
                <DialogDescription>
                    Add a new user to the system. Click save when you're done.
                </DialogDescription>
            </DialogHeader>
            
            <form @submit="onSubmit" class="space-y-4">
                <FormField v-slot="{ componentField }" name="email">
                    <FormItem>
                        <FormLabel>Email</FormLabel>
                        <FormControl>
                            <Input ref="emailInput" placeholder="user@example.com" v-bind="componentField" />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                </FormField>
                
                <FormField v-slot="{ componentField }" name="password">
                    <FormItem>
                        <FormLabel>Password</FormLabel>
                        <FormControl>
                            <Input type="password" placeholder="••••••••" v-bind="componentField" />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                </FormField>

                    <FormField v-slot="{ componentField }" name="role">
                    <FormItem>
                        <FormLabel>Role</FormLabel>
                        <Select v-bind="componentField" default-value="user">
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
                        {{ isSubmitting ? 'Creating...' : 'Create User' }}
                    </Button>
                </DialogFooter>
            </form>
        </DialogContent>
    </Dialog>
</template>
