export type DateFormat = 'browser' | 'iso' | 'us' | 'eu';
export type TimeFormat = 'browser' | '12h' | '24h';

export interface FormatOptions {
    timezone?: string;
    dateFormat?: DateFormat;
    timeFormat?: TimeFormat;
}

// Server timestamps without an explicit offset (e.g. SQLite-backed responses)
// must be treated as UTC. JS's Date constructor would otherwise parse them as
// local time. Postgres responses include a "Z" suffix and are passed through.
const HAS_TZ_SUFFIX = /[zZ]|[+-]\d{2}:?\d{2}$/;

export function parseServerDate(value: string | Date): Date {
    if (value instanceof Date) return value;
    return new Date(HAS_TZ_SUFFIX.test(value) ? value : `${value}Z`);
}

export function formatDateTime(
    dateString: string | null | undefined,
    timezone?: string,
    dateFormat: DateFormat = 'browser',
    timeFormat: TimeFormat = 'browser',
): string {
    if (!dateString) return '-';

    const date = parseServerDate(dateString);
    if (Number.isNaN(date.getTime())) return 'Invalid Date';

    const hour12 = timeFormat === 'browser' ? undefined : timeFormat === '12h';

    // Handle Custom Formats
    if (dateFormat === 'iso') {
        return formatCheck(
            date,
            timezone,
            {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                hour12: hour12 ?? false, // Default ISO is 24h usually, but if user forces 12h, we respect it? No, ISO implies 24h. Stay 24h for ISO structure unless explicitly asked. The user asked for "24h or AM/PM". ISO usually means strict format. Let's keep existing behavior for ISO but allow override if user REALLY wants. Actually, existing code had hour12: false hardcoded. Let's stick to that unless we want to break ISO spec visual style.
                // But wait, the previous code had `hour12: false`.
                // Let's keep logic simple: ISO format = standardized.
                // But if the user chooses '12h', showing ISO date with 12h time is weird.
                // Let's assume TimeFormat setting applies to 'browser', 'us', 'eu'.
                // For 'iso', let's stick to 24h as per ISO 8601, unless we want to support "ISO Date + 12h Time".
                // I'll keep ISO as 24h for now to be safe, or respect preference if passed?
                // Existing code: `hour12: false`.
                // I'll allow `hour12` to override if specific timeFormat is passed, consistent with others.
            },
            timeFormat,
        ).replace(/,/, '');
    }

    // Standard Options for Intl
    const options: Intl.DateTimeFormatOptions = {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: timezone === 'UTC' ? 'UTC' : timezone, // If timezone is undefined, uses local
        hour12: hour12,
    };

    if (dateFormat === 'us') {
        // MM/DD/YYYY
        options.month = '2-digit';
        options.day = '2-digit';
        // Force en-US locale for order, but keep other prefs
        return formatWithLocale(date, 'en-US', options, timezone);
    }

    if (dateFormat === 'eu') {
        // DD/MM/YYYY
        options.month = '2-digit';
        options.day = '2-digit';
        // Force en-GB or similar for DD/MM order
        return formatWithLocale(date, 'en-GB', options, timezone);
    }

    // Default 'browser' behavior
    const formatted = new Intl.DateTimeFormat(
        navigator.language,
        options,
    ).format(date);

    // Append timezone indicator
    const tzIndicator =
        timezone === 'UTC' ? 'UTC' : getLocalTimezoneAbbr(date, timezone);

    return `${formatted} (${tzIndicator})`;
}

function formatWithLocale(
    date: Date,
    locale: string,
    options: Intl.DateTimeFormatOptions,
    timezone?: string,
): string {
    // Ensure timezone is applied to options
    const opts = { ...options };
    if (timezone) opts.timeZone = timezone;
    const formatted = new Intl.DateTimeFormat(locale, opts).format(date);
    const tzIndicator =
        timezone === 'UTC' ? 'UTC' : getLocalTimezoneAbbr(date, timezone);
    return `${formatted} (${tzIndicator})`;
}

// Helper to standard formatting for ISO-like structure
function formatCheck(
    date: Date,
    timezone: string | undefined,
    options: Intl.DateTimeFormatOptions,
    timeFormat: TimeFormat,
): string {
    const opts = { ...options };
    if (timezone) opts.timeZone = timezone;

    // Override hour12 if timeFormat is explicit
    if (timeFormat !== 'browser') {
        opts.hour12 = timeFormat === '12h';
    }

    // sv-SE is used for ISO YYYY-MM-DD
    const formatted = new Intl.DateTimeFormat('sv-SE', opts).format(date);
    const tzIndicator =
        timezone === 'UTC' ? 'UTC' : getLocalTimezoneAbbr(date, timezone);
    return `${formatted} (${tzIndicator})`;
}

/**
 * Short label for the zone a timestamp is shown in ("UTC", "CET", …), so a
 * displayed time always says which clock it belongs to.
 */
export function getLocalTimezoneAbbr(date: Date, timezone?: string): string {
    try {
        const options: Intl.DateTimeFormatOptions = { timeZoneName: 'short' };
        if (timezone) options.timeZone = timezone;

        return (
            Intl.DateTimeFormat('default', options)
                .formatToParts(date)
                .find((part) => part.type === 'timeZoneName')?.value ||
            (timezone ? timezone : 'Local')
        );
    } catch {
        return timezone || 'Local';
    }
}
