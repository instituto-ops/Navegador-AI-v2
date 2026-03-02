from typing import Literal, Optional, TypedDict

InsightPriority = Literal['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
InsightRisk = Literal['NONE', 'LOW', 'MEDIUM', 'HIGH']
InsightOpportunity = Literal['MARGINAL', 'MODERATE', 'SIGNIFICANT', 'TRANSFORMATIONAL']
InsightTrend = Literal['DECLINING', 'STABLE', 'GROWING', 'EMERGING']

class NeuroInsights(TypedDict):
    priority: InsightPriority
    risk: InsightRisk
    opportunity: InsightOpportunity
    trend: InsightTrend
    confidence_score: float  # 0.0 to 1.0
    summary: str

AgentStatus = Literal['IDLE', 'PLANNING', 'WAITING_APPROVAL', 'EXECUTING', 'DONE', 'ERROR']

class HumanFeedback(TypedDict):
    approved: bool
    comments: Optional[str]
    modified_plan: Optional[list]
