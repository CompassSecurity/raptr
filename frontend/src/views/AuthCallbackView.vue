<template>
  <div class="flex items-center justify-center min-h-screen p-4">
    <Card class="w-full max-w-md">
      <CardHeader>
        <CardTitle class="text-2xl font-bold text-center">Authenticating</CardTitle>
        <CardDescription class="text-center">
          Please wait while we complete your sign in...
        </CardDescription>
      </CardHeader>
      <CardContent class="flex justify-center py-8">
        <Loader2 class="h-8 w-8 animate-spin text-primary" />
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { Loader2 } from '@lucide/vue';
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { toast } from 'vue-sonner';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

onMounted(async () => {
    try {
        await authStore.handleProviderCallback();
        toast.success('Successfully authenticated');
        router.push('/');
    } catch (error) {
        console.error('Authentication error:', error);
        toast.error('Authentication failed. Please try again.');
        router.push('/login');
    }
});
</script>
