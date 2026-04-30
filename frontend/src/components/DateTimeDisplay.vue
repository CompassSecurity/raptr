<script setup lang="ts">
import { computed } from 'vue';
import { usePreferencesStore } from '@/stores/preferences';
import { formatDateTime } from '@/utils/dateFormatter';

const props = defineProps<{
    date: string | null | undefined;
}>();

const preferencesStore = usePreferencesStore();

const formattedDate = computed(() => {
    return formatDateTime(
        props.date,
        preferencesStore.effectiveTimezone,
        preferencesStore.dateFormat,
        preferencesStore.timeFormat,
    );
});
</script>

<template>
    <span class="whitespace-nowrap">{{ formattedDate }}</span>
</template>
