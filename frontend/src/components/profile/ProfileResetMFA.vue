<script setup lang="ts">
import { toTypedSchema } from '@/utils/zodAdapter';
import { useForm } from 'vee-validate';
import { computed } from 'vue';
import { toast } from 'vue-sonner';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import { userService } from '@/services/userService';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const isMFAEnabled = computed(() => authStore.user?.mfa_verified ?? false);

const formSchema = toTypedSchema(
    z.object({
        password: z.string().min(1, 'Password is required to confirm reset'),
    }),
);

const { handleSubmit, isSubmitting, resetForm } = useForm({
    validationSchema: formSchema,
});

const onSubmit = handleSubmit(async (values) => {
    try {
        const response = await userService.resetMyMFA(values.password);
        toast.success(response.message || 'MFA reset successfully');
        resetForm();
        await authStore.fetchMe();
    } catch (error: any) {
        // Error is handled by global interceptor
    }
});
</script>

<template>
    <Card class="h-full">
        <CardHeader>
            <CardTitle class="text-2xl">Reset MFA</CardTitle>
            <CardDescription>
                Reset your Multi-Factor Authentication settings. You will need to reconfigure it on your next login.
            </CardDescription>
        </CardHeader>
        <Separator />
        <CardContent class="py-6">
            <form @submit="onSubmit" class="space-y-4">
                <FormField v-slot="{ componentField }" name="password">
                    <FormItem>
                        <FormLabel>Current Password</FormLabel>
                        <FormControl>
                            <Input
                                type="password"
                                placeholder="Enter password to confirm"
                                v-bind="componentField"
                                :disabled="!isMFAEnabled || isSubmitting"
                            />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                </FormField>

                <TooltipProvider v-if="!isMFAEnabled">
                    <Tooltip>
                        <TooltipTrigger as-child>
                            <span tabindex="0" class="w-full inline-block">
                                <Button type="submit" variant="destructive" class="w-full" :disabled="true">
                                    Reset MFA
                                </Button>
                            </span>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>MFA is not currently enabled for your account</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
                <Button v-else type="submit" variant="destructive" class="w-full" :disabled="isSubmitting">
                    {{ isSubmitting ? 'Resetting...' : 'Reset MFA' }}
                </Button>
            </form>
        </CardContent>
    </Card>
</template>
