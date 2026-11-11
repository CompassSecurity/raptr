<script setup lang="ts">
/**
 * Date/time picker: a trigger button showing the current value, opening a
 * calendar with typed hour and minute fields below it.
 *
 * The value is a ZonedDateTime throughout and only becomes a string at the
 * component boundary (a UTC ISO timestamp, as the API expects). Nothing parses
 * human-readable text, so the locale of the display can never change which
 * instant is stored.
 */
import { Calendar as CalendarIcon } from '@lucide/vue';
import {
    type DateValue,
    type ZonedDateTime,
    getLocalTimeZone,
    now,
    parseAbsolute,
    toTimeZone,
} from '@internationalized/date';
import type { HTMLAttributes } from 'vue';
import { computed, nextTick, ref, watch } from 'vue';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Input } from '@/components/ui/input';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import { usePreferencesStore } from '@/stores/preferences';
import { getLocalTimezoneAbbr } from '@/utils/dateFormatter';

const props = defineProps<{
    modelValue: string | null | undefined;
    disabled?: boolean;
    /** Overrides the default width cap, e.g. "max-w-none" to fill the parent */
    class?: HTMLAttributes['class'];
}>();

const emit = defineEmits<{
    (e: 'update:modelValue', value: string | null): void;
}>();

const preferencesStore = usePreferencesStore();

// Server timestamps without an explicit offset must be read as UTC, matching
// parseServerDate() in @/utils/dateFormatter
const HAS_TZ_SUFFIX = /[zZ]|[+-]\d{2}:?\d{2}$/;

const zone = computed(
    () => preferencesStore.effectiveTimezone ?? getLocalTimeZone(),
);

// The date-format preference picks the locale the value is rendered in;
// 'sv-SE' is the usual stand-in for ISO ordering
const LOCALE_BY_DATE_FORMAT: Record<string, string> = {
    iso: 'sv-SE',
    us: 'en-US',
    eu: 'en-GB',
};
const locale = computed(
    () =>
        LOCALE_BY_DATE_FORMAT[preferencesStore.dateFormat] ??
        navigator.language,
);

const use12h = computed(() => {
    if (preferencesStore.timeFormat === '12h') return true;
    if (preferencesStore.timeFormat === '24h') return false;
    return (
        new Intl.DateTimeFormat(locale.value, { hour: 'numeric' }).resolvedOptions()
            .hour12 ?? false
    );
});

function toZoned(value: string, timeZone: string): ZonedDateTime | undefined {
    try {
        return parseAbsolute(
            HAS_TZ_SUFFIX.test(value) ? value : `${value}Z`,
            timeZone,
        );
    } catch {
        return undefined;
    }
}

const value = computed<ZonedDateTime | undefined>(() =>
    props.modelValue ? toZoned(props.modelValue, zone.value) : undefined,
);

// Granularity is minutes, so never carry sub-minute noise into a stored value
function currentMinute() {
    return now(zone.value).set({ second: 0, millisecond: 0 });
}

function emitValue(next: ZonedDateTime | undefined) {
    emit('update:modelValue', next ? next.toDate().toISOString() : null);
}

const isOpen = ref(false);

// Which month the calendar opens on
const placeholder = ref<DateValue>(value.value ?? currentMinute());

watch(value, (val) => {
    if (val) placeholder.value = val;
});

watch(zone, (tz) => {
    placeholder.value = value.value ?? toTimeZone(currentMinute(), tz);
});

// --- Display ---

const timeZoneLabel = computed(() =>
    getLocalTimezoneAbbr(
        value.value?.toDate() ?? new Date(),
        preferencesStore.effectiveTimezone,
    ),
);

function displayFormat(): Intl.DateTimeFormatOptions {
    return {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: use12h.value,
        timeZone: zone.value,
    };
}

const displayValue = computed(() => {
    if (!value.value) return '';
    return new Intl.DateTimeFormat(locale.value, displayFormat()).format(
        value.value.toDate(),
    );
});

// Spell the expected shape out in the user's own locale, e.g. "DD.MM.YYYY HH:MM"
const TOKEN_BY_PART: Record<string, string> = {
    year: 'YYYY',
    month: 'MM',
    day: 'DD',
    minute: 'mm',
    dayPeriod: 'AM',
};
const formatHint = computed(() =>
    new Intl.DateTimeFormat(locale.value, displayFormat())
        .formatToParts(new Date(Date.UTC(2026, 1, 1, 14, 30)))
        .map((part) => {
            if (part.type === 'literal') return part.value;
            if (part.type === 'hour') return use12h.value ? 'hh' : 'HH';
            return TOKEN_BY_PART[part.type] ?? part.value;
        })
        .join(''),
);

// --- Time ---

const selectedHour = computed(() => {
    const h = value.value?.hour;
    if (h === undefined) return undefined;
    if (!use12h.value) return h;
    return h % 12 === 0 ? 12 : h % 12;
});

const selectedMinute = computed(() => value.value?.minute);
const isPm = computed(() => (value.value?.hour ?? 0) >= 12);

function setHour(hour: number) {
    const base = value.value ?? currentMinute();
    const next = use12h.value
        ? (hour % 12) + (isPm.value ? 12 : 0)
        : hour;
    emitValue(base.set({ hour: next }));
}

function setMinute(minute: number) {
    emitValue((value.value ?? currentMinute()).set({ minute }));
}

function setPeriod(period: 'AM' | 'PM') {
    const base = value.value ?? currentMinute();
    const h = base.hour % 12;
    emitValue(base.set({ hour: period === 'PM' ? h + 12 : h }));
}

// --- Typed hour/minute entry ---
//
// These are plain integers, not formatted text, so typing a time can never be
// misread the way a localized date string can.

const hourText = ref('');
const minuteText = ref('');
const hourFocused = ref(false);
const minuteFocused = ref(false);

const hourRange = computed(() => (use12h.value ? [1, 12] : [0, 23]));

function pad(n: number) {
    return n.toString().padStart(2, '0');
}

function syncHourText() {
    hourText.value = selectedHour.value === undefined ? '' : pad(selectedHour.value);
}

function syncMinuteText() {
    minuteText.value =
        selectedMinute.value === undefined ? '' : pad(selectedMinute.value);
}

// Only refresh a field the user is not currently typing into
watch(
    [value, use12h],
    () => {
        if (!hourFocused.value) syncHourText();
        if (!minuteFocused.value) syncMinuteText();
    },
    { immediate: true },
);

function clamp(n: number, min: number, max: number) {
    return Math.max(min, Math.min(n, max));
}

// The emitted value only comes back through props on a later tick, so show the
// committed number directly. Reading it back here would pick up the previous
// value and a following blur would write that stale number back.
function commitHour() {
    const parsed = Number.parseInt(hourText.value, 10);
    const [min, max] = hourRange.value;
    if (Number.isNaN(parsed)) return syncHourText();
    const next = clamp(parsed, min, max);
    setHour(next);
    hourText.value = pad(next);
}

function commitMinute() {
    const parsed = Number.parseInt(minuteText.value, 10);
    if (Number.isNaN(parsed)) return syncMinuteText();
    const next = clamp(parsed, 0, 59);
    setMinute(next);
    minuteText.value = pad(next);
}

const hourInput = ref<{ $el?: HTMLInputElement } | null>(null);
const minuteInput = ref<{ $el?: HTMLInputElement } | null>(null);

function selectInput(el: HTMLInputElement | undefined) {
    el?.focus();
    el?.select();
}

// Open straight into the hour field so a time can be typed without clicking
// first. This replaces the popover's own autofocus, which would otherwise land
// on the calendar.
function handleOpenAutoFocus(event: Event) {
    event.preventDefault();
    nextTick(() => selectInput(hourInput.value?.$el));
}

// Input handlers rather than watchers: these run only on real typing, so
// re-syncing the text from the value can never re-trigger the hand-off
function onHourInput(raw: string | number) {
    const digits = String(raw).replace(/\D/g, '').slice(0, 2);
    hourText.value = digits;
    // Two digits is a complete hour - commit it and move to the minutes
    if (digits.length === 2) {
        commitHour();
        selectInput(minuteInput.value?.$el);
    }
}

function onMinuteInput(raw: string | number) {
    minuteText.value = String(raw).replace(/\D/g, '').slice(0, 2);
}

// Enter accepts what was typed and dismisses the popover
function commitAndClose(commit: () => void) {
    commit();
    isOpen.value = false;
}

// The calendar only decides a day: carry the time across rather than letting it
// reset to midnight
function handleCalendarSelect(next: DateValue | undefined) {
    if (!next) return;
    const base = value.value ?? currentMinute();
    emitValue(base.set({ year: next.year, month: next.month, day: next.day }));
}

function setNow() {
    emitValue(currentMinute());
}
</script>

<template>
    <div :class="cn('flex w-full max-w-md items-center gap-2 lg:max-w-lg xl:max-w-xl 2xl:max-w-2xl', props.class)">
        <!-- modal: outside clicks dismiss the popover instead of reaching the
             control beneath, so a select underneath cannot open on top of it -->
        <Popover v-model:open="isOpen" modal>
            <PopoverTrigger as-child>
                <Button
                    variant="outline"
                    type="button"
                    :disabled="disabled"
                    :class="cn(
                        'h-9 flex-1 justify-start gap-2 px-3 font-normal',
                        !modelValue && 'text-muted-foreground',
                    )"
                >
                    <CalendarIcon class="h-4 w-4 shrink-0 opacity-70" />
                    <span class="truncate">{{ displayValue || formatHint }}</span>
                    <span class="ml-auto shrink-0 text-xs text-muted-foreground">{{ timeZoneLabel }}</span>
                </Button>
            </PopoverTrigger>

            <PopoverContent class="w-auto p-0" align="start" @open-auto-focus="handleOpenAutoFocus">
                <div class="p-3">
                    <Calendar
                        :model-value="value"
                        v-model:placeholder="placeholder"
                        :locale="locale"
                        @update:model-value="handleCalendarSelect"
                    />
                </div>

                <div class="space-y-2 border-t px-3 py-3">
                    <div class="flex items-center justify-between gap-4">
                        <span class="text-xs font-medium">Time</span>
                        <span class="text-xs text-muted-foreground">{{ timeZoneLabel }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                        <Input
                            :model-value="hourText"
                            inputmode="numeric"
                            maxlength="2"
                            :aria-label="`Hour (${hourRange[0]}-${hourRange[1]})`"
                            ref="hourInput"
                            :placeholder="use12h ? 'hh' : 'HH'"
                            class="h-8 w-12 px-1 text-center tabular-nums"
                            @update:model-value="onHourInput"
                            @focus="hourFocused = true; ($event.target as HTMLInputElement).select()"
                            @blur="hourFocused = false; commitHour()"
                            @keydown.enter.prevent="commitAndClose(commitHour)"
                        />
                        <span class="text-sm font-medium text-muted-foreground">:</span>
                        <Input
                            ref="minuteInput"
                            :model-value="minuteText"
                            inputmode="numeric"
                            maxlength="2"
                            aria-label="Minute (0-59)"
                            placeholder="mm"
                            class="h-8 w-12 px-1 text-center tabular-nums"
                            @update:model-value="onMinuteInput"
                            @focus="minuteFocused = true; ($event.target as HTMLInputElement).select()"
                            @blur="minuteFocused = false; commitMinute()"
                            @keydown.enter.prevent="commitAndClose(commitMinute)"
                        />
                        <div v-if="use12h" class="ml-2 flex items-center gap-1">
                            <Button
                                v-for="period in ['AM', 'PM'] as const"
                                :key="period"
                                type="button"
                                size="sm"
                                :variant="!!modelValue && (period === 'PM') === isPm ? 'default' : 'outline'"
                                class="h-8 px-2 text-xs"
                                @click="setPeriod(period)"
                            >
                                {{ period }}
                            </Button>
                        </div>
                    </div>
                </div>
            </PopoverContent>
        </Popover>

        <Button
            variant="outline"
            size="sm"
            class="h-9 shrink-0 px-3"
            type="button"
            :disabled="disabled"
            @click="setNow"
        >
            Now
        </Button>
    </div>
</template>
