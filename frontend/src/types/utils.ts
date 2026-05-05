/**
 * TypeScript utility types
 */

import type { GetAllActivitiesApiV1AssessmentsAssessmentIdActivityGetData } from './types.gen';

// Re-export all entity types from generated types
export type {
    AclBase,
    AclRead,
    AclRole,
    ActivityBase,
    ActivityEvaluationDynamicQuestionsRead,
    ActivityEvaluationDynamicQuestionsUpdate,
    ActivityEvaluationRead,
    ActivityEvaluationUpdate,
    ActivityGroupBase,
    ActivityGroupRead,
    ActivityGroupReorder,
    ActivityGroupTemplateRead,
    ActivityGroupUpdate,
    ActivityHistoryRead,
    ActivityPriority,
    ActivityRead,
    ActivityReorder,
    ActivitySeverity,
    ActivityState,
    ActivityTemplateRead,
    ActivityUpdate,
    AssetBase,
    AssetRead,
    AssessmentBase,
    AssessmentRead,
    AssessmentType,
    CampaignTemplateItemRead,
    CampaignTemplateRead,
    Configuration,
    DynamicEvaluationQuestionAssign,
    EvaluationTemplateRead,
    ExternalAuthProvider,
    FileCategory,
    FileRead,
    FileUploadResponse,
    ImportResponse,
    KnowledgeBaseRead,
    MessageResponse,
    ReportContextRequest,
    ReportGenerateRequest,
    ReportTemplateFormat,
    ReportTemplateRead,
    TacticBase,
    TacticWithTechniques,
    TagBase,
    TagRead,
    TechniqueBase,
    UserBase,
    UserCreate,
    UserPasswordReset,
    UserPasswordUpdate,
    UserRead,
    UserReadAcl,
    UserRole,
} from './types.gen';

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

// Filter types
export type ActivitySortField = NonNullable<
    NonNullable<
        GetAllActivitiesApiV1AssessmentsAssessmentIdActivityGetData['query']
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
