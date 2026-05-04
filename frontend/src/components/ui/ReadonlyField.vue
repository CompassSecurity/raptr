<script setup lang="ts">
import { Label } from '@/components/ui/label';

withDefaults(defineProps<{
    label?: string;
    modelValue?: string | null;
}>(), {
    modelValue: null,
});
</script>

<template>
    <div class="space-y-2">
        <Label v-if="label" class="text-sm font-medium">{{ label }}</Label>
        <div class="text-sm px-3 py-2 rounded-md border bg-muted/30 min-h-[36px] flex items-center text-foreground">
            <slot>{{ modelValue || '—' }}</slot>
        </div>
    </div>
</template>
