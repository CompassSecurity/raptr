<script setup lang="ts">
import { Check, ChevronsUpDown } from '@lucide/vue';
import { computed, ref } from 'vue';
import { toast } from 'vue-sonner';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from '@/components/ui/command';
import { Label } from '@/components/ui/label';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { usePreferencesStore } from '@/stores/preferences';

const preferencesStore = usePreferencesStore();

// Timezone combobox state
const timezoneOpen = ref(false);

const availableTimezones: string[] = (Intl as any).supportedValuesOf
    ? (Intl as any).supportedValuesOf('timeZone')
    : [];

const specialTimezones = [
    { value: 'Browser', label: 'Browser Default' },
    { value: 'UTC', label: 'UTC' },
];

const timezoneDisplayLabel = computed(() => {
    const value = preferencesStore.preferredTimezone;
    if (value === 'Browser') return 'Browser Default';
    if (value === 'UTC') return 'UTC';
    return value;
});

function selectTimezone(value: string) {
    preferencesStore.setPreferredTimezone(value);
    timezoneOpen.value = false;
    toast.success('Timezone updated');
}

function updateDateFormat(value: any) {
    preferencesStore.dateFormat = value;
    toast.success('Date format updated');
}

function updateTimeFormat(value: any) {
    preferencesStore.timeFormat = value;
    toast.success('Time format updated');
}

const dateFormats = [
    { value: 'browser', label: 'Browser Default' },
    { value: 'iso', label: 'ISO 8601 (YYYY-MM-DD)' },
    { value: 'us', label: 'US (MM/DD/YYYY)' },
    { value: 'eu', label: 'European (DD/MM/YYYY)' },
];

const timeFormats = [
    { value: 'browser', label: 'Browser Default' },
    { value: '12h', label: '12-hour (AM/PM)' },
    { value: '24h', label: '24-hour' },
];
</script>

<template>
    <Card>
        <CardHeader>
            <CardTitle>Time & Date Settings</CardTitle>
            <CardDescription>
                Customize how dates and times are displayed across the application.
            </CardDescription>
        </CardHeader>
        <CardContent class="space-y-6">
            <div class="space-y-2">
                <Label>Preferred Timezone</Label>
                <Popover v-model:open="timezoneOpen">
                    <PopoverTrigger as-child>
                        <Button
                            variant="outline"
                            role="combobox"
                            :aria-expanded="timezoneOpen"
                            class="w-full justify-between"
                        >
                            {{ timezoneDisplayLabel }}
                            <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent class="p-0" style="width: var(--reka-popper-anchor-width)">
                        <Command>
                            <CommandInput placeholder="Search timezone..." />
                            <CommandList>
                                <CommandEmpty>No timezone found.</CommandEmpty>
                                <CommandGroup heading="Quick Options">
                                    <CommandItem
                                        v-for="tz in specialTimezones"
                                        :key="tz.value"
                                        :value="tz.value"
                                        @select="selectTimezone(tz.value)"
                                    >
                                        <Check
                                            :class="cn(
                                                'mr-2 h-4 w-4',
                                                preferencesStore.preferredTimezone === tz.value ? 'opacity-100' : 'opacity-0'
                                            )"
                                        />
                                        {{ tz.label }}
                                    </CommandItem>
                                </CommandGroup>
                                <CommandGroup heading="All Timezones">
                                    <CommandItem
                                        v-for="tz in availableTimezones"
                                        :key="tz"
                                        :value="tz"
                                        @select="selectTimezone(tz)"
                                    >
                                        <Check
                                            :class="cn(
                                                'mr-2 h-4 w-4',
                                                preferencesStore.preferredTimezone === tz ? 'opacity-100' : 'opacity-0'
                                            )"
                                        />
                                        {{ tz }}
                                    </CommandItem>
                                </CommandGroup>
                            </CommandList>
                        </Command>
                    </PopoverContent>
                </Popover>
                <p class="text-sm text-muted-foreground">
                    This will override your browser's local timezone.
                </p>
            </div>

            <div class="space-y-2">
                <Label>Date Format</Label>
                <Select :model-value="preferencesStore.dateFormat" @update:model-value="updateDateFormat">
                     <SelectTrigger class="w-full">
                        <SelectValue placeholder="Select a date format" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem v-for="fmt in dateFormats" :key="fmt.value" :value="fmt.value">
                            {{ fmt.label }}
                        </SelectItem>
                    </SelectContent>
                </Select>
            </div>

            <div class="space-y-2">
                <Label>Time Format</Label>
                <Select :model-value="preferencesStore.timeFormat" @update:model-value="updateTimeFormat">
                     <SelectTrigger class="w-full">
                        <SelectValue placeholder="Select a time format" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem v-for="fmt in timeFormats" :key="fmt.value" :value="fmt.value">
                            {{ fmt.label }}
                        </SelectItem>
                    </SelectContent>
                </Select>
            </div>
        </CardContent>
    </Card>
</template>