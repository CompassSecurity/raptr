<script setup lang="ts">
import { toTypedSchema } from '@/utils/zodAdapter';
import { useForm } from 'vee-validate';
import { toast } from 'vue-sonner';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { useAuthStore } from '@/stores/auth';
import { zUserPasswordUpdate } from '@/types/zod.gen';

const authStore = useAuthStore();

const formSchema = toTypedSchema(
    zUserPasswordUpdate.extend({
        confirm_password: z.string(),
    }).refine((data) => data.new_password === data.confirm_password, {
        message: "Passwords don't match",
        path: ['confirm_password'],
    }),
);

const { handleSubmit, isSubmitting, resetForm } = useForm({
    validationSchema: formSchema,
});

const onSubmit = handleSubmit(async (values) => {
    try {
        await authStore.changePassword({
            old_password: values.old_password,
            new_password: values.new_password,
        });
        toast.success('Password updated successfully');
        resetForm();
    } catch (error: any) {
        // Error is handled by global interceptor
    }
});
</script>

<template>
    <Card class="h-full">
        <CardHeader>
            <CardTitle class="text-2xl">Reset Password</CardTitle>
        </CardHeader>
        <Separator />
        <CardContent class="py-6">
            <form @submit="onSubmit" class="space-y-4">
                <FormField v-slot="{ componentField }" name="old_password">
                    <FormItem>
                        <FormLabel>Current Password</FormLabel>
                        <FormControl>
                            <Input type="password" placeholder="Enter current password" v-bind="componentField" />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                </FormField>

                <FormField v-slot="{ componentField }" name="new_password">
                    <FormItem>
                         <FormLabel>New Password</FormLabel>
                         <FormControl>
                            <Input type="password" placeholder="Enter new password" v-bind="componentField" />
                         </FormControl>
                         <FormMessage />
                    </FormItem>
                </FormField>

                <FormField v-slot="{ componentField }" name="confirm_password">
                    <FormItem>
                         <FormLabel>Confirm Password</FormLabel>
                         <FormControl>
                            <Input type="password" placeholder="Confirm new password" v-bind="componentField" />
                         </FormControl>
                         <FormMessage />
                    </FormItem>
                </FormField>

                <Button type="submit" class="w-full" :disabled="isSubmitting">
                    {{ isSubmitting ? 'Updating...' : 'Update Password' }}
                </Button>
            </form>
        </CardContent>
    </Card>
</template>