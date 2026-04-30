<script setup lang="ts">
import { Button } from '@/components/ui/button';

const props = defineProps<{
    modelValue: string;
    disabled?: boolean;
}>();

const emit = defineEmits<{
    (e: 'update:modelValue', value: string): void;
}>();

function select(value: string) {
    if (props.disabled) return;
    emit('update:modelValue', value);
}
</script>

<template>
    <div class="inline-flex rounded-md" :class="{ 'pointer-events-none': disabled }" role="group">
        <Button
            type="button"
            size="sm"
            :class="[
                'rounded-r-none border-r-0 px-3 text-xs font-medium focus:z-10',
                modelValue === 'pass'
                    ? 'bg-green-600 text-white hover:bg-green-700 border-green-600'
                    : 'bg-background text-muted-foreground hover:bg-accent border'
            ]"
            @click="select('pass')"
        >
            Pass
        </Button>
        <Button
            type="button"
            size="sm"
            :class="[
                'rounded-none px-3 text-xs font-medium focus:z-10',
                modelValue === 'n/a'
                    ? 'bg-muted text-foreground hover:bg-muted/80 border-muted'
                    : 'bg-background text-muted-foreground hover:bg-accent border-y'
            ]"
            @click="select('n/a')"
        >
            N/A
        </Button>
        <Button
            type="button"
            size="sm"
            :class="[
                'rounded-l-none border-l-0 px-3 text-xs font-medium focus:z-10',
                modelValue === 'fail'
                    ? 'bg-red-600 text-white hover:bg-red-700 border-red-600'
                    : 'bg-background text-muted-foreground hover:bg-accent border'
            ]"
            @click="select('fail')"
        >
            Fail
        </Button>
    </div>
</template>
