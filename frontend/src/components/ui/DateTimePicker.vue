<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Calendar as CalendarIcon, Clock } from '@lucide/vue';
import {
  type DateValue,
  CalendarDate,
} from '@internationalized/date';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { usePreferencesStore } from '@/stores/preferences';
import { formatDateTime, formatDateTimeEditable, parseDateTimeInput } from '@/utils/dateFormatter';

const props = defineProps<{
  modelValue: string | null | undefined;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | null): void;
}>();

const preferencesStore = usePreferencesStore();

// Internal state
const dateValue = ref<DateValue | undefined>();
const timeValue = ref<string>('00:00'); // Always HH:mm 24h format for internal logic

// Helper: Parse UTC string to components in target timezone
function parseToTimezone(utcIsoString: string, timezone?: string) {
    const date = new Date(utcIsoString);
    if (isNaN(date.getTime())) return null;

    const opts: Intl.DateTimeFormatOptions = {
        timeZone: timezone,
        hourCycle: 'h23',
    };
    
    const formatter = new Intl.DateTimeFormat('en-US', {
        ...opts,
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
    });

    const parts = formatter.formatToParts(date);
    const getPart = (type: string) => {
        const val = parts.find(p => p.type === type)?.value;
        if (!val) return 0;
        const parsed = parseInt(val, 10);
        return isNaN(parsed) ? 0 : parsed;
    };

    let hour = getPart('hour');
    if (hour === 24) hour = 0;

    return {
        year: getPart('year'),
        month: getPart('month'),
        day: getPart('day'),
        hour: hour,
        minute: getPart('minute'),
    };
}

// Helper: Convert display components in timezone back to UTC ISO string
function toUtcIsoString(year: number, month: number, day: number, hours: number, minutes: number, timezone?: string): string {
    const isoLocal = `${year.toString().padStart(4, '0')}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}T${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:00`;

    if (timezone === 'UTC') {
        return `${isoLocal}Z`;
    }

    // If timezone is undefined, use browser's local timezone
    const effectiveTz = timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone;

    const tentativeUtc = new Date(Date.UTC(year, month - 1, day, hours, minutes));
    
    const longOffsetFormatter = new Intl.DateTimeFormat('en-US', {
        timeZone: effectiveTz,
        timeZoneName: 'longOffset'
    });
    
    const offsetPart = longOffsetFormatter.formatToParts(tentativeUtc).find(p => p.type === 'timeZoneName')?.value;
    
    if (offsetPart) {
         const match = offsetPart.match(/GMT([+-])(\d{1,2}):?(\d{2})?/);
         if (match) {
             const sign = match[1] === '+' ? 1 : -1;
             const offsetHours = parseInt(match[2] || '0', 10);
             const offsetMinutes = parseInt(match[3] || '0', 10);
             const totalOffsetMinutes = sign * (offsetHours * 60 + offsetMinutes);
             
             const actualUtc = tentativeUtc.getTime() - (totalOffsetMinutes * 60 * 1000);
             
             return new Date(actualUtc).toISOString();
         }
    }
    
    return `${isoLocal}Z`;
}

function updateFromProps() {
    if (props.modelValue) {
        try {
            const components = parseToTimezone(props.modelValue, preferencesStore.effectiveTimezone);
            if (components) {
                dateValue.value = new CalendarDate(components.year, components.month, components.day);
                const h = components.hour.toString().padStart(2, '0');
                const m = components.minute.toString().padStart(2, '0');
                timeValue.value = `${h}:${m}`;
            }
        } catch (e) {
            console.error(e);
        }
    } else {
        dateValue.value = undefined;
        timeValue.value = '00:00';
    }
}

// Watchers
watch(() => props.modelValue, updateFromProps, { immediate: true });
watch(() => preferencesStore.effectiveTimezone, updateFromProps);

// Sync to modelValue
const updateModelValue = () => {
    if (dateValue.value) {
        const d = dateValue.value;
        const [hours = 0, minutes = 0] = timeValue.value.split(':').map(Number);
        
        const iso = toUtcIsoString(d.year, d.month, d.day, hours, minutes, preferencesStore.effectiveTimezone);
        emit('update:modelValue', iso);
    } else {
        emit('update:modelValue', null);
    }
};

const handleDateSelect = (val: DateValue | undefined) => {
    dateValue.value = val;
    updateModelValue();
};

const setNow = () => {
    const now = new Date();
    const components = parseToTimezone(now.toISOString(), preferencesStore.effectiveTimezone);
    
    if (components) {
        dateValue.value = new CalendarDate(components.year, components.month, components.day);
        const h = components.hour.toString().padStart(2, '0');
        const m = components.minute.toString().padStart(2, '0');
        timeValue.value = `${h}:${m}`;
        updateModelValue();
    }
};

const formattedDisplay = computed(() => {
    if (!props.modelValue) return 'Pick a date & time';
    return formatDateTime(
        props.modelValue,
        preferencesStore.effectiveTimezone,
        preferencesStore.dateFormat,
        preferencesStore.timeFormat,
    );
});

// --- Inline Text Editing ---

const isEditing = ref(false);
const editText = ref('');

function onInputFocus() {
    if (props.disabled) return;
    isEditing.value = true;
    editText.value = formatDateTimeEditable(
        props.modelValue,
        preferencesStore.effectiveTimezone,
        preferencesStore.dateFormat,
        preferencesStore.timeFormat,
    );
}

function commitEdit() {
    isEditing.value = false;
    const parsed = parseDateTimeInput(editText.value, preferencesStore.dateFormat);
    if (parsed) {
        // Update internal state and emit
        dateValue.value = new CalendarDate(parsed.year, parsed.month, parsed.day);
        timeValue.value = `${parsed.hour.toString().padStart(2, '0')}:${parsed.minute.toString().padStart(2, '0')}`;
        const iso = toUtcIsoString(parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute, preferencesStore.effectiveTimezone);
        emit('update:modelValue', iso);
    }
    // If parse fails, the input simply reverts to formattedDisplay on next render
}

function cancelEdit() {
    isEditing.value = false;
}

// --- Custom Time Input Logic ---

const isBrowser = computed(() => preferencesStore.timeFormat === 'browser');
const is12h = computed(() => preferencesStore.timeFormat === '12h');

// Validation Helpers
function clamp(val: number, min: number, max: number) {
    return Math.max(min, Math.min(val, max));
}

// Using local refs for inputs to allow "invalid" transient state while typing
const localHour = ref('');
const localMinute = ref('');

// Sync local refs when timeValue changes from other sources (e.g. Now button or prop)
watch(timeValue, (newVal) => {
    const parts = newVal.split(':');
    const h = parts[0] || '00';
    const m = parts[1] || '00';
    // Only update local refs if they aren't being focused/typed in?
    // We'll update them.
    
    // For 24h
    if (!is12h.value) {
        localHour.value = h;
    } else {
        // For 12h
        let hInt = parseInt(h, 10);
        if (hInt === 0) hInt = 12;
        else if (hInt > 12) hInt -= 12;
        localHour.value = hInt.toString().padStart(2, '0');
    }
    localMinute.value = m;
}, { immediate: true });

// Commit Handlers
const commit24h = () => {
    const h = parseInt(localHour.value || '0', 10);
    const m = parseInt(localMinute.value || '0', 10);
    const hClamped = clamp(h, 0, 23);
    const mClamped = clamp(m, 0, 59);
    
    timeValue.value = `${hClamped.toString().padStart(2, '0')}:${mClamped.toString().padStart(2, '0')}`;
    updateModelValue();
    // Refresh local vals
    localHour.value = hClamped.toString().padStart(2, '0');
    localMinute.value = mClamped.toString().padStart(2, '0');
};

const commit12h = () => {
    const h = parseInt(localHour.value || '0', 10);
    const m = parseInt(localMinute.value || '0', 10);
    let hClamped = clamp(h, 1, 12); // 1-12 range
    const mClamped = clamp(m, 0, 59);
    
    // Convert to 24h based on current period
    let h24 = hClamped;
    const isPM = period.value === 'PM';
    
    if (isPM && h24 < 12) h24 += 12;
    if (!isPM && h24 === 12) h24 = 0;
    
    timeValue.value = `${h24.toString().padStart(2, '0')}:${mClamped.toString().padStart(2, '0')}`;
    updateModelValue();
    
    // Refresh local vals (keep 12h format)
    localHour.value = hClamped.toString().padStart(2, '0');
    localMinute.value = mClamped.toString().padStart(2, '0');
};

// Period for 12h
const period = computed({
    get: () => {
        const parts = timeValue.value.split(':');
        const h = parseInt(parts[0] || '0', 10);
        return h >= 12 ? 'PM' : 'AM';
    },
    set: (val) => {
        const parts = timeValue.value.split(':');
        let h = parseInt(parts[0] || '0', 10);
        if (val === 'PM' && h < 12) h += 12;
        if (val === 'AM' && h >= 12) h -= 12;
        const hStr = h.toString().padStart(2, '0');
        const m = parts[1] || '00';
        timeValue.value = `${hStr}:${m}`;
        updateModelValue();
    }
});

</script>

<template>
  <div class="flex items-center gap-2">
    <Input
      :model-value="isEditing ? editText : formattedDisplay"
      @update:model-value="editText = String($event)"
      @focus="onInputFocus"
      @blur="commitEdit"
      @keydown.enter="($event.target as HTMLInputElement).blur()"
      @keydown.escape="cancelEdit(); ($event.target as HTMLInputElement).blur()"
      :disabled="disabled"
      :class="cn(
        'flex-1 text-left font-normal h-9',
        !modelValue && !isEditing && 'text-muted-foreground'
      )"
      placeholder="Pick a date & time"
    />
    <Popover>
      <PopoverTrigger as-child>
        <Button variant="outline" size="icon" class="h-9 w-9 shrink-0" :disabled="disabled">
          <CalendarIcon class="h-4 w-4" />
        </Button>
      </PopoverTrigger>
    <PopoverContent class="w-auto p-0">
      <div class="p-3 border-b border-border">
          <Calendar
            v-model="dateValue"
            mode="single"
            initial-focus
            @update:model-value="handleDateSelect"
          />
      </div>
      <div class="p-3">
          <Label class="text-xs mb-1 block">Time ({{ preferencesStore.effectiveTimezone === 'UTC' ? 'UTC' : 'Local' }})</Label>
          <div class="flex items-center gap-2">
              <Clock class="h-4 w-4 text-muted-foreground" />
              
              <!-- Browser Native -->
              <Input 
                v-if="isBrowser"
                type="time" 
                v-model="timeValue" 
                @change="updateModelValue"
                class="h-8 flex-1"
              />

              <!-- Custom 24h -->
              <div v-else-if="!is12h" class="flex items-center gap-1 flex-1">
                  <Input 
                    v-model="localHour" 
                    @blur="commit24h"
                    @keydown.enter="commit24h"
                    class="h-8 w-[50px] text-center px-1" 
                    placeholder="HH"
                    maxlength="2"
                  />
                  <span class="text-sm font-medium">:</span>
                  <Input 
                    v-model="localMinute" 
                    @blur="commit24h"
                    @keydown.enter="commit24h"
                    class="h-8 w-[50px] text-center px-1" 
                    placeholder="MM"
                    maxlength="2"
                  />
              </div>

              <!-- Custom 12h -->
              <div v-else class="flex items-center gap-1 flex-1">
                 <Input 
                    v-model="localHour" 
                    @blur="commit12h"
                    @keydown.enter="commit12h"
                    class="h-8 w-[50px] text-center px-1" 
                    placeholder="HH"
                    maxlength="2"
                  />
                  <span class="text-sm font-medium">:</span>
                  <Input 
                    v-model="localMinute" 
                    @blur="commit12h"
                    @keydown.enter="commit12h"
                    class="h-8 w-[50px] text-center px-1" 
                    placeholder="MM"
                    maxlength="2"
                  />
                  <Select v-model="period">
                      <SelectTrigger class="h-8 w-[65px] px-2">
                          <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                          <SelectItem value="AM">AM</SelectItem>
                          <SelectItem value="PM">PM</SelectItem>
                      </SelectContent>
                  </Select>
              </div>

              <Button size="sm" variant="outline" class="h-8 px-2 ml-auto" @click="setNow">
                  Now
              </Button>
          </div>
      </div>
    </PopoverContent>
    </Popover>
    <Button variant="outline" size="sm" class="h-9 px-3 shrink-0" :disabled="disabled" @click="setNow">
      Now
    </Button>
  </div>
</template>
