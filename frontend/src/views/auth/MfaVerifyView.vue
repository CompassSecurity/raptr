<script setup lang="ts">
import { Loader2 } from 'lucide-vue-next';
import { nextTick, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { toast } from 'vue-sonner';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    InputOTP,
    InputOTPGroup,
    InputOTPSeparator,
    InputOTPSlot,
} from '@/components/ui/input-otp';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const loading = ref(false);
const otp = ref('');

function focusOtpInput() {
    // [data-input-otp] IS the hidden input element itself (not a container)
    const input = document.querySelector<HTMLInputElement>('[data-input-otp]');
    if (input) input.focus();
}

onMounted(async () => {
    await nextTick();
    focusOtpInput();
    // Retry to handle route transition timing
    setTimeout(focusOtpInput, 100);
    setTimeout(focusOtpInput, 300);
});

async function handleVerify() {
    if (otp.value.length !== 6) return;

    loading.value = true;
    try {
        await authStore.verifyMfa(otp.value);
        toast.success('Login Successful');
        router.push('/');
    } catch (error: any) {
        toast.error('Verification Failed', {
            description: error.response?.data?.detail || 'Invalid OTP code.',
        });
        otp.value = '';
    } finally {
        loading.value = false;
    }
}
</script>

<template>
    <div class="flex h-screen w-full items-center justify-center px-4">
        <Card class="w-full max-w-sm">
            <CardHeader>
                <CardTitle class="text-2xl">MFA Verification</CardTitle>
                <CardDescription>
                    Enter the 6-digit code from your authenticator app.
                </CardDescription>
            </CardHeader>
            <CardContent class="grid gap-4">
                <div class="flex justify-center py-4">
                     <InputOTP v-model="otp" :maxlength="6" @complete="handleVerify">
                        <InputOTPGroup>
                            <InputOTPSlot :index="0" />
                            <InputOTPSlot :index="1" />
                            <InputOTPSlot :index="2" />
                        </InputOTPGroup>
                        <InputOTPSeparator />
                        <InputOTPGroup>
                            <InputOTPSlot :index="3" />
                            <InputOTPSlot :index="4" />
                            <InputOTPSlot :index="5" />
                        </InputOTPGroup>
                    </InputOTP>
                </div>
            </CardContent>
            <CardFooter>
                <Button class="w-full" @click="handleVerify" :disabled="loading || otp.length !== 6">
                    <Loader2 v-if="loading" class="mr-2 h-4 w-4 animate-spin" />
                    Verify
                </Button>
            </CardFooter>
        </Card>
    </div>
</template>
