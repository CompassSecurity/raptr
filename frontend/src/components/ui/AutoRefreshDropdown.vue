<script setup lang="ts">
import { Button } from '@/components/ui/button';
import { RefreshCw, Check } from 'lucide-vue-next';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { usePreferencesStore } from '@/stores/preferences';

const preferencesStore = usePreferencesStore();

const props = defineProps<{
  variant?: 'outline' | 'default' | 'ghost' | 'secondary' | 'link' | 'destructive';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}>();

const setRefreshInterval = (seconds: number) => {
  if (seconds === 0) {
    preferencesStore.setAutoRefreshEnabled(false);
  } else {
    preferencesStore.setAutoRefreshInterval(seconds);
    preferencesStore.setAutoRefreshEnabled(true);
  }
};

const triggerManualRefresh = () => {
    preferencesStore.triggerManualRefresh();
};
</script>

<template>
    <DropdownMenu>
        <DropdownMenuTrigger as-child>
            <Button
                :size="size || 'sm'"
                :variant="variant || (preferencesStore.autoRefreshEnabled ? 'default' : 'outline')"
                class="relative"
            >
                <RefreshCw :class="{ 'mr-2 h-4 w-4': size !== 'icon', 'h-[1.2rem] w-[1.2rem]': size === 'icon' }" />
                <template v-if="size !== 'icon'">
                    {{ preferencesStore.autoRefreshEnabled ? `${preferencesStore.autoRefreshInterval}s` : 'Off' }}
                </template>
                <span v-else class="sr-only">Refresh Options</span>
                
                <!-- Active Indicator Dot (useful for icon-only mode) -->
                <span 
                    v-if="preferencesStore.autoRefreshEnabled" 
                    class="absolute top-1 right-1 flex h-2 w-2"
                >
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
            </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent :align="size === 'icon' ? 'end' : 'start'">
            <DropdownMenuItem @click="triggerManualRefresh" class="font-semibold text-primary">
                Reload Now
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem @click="setRefreshInterval(0)" class="flex items-center justify-between">
                Off
                <Check v-if="!preferencesStore.autoRefreshEnabled" class="h-4 w-4 text-primary" />
            </DropdownMenuItem>
            <DropdownMenuItem @click="setRefreshInterval(1)" class="flex items-center justify-between">
                1 second
                <Check v-if="preferencesStore.autoRefreshEnabled && preferencesStore.autoRefreshInterval === 1" class="h-4 w-4 text-primary" />
            </DropdownMenuItem>
            <DropdownMenuItem @click="setRefreshInterval(5)" class="flex items-center justify-between">
                5 seconds
                <Check v-if="preferencesStore.autoRefreshEnabled && preferencesStore.autoRefreshInterval === 5" class="h-4 w-4 text-primary" />
            </DropdownMenuItem>
            <DropdownMenuItem @click="setRefreshInterval(10)" class="flex items-center justify-between">
                10 seconds
                <Check v-if="preferencesStore.autoRefreshEnabled && preferencesStore.autoRefreshInterval === 10" class="h-4 w-4 text-primary" />
            </DropdownMenuItem>
            <DropdownMenuItem @click="setRefreshInterval(30)" class="flex items-center justify-between">
                30 seconds
                <Check v-if="preferencesStore.autoRefreshEnabled && preferencesStore.autoRefreshInterval === 30" class="h-4 w-4 text-primary" />
            </DropdownMenuItem>
        </DropdownMenuContent>
    </DropdownMenu>
</template>
