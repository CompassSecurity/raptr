<script setup lang="ts">
import { Loader2 } from 'lucide-vue-next';
import QRCode from 'qrcode';
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
const qrCodeUrl = ref('');
const otp = ref(''); // InputOTP v-model
const setupError = ref('');

function focusOtpInput() {
    // [data-input-otp] IS the hidden input element itself (not a container)
    const input = document.querySelector<HTMLInputElement>('[data-input-otp]');
    if (input) input.focus();
}

onMounted(async () => {
    try {
        const response = await authStore.setupMfa();
        qrCodeUrl.value = await QRCode.toDataURL(response.provisioning_uri);
    } catch (error: any) {
        setupError.value =
            error.response?.data?.detail || 'Failed to initiate MFA setup.';
        toast.error('MFA Setup Failed', { description: setupError.value });
    }
    // Focus the OTP input after QR code loads
    await nextTick();
    focusOtpInput();
    setTimeout(focusOtpInput, 100);
});

async function handleVerify() {
    if (otp.value.length !== 6) return;

    loading.value = true;
    try {
        const nextUrl = await authStore.validateMfaSetup(otp.value);
        toast.success('MFA Validation Success', {
            description: 'Your MFA has been verified.',
        });
        // Redirect to the target page or home since we now have the full token
        router.push(nextUrl || '/');
    } catch (error: any) {
        toast.error('Validation Failed', {
            description: error.response?.data?.detail || 'Invalid OTP code.',
        });
        otp.value = ''; // Clear input on error
    } finally {
        loading.value = false;
    }
}
</script>

<template>
    <div class="flex h-screen w-full items-center justify-center px-4">
        <Card class="w-full max-w-sm">
            <CardHeader>
                <CardTitle class="text-2xl">Setup MFA</CardTitle>
                <CardDescription>
                    Scan the QR code with your authenticator app to enable Multi-Factor Authentication.
                </CardDescription>
            </CardHeader>
            <CardContent class="grid gap-4">
                <div v-if="qrCodeUrl" class="flex justify-center p-4 bg-white rounded-lg border">
                    <img :src="qrCodeUrl" alt="MFA QR Code" class="w-48 h-48" />
                </div>
                <div v-else-if="setupError" class="text-red-500 text-center py-4">
                    {{ setupError }}
                </div>
                <div v-else class="flex justify-center py-8">
                    <Loader2 class="h-8 w-8 animate-spin text-muted-foreground" />
                </div>

                <div class="flex flex-col gap-2">
                    <p class="text-sm text-center text-muted-foreground mb-2">Enter the 6-digit code from your app</p>
                    <div class="flex justify-center">
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
                </div>
            </CardContent>
            <CardFooter>
                <Button class="w-full" @click="handleVerify" :disabled="loading || otp.length !== 6">
                    <Loader2 v-if="loading" class="mr-2 h-4 w-4 animate-spin" />
                    Verify & Activate
                </Button>
            </CardFooter>
        </Card>
    </div>
</template>
