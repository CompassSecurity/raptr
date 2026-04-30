import { useStorage } from '@vueuse/core';
import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

export type DateFormat = 'browser' | 'iso' | 'us' | 'eu';
export type TimeFormat = 'browser' | '12h' | '24h';

export const usePreferencesStore = defineStore('preferences', () => {
    // Persistent State
    const preferredTimezone = useStorage<string>(
        'raptr-preferred-timezone',
        'Browser',
    );
    const dateFormat = useStorage<DateFormat>('raptr-date-format', 'browser');
    const timeFormat = useStorage<TimeFormat>('raptr-time-format', 'browser');

    // 'local' here means "Use Preferred Timezone", 'utc' means "Force UTC"
    const quickToggleState = useStorage<'local' | 'utc'>(
        'raptr-timezone-mode',
        'local',
    );

    // Auto-refresh settings
    const autoRefreshEnabled = useStorage<boolean>(
        'raptr-auto-refresh-enabled',
        false,
    );
    const autoRefreshInterval = useStorage<number>(
        'raptr-auto-refresh-interval',
        30,
    ); // seconds
    const manualRefreshTrigger = ref(Date.now());
    const columnVisibility = useStorage<Record<string, boolean>>(
        'raptr-column-visibility',
        {
            name: true,
            activity_group: false,
            mitre_tactic: true,
            mitre_technique: true,
            priority: true,
            state: true,
            start_time: false,
            end_time: false,
            tags: true,
            created_at: false,
            updated_at: false,
            activity_coverage_score: false,
            visible: true,
        },
        undefined,
        { mergeDefaults: true },
    );

    // Activity table view mode
    const activityViewMode = useStorage<'grouped' | 'flat'>(
        'raptr-activity-view-mode',
        'grouped',
    );

    // Activity table filters
    const activityTableFilters = useStorage<{
        name: string;
        mitre_tactic: string;
        mitre_technique: string;
        priority: string[];
        state: string[];
        tags: string[];
        visible: boolean | null;
    }>(
        'raptr-activity-table-filters',
        {
            name: '',
            mitre_tactic: '',
            mitre_technique: '',
            priority: [],
            state: [],
            tags: [],
            visible: null,
        },
        undefined,
        { mergeDefaults: true },
    );

    // Computed
    const effectiveTimezone = computed(() => {
        if (quickToggleState.value === 'utc') {
            return 'UTC';
        }
        return preferredTimezone.value === 'Browser'
            ? undefined
            : preferredTimezone.value;
    });

    // Actions
    function toggleTimezoneMode() {
        quickToggleState.value =
            quickToggleState.value === 'local' ? 'utc' : 'local';
    }

    function setPreferredTimezone(timezone: string) {
        preferredTimezone.value = timezone;
    }

    function setDateFormat(format: DateFormat) {
        dateFormat.value = format;
    }

    function setTimeFormat(format: TimeFormat) {
        timeFormat.value = format;
    }

    function setAutoRefreshEnabled(enabled: boolean) {
        autoRefreshEnabled.value = enabled;
    }

    function setAutoRefreshInterval(interval: number) {
        autoRefreshInterval.value = interval;
    }

    function triggerManualRefresh() {
        manualRefreshTrigger.value = Date.now();
    }

    function setActivityViewMode(mode: 'grouped' | 'flat') {
        activityViewMode.value = mode;
    }

    return {
        // State
        preferredTimezone,
        dateFormat,
        timeFormat,
        quickToggleState, // Exposed for TopBar if needed explicitly, but effectiveTimezone is main consumer
        timezoneMode: quickToggleState, // Alias for backward compatibility if needed temporarily, but we'll refactor logic
        autoRefreshEnabled,
        autoRefreshInterval,
        manualRefreshTrigger,
        columnVisibility,
        activityViewMode,
        activityTableFilters,

        // Computed
        effectiveTimezone,

        // Actions
        toggleTimezoneMode,
        setPreferredTimezone,
        setDateFormat,
        setTimeFormat,
        setAutoRefreshEnabled,
        setAutoRefreshInterval,
        triggerManualRefresh,
        setActivityViewMode,
    };
});
