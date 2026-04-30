<script setup lang="ts">
import { ref, computed } from 'vue';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Check, ChevronsUpDown } from 'lucide-vue-next';
import { cn } from '@/lib/utils';


interface Option {
    value: string;
    label: string;
}

const props = withDefaults(defineProps<{
    modelValue?: string | null;
    options: Option[];
    placeholder?: string;
    searchPlaceholder?: string;
    emptyMessage?: string;
    clearable?: boolean;
    disabled?: boolean;
}>(), {
    clearable: true,
});

const emit = defineEmits<{
    'update:modelValue': [value: string | null];
}>();

const open = ref(false);
const searchQuery = ref('');

const filteredOptions = computed(() => {
    if (!searchQuery.value) {
        return props.options;
    }

    const query = searchQuery.value.toLowerCase();
    return props.options.filter((option) =>
        option.label.toLowerCase().includes(query) ||
        option.value.toLowerCase().includes(query)
    );
});

const selectedLabel = computed(() => {
    if (!props.modelValue) return props.placeholder || 'Select...';
    const option = props.options.find((opt) => opt.value === props.modelValue);
    return option ? option.label : props.placeholder || 'Select...';
});

function selectOption(value: string) {
    emit('update:modelValue', value);
    open.value = false;
    searchQuery.value = '';
}

function clearSelection() {
    emit('update:modelValue', null);
    open.value = false;
    searchQuery.value = '';
}

</script>

<template>
    <Popover v-model:open="open">
        <PopoverTrigger as-child>
            <Button
                variant="outline"
                role="combobox"
                :aria-expanded="open"
                :disabled="disabled"
                class="w-full justify-between font-normal"
            >
                <span class="truncate">{{ selectedLabel }}</span>
                <ChevronsUpDown class="h-4 w-4 shrink-0 opacity-50 ml-2" />
            </Button>
        </PopoverTrigger>
        <PopoverContent class="w-[var(--reka-popper-anchor-width)] p-0" align="start">
            <div class="flex flex-col">
                <div class="p-2 border-b">
                    <Input
                        v-model="searchQuery"
                        :placeholder="searchPlaceholder || 'Search...'"
                        class="h-9"
                        @keydown.escape="open = false"
                    />
                </div>
                <div class="max-h-[300px] overflow-y-auto p-1">
                    <button
                        v-if="modelValue && clearable"
                        type="button"
                        class="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground text-muted-foreground italic border-b mb-1"
                        @click="clearSelection"
                    >
                        <span class="truncate">Clear selection</span>
                    </button>
                    <div
                        v-if="filteredOptions.length === 0"
                        class="py-6 text-center text-sm text-muted-foreground"
                    >
                        {{ emptyMessage || 'No results found.' }}
                    </div>
                    <button
                        v-for="option in filteredOptions"
                        :key="option.value"
                        type="button"
                        class="relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                        :class="
                            cn(
                                'justify-between',
                                modelValue === option.value && 'bg-accent'
                            )
                        "
                        @click="selectOption(option.value)"
                    >
                        <span class="truncate">{{ option.label }}</span>
                        <Check
                            v-if="modelValue === option.value"
                            class="h-4 w-4 shrink-0"
                        />
                    </button>
                </div>
            </div>
        </PopoverContent>
    </Popover>
</template>
