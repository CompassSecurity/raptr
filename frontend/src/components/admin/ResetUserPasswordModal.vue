<script setup lang="ts">
import { toTypedSchema } from '@/utils/zodAdapter';
import { useForm } from 'vee-validate';
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
import { useAdminStore } from '@/stores/admin';
import type { UserRead } from '@/types/utils';
import { zUserPasswordReset } from '@/types/zod.gen';

const props = defineProps<{
    open: boolean;
    user: UserRead | null;
}>();

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}>();

const adminStore = useAdminStore();

// Reset Password Form
const formSchema = toTypedSchema(zUserPasswordReset);

const { handleSubmit, isSubmitting, resetForm } = useForm({
    validationSchema: formSchema,
    initialValues: {
        new_password: '',
    },
});

const onSubmit = handleSubmit(async (values) => {
    if (!props.user) return;

    try {
        const response = await adminStore.resetUserPassword(
            props.user.id,
            values,
        );
        console.log('Reset Password Response:', response);
        if (response?.message) {
            toast.success(response.message);
        } else {
            console.error('No message in response');
            toast.success('Password reset successfully'); // Fallback
        }
        emit('success');
        emit('update:open', false);
        resetForm();
    } catch (error) {
        // Error handled globally
    }
});
</script>

<template>
    <Dialog :open="open" @update:open="$emit('update:open', $event)">
        <DialogContent>
            <DialogHeader>
                <DialogTitle>Reset Password</DialogTitle>
                <DialogDescription>
                    Reset password for user {{ user?.email }}.
                </DialogDescription>
            </DialogHeader>
            
            <form @submit="onSubmit" class="space-y-4">
                <FormField v-slot="{ componentField }" name="new_password">
                    <FormItem>
                        <FormLabel>New Password</FormLabel>
                        <FormControl>
                            <Input type="password" placeholder="••••••••" v-bind="componentField" />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                </FormField>
                
                <DialogFooter>
                    <Button type="submit" :disabled="isSubmitting">
                        {{ isSubmitting ? 'Resetting...' : 'Reset Password' }}
                    </Button>
                </DialogFooter>
            </form>
        </DialogContent>
    </Dialog>
</template>
