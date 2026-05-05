/**
 * Conflict resolution utilities for optimistic concurrency control.
 *
 * Uses 3-way merge: compares user's version and server's version against
 * the original version (snapshot taken when the form was loaded).
 * Only fields changed by BOTH sides are flagged as conflicts.
 */

export interface FieldConflict {
    field: string;
    label: string;
    section: string;
    myValue: unknown;
    serverValue: unknown;
    choice: 'mine' | 'theirs';
    /** Set when a dynamic question was removed or added by the server */
    status?: 'removed' | 'added';
}

/**
 * Human-readable labels and section groupings for activity fields.
 * Dotted paths (e.g. "evaluation.X") refer to nested object fields.
 */
const FIELD_META: Record<string, { label: string; section: string }> = {
    name: { label: 'Activity Name', section: 'General' },
    mitre_tactic: { label: 'MITRE Tactic', section: 'General' },
    mitre_technique: { label: 'MITRE Technique', section: 'General' },
    provider: { label: 'Provider', section: 'General' },
    priority: { label: 'Priority', section: 'General' },
    state: { label: 'State', section: 'General' },
    visible: { label: 'Visible', section: 'General' },
    activity_group_id: { label: 'Activity Group', section: 'General' },
    tags: { label: 'Tags', section: 'General' },
    linked_knowledge_base_articles: {
        label: 'Knowledge Base Articles',
        section: 'General',
    },

    activity_rationale: { label: 'Rationale', section: 'Activity Details' },
    activity_actions: { label: 'Actions', section: 'Activity Details' },
    activity_requirements: {
        label: 'Requirements',
        section: 'Activity Details',
    },
    activity_notes: { label: 'Activity Notes', section: 'Activity Details' },
    activity_start_time: { label: 'Start Time', section: 'Activity Details' },
    activity_end_time: { label: 'End Time', section: 'Activity Details' },
    sources: { label: 'Sources', section: 'Activity Details' },
    targets: { label: 'Targets', section: 'Activity Details' },
    tools: { label: 'Tools', section: 'Activity Details' },

    expected_logging: {
        label: 'Expected Logging',
        section: 'Expected Results',
    },
    expected_prevention: {
        label: 'Expected Prevention',
        section: 'Expected Results',
    },
    expected_alert_creation: {
        label: 'Expected Alert Creation',
        section: 'Expected Results',
    },
    expected_stakeholder_notification: {
        label: 'Expected Stakeholder Notification',
        section: 'Expected Results',
    },
    expected_severity: {
        label: 'Expected Severity',
        section: 'Expected Results',
    },
    log_sources: { label: 'Log Sources', section: 'Expected Results' },
    prevention_sources: {
        label: 'Prevention Sources',
        section: 'Expected Results',
    },
    alert_sources: { label: 'Alert Sources', section: 'Expected Results' },
    stakeholder_notification_sources: {
        label: 'Stakeholder Notification Sources',
        section: 'Expected Results',
    },

    logged: { label: 'Logged', section: 'Detection Results' },
    log_time: { label: 'Log Time', section: 'Detection Results' },
    log_notes: { label: 'Log Notes', section: 'Detection Results' },
    prevented: { label: 'Prevented', section: 'Detection Results' },
    prevent_time: { label: 'Prevent Time', section: 'Detection Results' },
    prevent_notes: { label: 'Prevent Notes', section: 'Detection Results' },
    alerted: { label: 'Alerted', section: 'Detection Results' },
    alert_severity: { label: 'Alert Severity', section: 'Detection Results' },
    alert_time: { label: 'Alert Time', section: 'Detection Results' },
    alert_notes: { label: 'Alert Notes', section: 'Detection Results' },
    stakeholder_notification_created: {
        label: 'Stakeholder Notification',
        section: 'Detection Results',
    },
    stakeholder_notification_severity: {
        label: 'Stakeholder Severity',
        section: 'Detection Results',
    },
    stakeholder_notification_time: {
        label: 'Stakeholder Time',
        section: 'Detection Results',
    },
    stakeholder_notification_notes: {
        label: 'Stakeholder Notes',
        section: 'Detection Results',
    },

    // Evaluation sub-fields (user-editable timing/severity results)
    'evaluation.event_to_alert_evaluation_result': {
        label: 'Event → Alert Result',
        section: 'Evaluation',
    },
    'evaluation.event_to_alert_data': {
        label: 'Event → Alert Data',
        section: 'Evaluation',
    },
    'evaluation.alert_to_stakeholder_evaluation_result': {
        label: 'Alert → Stakeholder Result',
        section: 'Evaluation',
    },
    'evaluation.alert_to_stakeholder_data': {
        label: 'Alert → Stakeholder Data',
        section: 'Evaluation',
    },
    'evaluation.alert_severity_evaluation_result': {
        label: 'Alert Severity Result',
        section: 'Evaluation',
    },
    'evaluation.alert_severity_data': {
        label: 'Alert Severity Data',
        section: 'Evaluation',
    },
    'evaluation.stakeholder_notification_severity_evaluation_result': {
        label: 'Stakeholder Severity Result',
        section: 'Evaluation',
    },
    'evaluation.stakeholder_notification_severity_data': {
        label: 'Stakeholder Severity Data',
        section: 'Evaluation',
    },
    // Dynamic questions are handled separately in computeConflicts — not listed here
};

/**
 * Fields to skip during diff computation — read-only or structural fields
 * that are not directly editable.
 */
const SKIP_FIELDS = new Set([
    'id',
    'deleted',
    'created_at',
    'updated_at',
    'activity_position',
    'activity_group',
    'files',
]);

/**
 * Fields that contain arrays of objects with an `id` property (assets, tags).
 * These need to be normalized to sorted ID arrays for comparison.
 */
const ID_ARRAY_FIELDS = new Set([
    'sources',
    'targets',
    'tools',
    'tags',
    'log_sources',
    'prevention_sources',
    'alert_sources',
    'stakeholder_notification_sources',
]);

/**
 * Read a possibly nested field value using dot notation.
 * e.g. getFieldValue(obj, "evaluation.event_to_alert_data")
 */
function getFieldValue(obj: Record<string, unknown>, field: string): unknown {
    const dotIdx = field.indexOf('.');
    if (dotIdx === -1) return obj[field];
    const parent = field.substring(0, dotIdx);
    const child = field.substring(dotIdx + 1);
    const parentObj = obj[parent];
    if (
        parentObj &&
        typeof parentObj === 'object' &&
        !Array.isArray(parentObj)
    ) {
        return (parentObj as Record<string, unknown>)[child];
    }
    return undefined;
}

/**
 * Set a possibly nested field value using dot notation.
 * Mutates the target object in place.
 */
function setFieldValue(
    obj: Record<string, unknown>,
    field: string,
    value: unknown,
): void {
    const dotIdx = field.indexOf('.');
    if (dotIdx === -1) {
        obj[field] = value;
        return;
    }
    const parent = field.substring(0, dotIdx);
    const child = field.substring(dotIdx + 1);
    if (!obj[parent] || typeof obj[parent] !== 'object') {
        obj[parent] = {};
    }
    (obj[parent] as Record<string, unknown>)[child] = value;
}

/**
 * Normalize a field value for comparison. For ID array fields (assets, tags),
 * extract IDs and sort them. For other fields, return as-is.
 */
function normalizeForComparison(field: string, value: unknown): unknown {
    if (ID_ARRAY_FIELDS.has(field) && Array.isArray(value)) {
        return value
            .map((item: any) =>
                typeof item === 'object' && item?.id
                    ? String(item.id)
                    : String(item),
            )
            .sort();
    }
    return value;
}

/**
 * Deep equality check for comparing field values.
 */
function isEmpty(v: unknown): boolean {
    if (v == null || v === '') return true;
    if (Array.isArray(v) && v.length === 0) return true;
    return false;
}

function deepEqual(a: unknown, b: unknown): boolean {
    if (a === b) return true;

    // Treat all empty-ish values as equivalent (null, undefined, '', [])
    if (isEmpty(a) && isEmpty(b)) return true;

    if (a == null || b == null) return false;
    if (typeof a !== typeof b) return false;

    if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length) return false;
        return a.every((val, i) => deepEqual(val, b[i]));
    }

    if (typeof a === 'object' && typeof b === 'object') {
        const keysA = Object.keys(a as Record<string, unknown>);
        const keysB = Object.keys(b as Record<string, unknown>);
        if (keysA.length !== keysB.length) return false;
        return keysA.every((key) =>
            deepEqual(
                (a as Record<string, unknown>)[key],
                (b as Record<string, unknown>)[key],
            ),
        );
    }

    return false;
}

/**
 * Compute field-level diffs between user's version and server's version.
 *
 * Every field where the two versions differ is shown to the user for review.
 * The original version is used to set smart defaults: if only I changed it,
 * default to "mine"; if only the server changed it, default to "theirs";
 * if both changed it, default to "mine".
 *
 * Supports dotted paths (e.g. "evaluation.X") for nested object fields.
 */
export function computeConflicts(
    myVersion: Record<string, unknown>,
    serverVersion: Record<string, unknown>,
    originalVersion: Record<string, unknown>,
): { conflicts: FieldConflict[]; autoMerged: Record<string, unknown> } {
    const conflicts: FieldConflict[] = [];
    // autoMerged is kept as a base but all differing fields will be in conflicts
    const autoMerged: Record<string, unknown> = JSON.parse(
        JSON.stringify(serverVersion),
    );

    for (const field of Object.keys(FIELD_META)) {
        if (SKIP_FIELDS.has(field)) continue;

        const originalVal = getFieldValue(originalVersion, field);
        const myVal = getFieldValue(myVersion, field);
        const serverVal = getFieldValue(serverVersion, field);

        const original = normalizeForComparison(field, originalVal);
        const mine = normalizeForComparison(field, myVal);
        const theirs = normalizeForComparison(field, serverVal);

        // Skip if both versions are the same
        if (deepEqual(mine, theirs)) continue;

        const meta = FIELD_META[field];
        if (!meta) continue;

        // Smart default: prefer "mine" if I changed it, "theirs" if only server changed it
        const iChangedIt = !deepEqual(original, mine);
        const defaultChoice: 'mine' | 'theirs' = iChangedIt ? 'mine' : 'theirs';

        conflicts.push({
            field,
            label: meta.label,
            section: meta.section,
            myValue: myVal,
            serverValue: serverVal,
            choice: defaultChoice,
        });
    }

    // Compare dynamic questions individually
    const myEval = (myVersion.evaluation as Record<string, unknown>) || {};
    const serverEval =
        (serverVersion.evaluation as Record<string, unknown>) || {};
    const originalEval =
        (originalVersion.evaluation as Record<string, unknown>) || {};

    const myQuestions = (myEval.dynamic_questions as any[]) || [];
    const serverQuestions = (serverEval.dynamic_questions as any[]) || [];
    const originalQuestions = (originalEval.dynamic_questions as any[]) || [];

    // Build lookup by template_id for each version
    const byTemplate = (qs: any[]) => {
        const map: Record<string, any> = {};
        for (const q of qs) map[q.evaluation_template_id] = q;
        return map;
    };
    const myQMap = byTemplate(myQuestions);
    const serverQMap = byTemplate(serverQuestions);
    const originalQMap = byTemplate(originalQuestions);

    // Collect all template IDs across all versions
    const allTemplateIds = new Set([
        ...Object.keys(myQMap),
        ...Object.keys(serverQMap),
    ]);

    for (const templateId of allTemplateIds) {
        const myQ = myQMap[templateId];
        const serverQ = serverQMap[templateId];
        const originalQ = originalQMap[templateId];
        if (!myQ && !serverQ) continue;

        // Detect added/removed questions
        const qStatus: 'removed' | 'added' | undefined =
            myQ && !serverQ ? 'removed' : !myQ && serverQ ? 'added' : undefined;

        // Compare evaluation_result
        const myResult = myQ?.evaluation_result ?? 'n/a';
        const serverResult = serverQ?.evaluation_result ?? 'n/a';
        const originalResult = originalQ?.evaluation_result ?? 'n/a';

        if (myResult !== serverResult) {
            const iChangedIt = originalResult !== myResult;
            const qName =
                myQ?.name ||
                serverQ?.name ||
                `Question ${myQ?.position ?? serverQ?.position ?? '?'}`;
            conflicts.push({
                field: `dq.${templateId}.evaluation_result`,
                label: `${qName} — Result`,
                section: 'Dynamic Questions',
                myValue: myResult,
                serverValue: serverResult,
                // Force "theirs" for removed questions (edit can't be applied)
                choice:
                    qStatus === 'removed'
                        ? 'theirs'
                        : iChangedIt
                          ? 'mine'
                          : 'theirs',
                status: qStatus,
            });
        }

        // Compare data
        const myData = myQ?.data ?? '';
        const serverData = serverQ?.data ?? '';
        const originalData = originalQ?.data ?? '';

        if (!deepEqual(myData, serverData)) {
            const iChangedIt = !deepEqual(originalData, myData);
            const qName =
                myQ?.name ||
                serverQ?.name ||
                `Question ${myQ?.position ?? serverQ?.position ?? '?'}`;
            conflicts.push({
                field: `dq.${templateId}.data`,
                label: `${qName} — Data`,
                section: 'Dynamic Questions',
                myValue: myData,
                serverValue: serverData,
                choice:
                    qStatus === 'removed'
                        ? 'theirs'
                        : iChangedIt
                          ? 'mine'
                          : 'theirs',
                status: qStatus,
            });
        }
    }

    return { conflicts, autoMerged };
}

/**
 * Build the final merged result from resolved conflicts.
 */
export function buildMergedResult(
    autoMerged: Record<string, unknown>,
    conflicts: FieldConflict[],
): Record<string, unknown> {
    const result = JSON.parse(JSON.stringify(autoMerged));

    for (const conflict of conflicts) {
        const value =
            conflict.choice === 'mine'
                ? conflict.myValue
                : conflict.serverValue;

        // Handle dynamic question fields: dq.<templateId>.<field>
        if (conflict.field.startsWith('dq.')) {
            const parts = conflict.field.split('.');
            const templateId = parts[1];
            const qField = parts[2];

            if (!qField) continue;

            const eval_ = result.evaluation as
                | Record<string, unknown>
                | undefined;
            if (eval_) {
                const questions = (eval_.dynamic_questions as any[]) || [];
                const q = questions.find(
                    (q: any) => q.evaluation_template_id === templateId,
                );
                if (q) {
                    q[qField] = value;
                }
            }
            continue;
        }

        setFieldValue(result, conflict.field, value);
    }

    return result;
}

/**
 * Optional lookup maps for resolving IDs to human-readable names.
 * Keys are field names, values are Maps from ID → display name.
 */
export type FieldDisplayLookups = Record<string, Map<string, string>>;

/**
 * Format a field value for display in the conflict dialog.
 * Handles scalars, arrays of objects with names (assets/tags), and dynamic questions.
 * When lookups are provided, resolves IDs to names for specific fields.
 */
export function formatFieldValue(
    value: unknown,
    fieldName?: string,
    lookups?: FieldDisplayLookups,
): string {
    // Resolve ID fields via lookups (e.g. activity_group_id → group name)
    if (fieldName && lookups?.[fieldName] && value != null) {
        const name = lookups[fieldName].get(String(value));
        if (name) return name;
    }

    // Evaluation result values — display as uppercase labels
    if (
        fieldName?.endsWith('.evaluation_result') &&
        typeof value === 'string'
    ) {
        return value.toUpperCase();
    }
    if (value === null || value === undefined) return '(empty)';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (typeof value === 'string') {
        if (value === '') return '(empty)';
        return value;
    }
    if (Array.isArray(value)) {
        if (value.length === 0) return '(none)';
        // Array of objects with name (assets, tags)
        if (typeof value[0] === 'object' && value[0]?.name) {
            return value.map((item: any) => item.name).join(', ');
        }
        // Array of strings (e.g. knowledge base articles)
        return value.join(', ');
    }
    if (typeof value === 'object') {
        return JSON.stringify(value, null, 2);
    }
    return String(value);
}
