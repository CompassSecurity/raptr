import type { Ref } from 'vue';
import { computed, watch } from 'vue';
import type { ActivityEvaluationUpdate, ActivityRead } from '@/types/utils';

export type EvalResult = 'PASS' | 'FAIL' | 'N/A';

export function formatTimeDiff(
    fromTime: string | Date | null | undefined,
    toTime: string | Date | null | undefined,
): string {
    if (!fromTime || !toTime) return '';
    const from = new Date(fromTime).getTime();
    const to = new Date(toTime).getTime();
    if (Number.isNaN(from) || Number.isNaN(to)) return '';
    const diffMs = to - from;
    if (diffMs < 0) return 'N/A (negative)';
    const totalSeconds = Math.floor(diffMs / 1000);
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    const parts: string[] = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    if (seconds > 0 || parts.length === 0) parts.push(`${seconds}s`);
    return parts.join(' ');
}

export function evalBadgeClass(result: string): string {
    if (result === 'PASS') return 'bg-green-600 text-white border-green-600';
    if (result === 'FAIL') return 'bg-red-600 text-white border-red-600';
    return 'bg-muted text-muted-foreground border-border';
}

function evalResultToWire(result: EvalResult): 'pass' | 'fail' | 'n/a' {
    if (result === 'PASS') return 'pass';
    if (result === 'FAIL') return 'fail';
    return 'n/a';
}

function evalStatus(
    expected: boolean | null | undefined,
    actual: boolean | null | undefined,
): EvalResult {
    if (!expected) return 'N/A';
    return actual ? 'PASS' : 'FAIL';
}

export function useActivityEvaluation(formData: Ref<Partial<ActivityRead>>) {
    // Auto-calculated timing values (includes state-based messages)
    const eventToAlertData = computed(() => {
        if (!formData.value.alerted) return 'No alert generated';
        const hasStart = !!formData.value.activity_start_time;
        const hasAlert = !!formData.value.alert_time;
        if (!hasStart && !hasAlert)
            return 'Alert created but start time and alert time missing';
        if (!hasStart) return 'Alert created but start time missing';
        if (!hasAlert) return 'Alert created but alert time missing';
        return (
            formatTimeDiff(
                formData.value.activity_start_time,
                formData.value.alert_time,
            ) || ''
        );
    });
    const alertToStakeholderData = computed(() => {
        if (!formData.value.stakeholder_notification_created)
            return 'No notification created';
        const hasAlertTime = !!formData.value.alert_time;
        const hasNotifTime = !!formData.value.stakeholder_notification_time;
        if (!hasAlertTime && !hasNotifTime)
            return 'Stakeholder notified but alert time and notification time missing';
        if (!hasAlertTime) return 'Stakeholder notified but alert time missing';
        if (!hasNotifTime)
            return 'Stakeholder notified but notification time missing';
        return (
            formatTimeDiff(
                formData.value.alert_time,
                formData.value.stakeholder_notification_time,
            ) || ''
        );
    });

    // Only overwrite a field if it's empty or was previously auto-calculated
    function canAutoFill(current: string | undefined | null): boolean {
        return !current || current.endsWith('(auto-calculated)');
    }

    // Sync auto-calculated values back into evaluation when source data changes
    watch(
        [eventToAlertData, alertToStakeholderData, () => formData.value.id],
        ([newEventToAlert, newAlertToStakeholder]) => {
            if (!formData.value.evaluation) return;
            const updates: Record<string, any> = {};

            const finalEventToAlert = newEventToAlert
                ? `${newEventToAlert} (auto-calculated)`
                : '';
            if (
                finalEventToAlert &&
                canAutoFill(formData.value.evaluation.event_to_alert_data) &&
                formData.value.evaluation.event_to_alert_data !==
                    finalEventToAlert
            ) {
                updates.event_to_alert_data = finalEventToAlert;
            }

            const finalAlertToStakeholder = newAlertToStakeholder
                ? `${newAlertToStakeholder} (auto-calculated)`
                : '';
            if (
                finalAlertToStakeholder &&
                canAutoFill(
                    formData.value.evaluation.alert_to_stakeholder_data,
                ) &&
                formData.value.evaluation.alert_to_stakeholder_data !==
                    finalAlertToStakeholder
            ) {
                updates.alert_to_stakeholder_data = finalAlertToStakeholder;
            }

            if (Object.keys(updates).length > 0) {
                formData.value.evaluation = {
                    ...formData.value.evaluation,
                    ...updates,
                };
            }
        },
        { immediate: true },
    );

    // Auto-calculated severity comparisons (includes state-based messages)
    const alertSeverityData = computed(() => {
        if (!formData.value.alerted) return 'No alert generated';
        const expected = formData.value.expected_severity;
        const actual = formData.value.alert_severity;
        if (!expected && !actual)
            return 'Alert created but expected severity and alert severity missing';
        if (!expected) return 'Alert created but expected severity missing';
        if (!actual) return 'Alert created but alert severity missing';
        return `Expected: ${expected}, Actual: ${actual}`;
    });
    const stakeholderSeverityData = computed(() => {
        if (!formData.value.stakeholder_notification_created)
            return 'No notification created';
        const expected = formData.value.expected_severity;
        const actual = formData.value.stakeholder_notification_severity;
        if (!expected && !actual)
            return 'Stakeholder notified but expected severity and notification severity missing';
        if (!expected)
            return 'Stakeholder notified but expected severity missing';
        if (!actual)
            return 'Stakeholder notified but notification severity missing';
        return `Expected: ${expected}, Actual: ${actual}`;
    });

    // Sync auto-calculated severity values back into evaluation
    watch(
        [alertSeverityData, stakeholderSeverityData, () => formData.value.id],
        ([newAlertSeverity, newStakeholderSeverity]) => {
            if (!formData.value.evaluation) return;
            const updates: Record<string, any> = {};

            const finalAlertSeverity = newAlertSeverity
                ? `${newAlertSeverity} (auto-calculated)`
                : '';
            if (
                finalAlertSeverity &&
                canAutoFill(formData.value.evaluation.alert_severity_data) &&
                formData.value.evaluation.alert_severity_data !==
                    finalAlertSeverity
            ) {
                updates.alert_severity_data = finalAlertSeverity;
            }

            const finalStakeholderSeverity = newStakeholderSeverity
                ? `${newStakeholderSeverity} (auto-calculated)`
                : '';
            if (
                finalStakeholderSeverity &&
                canAutoFill(
                    formData.value.evaluation
                        .stakeholder_notification_severity_data,
                ) &&
                formData.value.evaluation
                    .stakeholder_notification_severity_data !==
                    finalStakeholderSeverity
            ) {
                updates.stakeholder_notification_severity_data =
                    finalStakeholderSeverity;
            }

            if (Object.keys(updates).length > 0) {
                formData.value.evaluation = {
                    ...formData.value.evaluation,
                    ...updates,
                };
            }
        },
        { immediate: true },
    );

    // Detection evaluation statuses
    const loggedEvaluation = computed(() =>
        evalStatus(formData.value.expected_logging, formData.value.logged),
    );
    const preventedEvaluation = computed(() =>
        evalStatus(
            formData.value.expected_prevention,
            formData.value.prevented,
        ),
    );
    const alertedEvaluation = computed(() =>
        evalStatus(
            formData.value.expected_alert_creation,
            formData.value.alerted,
        ),
    );
    const stakeholderNotifiedEvaluation = computed(() =>
        evalStatus(
            formData.value.expected_stakeholder_notification,
            formData.value.stakeholder_notification_created,
        ),
    );

    // Coverage score
    const activityCoverageScore = computed(() => {
        const checks = [
            {
                expected: !!formData.value.expected_logging,
                actual: !!formData.value.logged,
            },
            {
                expected: !!formData.value.expected_prevention,
                actual: !!formData.value.prevented,
            },
            {
                expected: !!formData.value.expected_alert_creation,
                actual: !!formData.value.alerted,
            },
            {
                expected: !!formData.value.expected_stakeholder_notification,
                actual: !!formData.value.stakeholder_notification_created,
            },
        ];
        const expectedChecks = checks.filter((c) => c.expected);
        if (expectedChecks.length === 0) return 0;
        const passed = expectedChecks.filter((c) => c.actual).length;
        return Math.round((passed / expectedChecks.length) * 100);
    });

    // Timing & severity evaluation result statuses (from formData.evaluation)
    const eventToAlertEvalStatus = computed(() =>
        (
            (formData.value.evaluation as any)
                ?.event_to_alert_evaluation_result || 'N/A'
        ).toUpperCase(),
    );
    const alertToStakeholderEvalStatus = computed(() =>
        (
            (formData.value.evaluation as any)
                ?.alert_to_stakeholder_evaluation_result || 'N/A'
        ).toUpperCase(),
    );
    const alertSeverityEvalStatus = computed(() =>
        (
            (formData.value.evaluation as any)
                ?.alert_severity_evaluation_result || 'N/A'
        ).toUpperCase(),
    );
    const stakeholderSeverityEvalStatus = computed(() =>
        (
            (formData.value.evaluation as any)
                ?.stakeholder_notification_severity_evaluation_result || 'N/A'
        ).toUpperCase(),
    );

    // Evaluation save payload
    const evaluationPayload = computed<ActivityEvaluationUpdate>(() => ({
        logged_evaluation: evalResultToWire(loggedEvaluation.value),
        alerted_evaluation: evalResultToWire(alertedEvaluation.value),
        prevented_evaluation: evalResultToWire(preventedEvaluation.value),
        stakeholder_notified_evaluation: evalResultToWire(
            stakeholderNotifiedEvaluation.value,
        ),
        activity_coverage_score: activityCoverageScore.value,
        event_to_alert_data:
            formData.value.evaluation?.event_to_alert_data || '',
        event_to_alert_evaluation_result:
            (formData.value.evaluation as any)
                ?.event_to_alert_evaluation_result ?? 'n/a',
        alert_to_stakeholder_data:
            formData.value.evaluation?.alert_to_stakeholder_data || '',
        alert_to_stakeholder_evaluation_result:
            (formData.value.evaluation as any)
                ?.alert_to_stakeholder_evaluation_result ?? 'n/a',
        alert_severity_data:
            formData.value.evaluation?.alert_severity_data || '',
        alert_severity_evaluation_result:
            (formData.value.evaluation as any)
                ?.alert_severity_evaluation_result ?? 'n/a',
        stakeholder_notification_severity_data:
            formData.value.evaluation?.stakeholder_notification_severity_data ||
            '',
        stakeholder_notification_severity_evaluation_result:
            (formData.value.evaluation as any)
                ?.stakeholder_notification_severity_evaluation_result ?? 'n/a',
        dynamic_questions: (
            formData.value.evaluation?.dynamic_questions || []
        ).map((q: any) => ({
            evaluation_template_id: q.evaluation_template_id,
            data: q.data ?? null,
            evaluation_result: q.evaluation_result ?? 'n/a',
        })),
    }));

    return {
        eventToAlertData,
        alertToStakeholderData,
        alertSeverityData,
        stakeholderSeverityData,
        loggedEvaluation,
        preventedEvaluation,
        alertedEvaluation,
        stakeholderNotifiedEvaluation,
        activityCoverageScore,
        eventToAlertEvalStatus,
        alertToStakeholderEvalStatus,
        alertSeverityEvalStatus,
        stakeholderSeverityEvalStatus,
        evaluationPayload,
    };
}
