export type InsightPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type InsightRisk = 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';
export type InsightOpportunity = 'MARGINAL' | 'MODERATE' | 'SIGNIFICANT' | 'TRANSFORMATIONAL';
export type InsightTrend = 'DECLINING' | 'STABLE' | 'GROWING' | 'EMERGING';

export interface NeuroInsights {
  priority: InsightPriority;
  risk: InsightRisk;
  opportunity: InsightOpportunity;
  trend: InsightTrend;
  confidence_score: number; // 0.0 to 1.0
  summary: string;
}

export type AgentStatus = 'IDLE' | 'PLANNING' | 'WAITING_APPROVAL' | 'EXECUTING' | 'DONE' | 'ERROR';

export interface HumanFeedback {
  approved: boolean;
  comments?: string;
  modified_plan?: any;
}
