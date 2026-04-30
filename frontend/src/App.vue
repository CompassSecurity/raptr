<script setup lang="ts">
import { onMounted } from 'vue';
import { RouterView } from 'vue-router';
import 'vue-sonner/style.css';
import TopBar from '@/components/TopBar.vue';
import { Toaster } from '@/components/ui/sonner';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();

onMounted(() => {
    authStore.initializeAuth();
});
</script>

<template>
  <TopBar />
  <RouterView />
  <Toaster richColors position="top-center" />
</template>