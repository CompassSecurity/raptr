<script setup lang="ts">
import { useDark, useToggle } from '@vueuse/core';
import {
    ChevronRight,
    Globe,
    LogOut,
    MoonIcon,
    Settings,
    SunIcon,
} from 'lucide-vue-next';
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';
import AboutModal from '@/components/layout/AboutModal.vue';
import AutoRefreshDropdown from '@/components/ui/AutoRefreshDropdown.vue';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAssessmentDetailStore } from '@/stores/assessmentDetail';
import { useAuthStore } from '@/stores/auth';
import { usePreferencesStore } from '@/stores/preferences';

const authStore = useAuthStore();
const preferencesStore = usePreferencesStore();
const assessmentStore = useAssessmentDetailStore();
const route = useRoute();
const isDark = useDark();
const toggleDark = useToggle(isDark);
const showAboutModal = ref(false);

// Breadcrumb: show assessment name when on assessment or activity routes
const assessmentId = computed(() => route.params.id as string | undefined);
const isAssessmentRoute = computed(
    () =>
        route.name === 'assessment-detail' ||
        route.name === 'assessment-activity-detail' ||
        route.name === 'assessment-group-detail' ||
        route.name === 'assessment-statistics',
);
const isActivityRoute = computed(
    () =>
        route.name === 'assessment-activity-detail' ||
        route.name === 'assessment-group-detail' ||
        route.name === 'assessment-statistics',
);
const assessmentName = computed(() => assessmentStore.assessment?.name);

// Breadcrumb: show "Admin" when on admin sub-routes
const isAdminSubRoute = computed(
    () => route.name === 'user-management' || route.name === 'configuration',
);
const adminSubRouteName = computed(() => {
    if (route.name === 'user-management') return 'User Management';
    if (route.name === 'configuration') return 'Configuration';
    return '';
});

const handleLogout = async () => {
    // Assuming authStore.logout() handles API call and redirect
    authStore.logout();
};
</script>

<template>
  <nav class="border-b w-full bg-background">
    <div class="flex h-16 items-center px-4 md:px-6 justify-between w-full">
      <!-- Logo + Breadcrumb -->
      <div class="flex items-center gap-1 min-w-0">
        <h1 class="text-2xl font-bold shrink-0">
          <RouterLink to="/" class="hover:opacity-80 transition-opacity">RAPTR</RouterLink>
        </h1>
        <template v-if="isAssessmentRoute && assessmentName">
          <ChevronRight class="h-4 w-4 text-muted-foreground shrink-0" />
          <RouterLink
              v-if="isActivityRoute && assessmentId"
              :to="{ name: 'assessment-detail', params: { id: assessmentId } }"
              class="text-2xl font-bold text-muted-foreground hover:text-foreground transition-colors truncate max-w-[200px] md:max-w-[300px]"
              :title="assessmentName"
          >
            {{ assessmentName }}
          </RouterLink>
          <span
              v-else
              class="text-2xl font-bold text-foreground truncate max-w-[200px] md:max-w-[300px]"
              :title="assessmentName"
          >
            {{ assessmentName }}
          </span>
        </template>
        <template v-if="isAdminSubRoute">
          <ChevronRight class="h-4 w-4 text-muted-foreground shrink-0" />
          <RouterLink
              :to="{ name: 'admin' }"
              class="text-2xl font-bold text-muted-foreground hover:text-foreground transition-colors"
          >
            Admin
          </RouterLink>
          <ChevronRight class="h-4 w-4 text-muted-foreground shrink-0" />
          <span class="text-2xl font-bold text-foreground">
            {{ adminSubRouteName }}
          </span>
        </template>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-2">
        <p v-if="authStore.user" class="text-sm font-medium mr-2 hidden md:block">
          {{ authStore.user.email }}
        </p>

        <!-- Timezone Toggle -->
        <Button @click="preferencesStore.toggleTimezoneMode()" variant="ghost" size="sm" class="flex items-center gap-2">
            <Globe class="h-[1.2rem] w-[1.2rem]" />
            <span class="text-xs font-mono w-8 hidden md:block">{{ preferencesStore.timezoneMode.toUpperCase() }}</span>
        </Button>

        <!-- Theme Toggle -->
        <Button @click="toggleDark()" variant="ghost" size="icon">
           <SunIcon class="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
           <MoonIcon class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
           <span class="sr-only">Toggle theme</span>
        </Button>

        <template v-if="authStore.token">
           <!-- Auto-Refresh Dropdown -->
           <AutoRefreshDropdown variant="ghost" size="icon" />

           <!-- Settings Dropdown -->
           <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button variant="ghost" size="icon">
                <Settings class="h-[1.2rem] w-[1.2rem]" />
                <span class="sr-only">Settings</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem v-if="authStore.user?.role === 'admin'" @click="$router.push('/admin')">
                Admin
              </DropdownMenuItem>
              <DropdownMenuItem @click="$router.push('/profile')">
                Profile
              </DropdownMenuItem>

              <DropdownMenuSeparator />
              <DropdownMenuItem @click="showAboutModal = true">
                About
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <!-- About Modal -->
          <AboutModal v-model:open="showAboutModal" />

          <!-- Logout -->
          <Button @click="handleLogout" variant="destructive" size="sm" class="ml-2">
            <LogOut class="mr-2 h-4 w-4" />
            Logout
          </Button>
        </template>
      </div>
    </div>
  </nav>
</template>
