# ✅ FIXED — schemas.py

from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class Recommendation(str, Enum):
    STRONG_YES = "Strong Yes - Advance to Interview"
    YES        = "Yes - Schedule Interview"
    MAYBE      = "Maybe - Interview with Reservations"
    NO         = "No - Does Not Meet Requirements"
    STRONG_NO  = "Strong No - Significant Skills Gap"


class ScoreBreakdown(BaseModel):
    keyword:    float = Field(..., ge=0.0, le=1.0, description="Skill keyword overlap ratio")
    semantic:   float = Field(..., ge=0.0, le=1.0, description="Embedding cosine similarity")
    final:      float = Field(..., ge=0.0, le=1.0, description="Weighted composite score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence in evaluation")


class FeedbackDetail(BaseModel):
    summary:        str            = Field(..., description="2-3 sentence executive summary")
    strengths:      List[str]      = Field(..., description="Specific strengths with evidence")
    improvements:   List[str]      = Field(..., description="Actionable gaps to address")
    recommendation: Recommendation = Field(..., description="Hiring recommendation")


class AnalyzeResponse(BaseModel):
    scores:         ScoreBreakdown = Field(..., description="All scoring metrics")
    matched_skills: List[str]      = Field(..., description="Skills found in both resume and JD")
    missing_skills: List[str]      = Field(..., description="Skills in JD but absent from resume")
    feedback:       FeedbackDetail = Field(..., description="Structured recruiter-style feedback")

    class Config:
        use_enum_values = True
        
        
class CandidateResult(BaseModel):
    rank:           int
    filename:       str
    scores:         ScoreBreakdown
    matched_skills: List[str]
    missing_skills: List[str]
    feedback:       FeedbackDetail
    class Config:
        use_enum_values = True

class BatchAnalyzeResponse(BaseModel):
    total_candidates: int
    job_description:  str
    candidates:       List[CandidateResult]