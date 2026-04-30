/**
 * TypeScript utility types
 */

import type { components, operations } from './schema';

// Extract paginated response type
export type PaginatedResponse<T> = {
    items: T[];
    total: number;
    page: number;
    size: number;
    pages: number;
};

// Column filter value - can be a single value or array for multi-select
export type ColumnFilterValue = string | string[] | boolean | boolean[];

// Column filters map - field name to filter value(s)
export type ColumnFilters = Record<string, ColumnFilterValue>;

// Pagination parameters
export type PaginationParams = {
    offset?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    filters?: ColumnFilters;
};

// Pagination state
export type PaginationState = {
    total: number;
    page: number;
    size: number;
    pages: number;
};

// Common entity types
export type AssessmentRead = components['schemas']['AssessmentRead'];
export type AssessmentBase = components['schemas']['AssessmentBase'];
export type ActivityRead = components['schemas']['ActivityRead'];
export type ActivityBase = components['schemas']['ActivityBase'];
export type ActivityUpdate = components['schemas']['ActivityUpdate'];
export type ActivityGroupRead = components['schemas']['ActivityGroupRead'];
export type ActivityGroupBase = components['schemas']['ActivityGroupBase'];
export type ActivityGroupUpdate = components['schemas']['ActivityGroupUpdate'];
export type ActivityHistoryRead = components['schemas']['ActivityHistoryRead'];
export type TagRead = components['schemas']['TagRead'];
export type TagBase = components['schemas']['TagBase'];
export type UserRead = components['schemas']['UserRead'];
export type UserReadAcl = components['schemas']['UserReadAcl'];
export type UserCreate = components['schemas']['UserCreate'];
export type UserBase = components['schemas']['UserBase'];
export type UserPasswordReset = components['schemas']['UserPasswordReset'];
export type MessageResponse = components['schemas']['MessageResponse'];
export type AclRead = components['schemas']['AclRead'];
export type AclBase = components['schemas']['AclBase'];
export type AclRole = components['schemas']['AclRole'];
export type AssetRead = components['schemas']['AssetRead'];
export type AssetBase = components['schemas']['AssetBase'];
export type TacticBase = components['schemas']['TacticBase'];
export type TechniqueBase = components['schemas']['TechniqueBase'];
export type TacticWithTechniques =
    components['schemas']['TacticWithTechniques'];
export type ExternalAuthProvider =
    components['schemas']['ExternalAuthProvider'];
export type ActivityTemplateRead =
    components['schemas']['ActivityTemplateRead'];
export type ActivityGroupTemplateRead =
    components['schemas']['ActivityGroupTemplateRead'];
export type KnowledgeBaseRead = components['schemas']['KnowledgeBaseRead'];
export type ActivityEvaluationUpdate =
    components['schemas']['ActivityEvaluationUpdate'];
export type ActivityEvaluationRead =
    components['schemas']['ActivityEvaluationRead'];
export type ActivityEvaluationDynamicQuestionsRead =
    components['schemas']['ActivityEvaluationDynamicQuestionsRead'];
export type ActivityEvaluationDynamicQuestionsUpdate =
    components['schemas']['ActivityEvaluationDynamicQuestionsUpdate'];
export type EvaluationTemplateRead =
    components['schemas']['EvaluationTemplateRead'];
export type DynamicEvaluationQuestionAssign =
    components['schemas']['DynamicEvaluationQuestionAssign'];
export type ActivityGroupReorder =
    components['schemas']['ActivityGroupReorder'];
export type ActivityReorder = components['schemas']['ActivityReorder'];
export type FileRead = components['schemas']['FileRead'];
export type FileUploadResponse = components['schemas']['FileUploadResponse'];
export type FileCategory = components['schemas']['FileCategory'];
export type ImportResponse = components['schemas']['ImportResponse'];

// Campaign template types
export type CampaignTemplateRead =
    components['schemas']['CampaignTemplateRead'];
export type CampaignTemplateItemRead =
    components['schemas']['CampaignTemplateItemRead'];

// Report types
export type ReportTemplateRead = components['schemas']['ReportTemplateRead'];
export type ReportTemplateFormat =
    components['schemas']['ReportTemplateFormat'];
export type ReportGenerateRequest =
    components['schemas']['ReportGenerateRequest'];
export type ReportContextRequest =
    components['schemas']['ReportContextRequest'];

// Enum types
export type ActivityPriority = components['schemas']['ActivityPriority'];
export type ActivityState = components['schemas']['ActivityState'];
export type ActivitySeverity = components['schemas']['ActivitySeverity'];
export type UserRole = components['schemas']['UserRole'];
export type AssessmentType = components['schemas']['AssessmentType'];

// Filter types
export type ActivitySortField = NonNullable<
    NonNullable<
        operations['get_all_activities_api_v1_assessments__assessment_id__activity__get']['parameters']['query']
    >['sort_by']
>;

// Statistics types (manually defined until backend schema is regenerated via update:api)
export type StateDistributionItem = { state: string; count: number };
export type PriorityBreakdownItem = { priority: string; count: number };
export type PriorityAverageScoreItem = {
    priority: string;
    average_score: number | null;
};

export type MitreTechniqueScoreItem = {
    technique: string;
    overall_score: number | null;
    expected_logged_score: number | null;
    logged_score: number | null;
    expected_prevented_score: number | null;
    prevented_score: number | null;
    expected_alerted_score: number | null;
    alerted_score: number | null;
    expected_stakeholder_notified_score: number | null;
    stakeholder_notified_score: number | null;
};

export type MitreOverallTacticScoreItem = {
    tactic: string;
    overall_score: number | null;
    expected_logged_score: number | null;
    logged_score: number | null;
    expected_prevented_score: number | null;
    prevented_score: number | null;
    expected_alerted_score: number | null;
    alerted_score: number | null;
    expected_stakeholder_notified_score: number | null;
    stakeholder_notified_score: number | null;
};

export type MitreTacticScoreItem = {
    tactic: string;
    techniques: MitreTechniqueScoreItem[];
};

export type MeanTimeMetricsItem = {
    priority: string;
    mean_time_to_detect_seconds: number | null;
    mean_time_to_respond_seconds: number | null;
};

export type SeverityAccuracyItem = {
    expected_severity: string;
    actual_informational: number;
    actual_low: number;
    actual_medium: number;
    actual_high: number;
    actual_critical: number;
    actual_none: number;
};

export type AssessmentStatisticsResponse = {
    state_distribution: StateDistributionItem[];
    priority_breakdown: PriorityBreakdownItem[];
    average_coverage_score: number | null;
    average_coverage_scores_by_priority: PriorityAverageScoreItem[];
    mitre_overall_tactic_scores: MitreOverallTacticScoreItem[];
    mitre_tactic_scores: MitreTacticScoreItem[];
    mean_time_metrics: MeanTimeMetricsItem[];
    severity_accuracy: SeverityAccuracyItem[];
};

// Helper to make all properties optional (Partial alternative)
export type DeepPartial<T> = {
    [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// Pick only the ID from an entity
export type EntityId<T extends { id: string }> = Pick<T, 'id'>;

// Omit common audit fields
export type OmitAuditFields<T> = Omit<
    T,
    'id' | 'deleted' | 'created_at' | 'updated_at'
>;
