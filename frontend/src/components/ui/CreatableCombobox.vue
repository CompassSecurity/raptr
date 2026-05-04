<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Check, ChevronsUpDown } from 'lucide-vue-next';
import { cn } from '@/lib/utils';

const props = withDefaults(
    defineProps<{
        modelValue: string;
        options: string[];
        placeholder?: string;
        searchPlaceholder?: string;
        disabled?: boolean;
    }>(),
    {
        placeholder: 'Select or create...',
        searchPlaceholder: 'Search or type...',
    },
);

const emit = defineEmits<{
    'update:modelValue': [value: string];
}>();

const open = ref(false);
const searchQuery = ref('');

// When opening, reset search to current value
watch(open, (isOpen) => {
    if (isOpen) {
        searchQuery.value = props.modelValue || '';
    }
});

const filteredOptions = computed(() => {
    if (!searchQuery.value) return props.options;
    const query = searchQuery.value.toLowerCase();
    return props.options.filter((opt) => opt.toLowerCase().includes(query));
});

const showCreateOption = computed(() => {
    if (!searchQuery.value) return false;
    // Don't show create if exact match exists (case-insensitive)
    const query = searchQuery.value.toLowerCase();
    return !props.options.some((opt) => opt.toLowerCase() === query);
});

function selectOption(value: string) {
    emit('update:modelValue', value);
    open.value = false;
}
</script>

<template>
    <div class="relative w-full">
        <Popover v-model:open="open">
            <PopoverTrigger as-child>
                <Button
                    variant="outline"
                    role="combobox"
                    :aria-expanded="open"
                    :disabled="disabled"
                    class="w-full justify-between font-normal px-3"
                    :class="!modelValue && 'text-muted-foreground'"
                >
                    <span class="truncate">{{ modelValue || placeholder }}</span>
                    <ChevronsUpDown class="h-4 w-4 shrink-0 opacity-50 ml-2" />
                </Button>
            </PopoverTrigger>
            <PopoverContent class="w-[var(--reka-popper-anchor-width)] p-0" align="start">
                <div class="flex flex-col">
                    <div class="p-2 border-b">
                        <Input
                            v-model="searchQuery"
                            :placeholder="searchPlaceholder"
                            class="h-9"
                            @keydown.escape="open = false"
                            @keydown.enter.prevent="searchQuery ? selectOption(searchQuery) : null"
                        />
                    </div>
                    <div class="max-h-[200px] overflow-y-auto p-1">
                        <button
                            v-if="showCreateOption"
                            type="button"
                            class="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground border-b mb-1 font-medium text-primary"
                            @click="selectOption(searchQuery)"
                        >
                            <span class="truncate">Create "{{ searchQuery }}"</span>
                        </button>
                        
                        <div
                            v-if="filteredOptions.length === 0 && !showCreateOption"
                            class="py-4 text-center text-sm text-muted-foreground"
                        >
                            No results found.
                        </div>
                        
                        <button
                            v-for="option in filteredOptions"
                            :key="option"
                            type="button"
                            class="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                            :class="cn('justify-between', modelValue === option && 'bg-accent')"
                            @click="selectOption(option)"
                        >
                            <span class="truncate">{{ option }}</span>
                            <Check
                                v-if="modelValue === option"
                                class="h-4 w-4 shrink-0"
                            />
                        </button>
                    </div>
                </div>
            </PopoverContent>
        </Popover>
    </div>
</template>
