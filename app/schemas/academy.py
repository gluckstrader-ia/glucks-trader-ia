from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel


class AcademyCourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    price: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AcademyModuleResponse(BaseModel):
    id: int
    course_id: int
    level: int
    title: str
    description: Optional[str] = None
    order_index: int
    required_xp: int
    reward_xp: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AcademyLessonResponse(BaseModel):
    id: int
    module_id: int
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: int
    order_index: int
    reward_xp: int
    has_quiz: bool
    has_mission: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AcademyUserProgressResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    total_xp: int
    current_level: int
    current_module_id: Optional[int] = None
    current_lesson_id: Optional[int] = None
    streak_days: int
    last_access_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AcademyLessonProgressResponse(BaseModel):
    id: int
    user_id: int
    lesson_id: int
    status: str
    watch_percentage: float
    completed_at: Optional[datetime] = None
    xp_earned: int
    created_at: datetime

    class Config:
        from_attributes = True


class AcademyXPLogResponse(BaseModel):
    id: int
    user_id: int
    source_type: str
    source_id: Optional[int] = None
    xp_amount: int
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AcademyQuizResponse(BaseModel):
    id: int
    lesson_id: int
    question: str
    options_json: Any
    explanation: Optional[str] = None
    reward_xp: int
    difficulty: str
    created_at: datetime

    class Config:
        from_attributes = True


class AcademyQuizAnswerRequest(BaseModel):
    selected_answer: str


class AcademyQuizAnswerResponse(BaseModel):
    quiz_id: int
    selected_answer: str
    is_correct: bool
    xp_earned: int
    explanation: Optional[str] = None


class AcademyMissionResponse(BaseModel):
    id: int
    module_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    mission_type: str
    required_action: Optional[str] = None
    reward_xp: int
    difficulty: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AcademyAchievementResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    reward_xp: int
    is_secret: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AcademyCertificateResponse(BaseModel):
    id: int
    user_id: int
    certificate_type: str
    certificate_code: str
    qr_code_url: Optional[str] = None
    pdf_url: Optional[str] = None
    score: float
    issued_at: datetime

    class Config:
        from_attributes = True


class AcademyHomeNextLesson(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    module_title: Optional[str] = None


class AcademyHomeMission(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    reward_xp: Optional[int] = None


class AcademyHomeResponse(BaseModel):
    total_xp: int
    current_level: int
    level_name: str
    streak_days: int
    completion_percent: float
    next_lesson: Optional[AcademyHomeNextLesson] = None
    active_mission: Optional[AcademyHomeMission] = None
    recent_badges: List[AcademyAchievementResponse] = []


class AcademyJourneyModule(BaseModel):
    id: int
    level: int
    title: str
    description: Optional[str] = None
    order_index: int
    required_xp: int
    reward_xp: int
    unlocked: bool
    completed: bool
    lessons_count: int


class AcademyJourneyResponse(BaseModel):
    total_xp: int
    current_level: int
    level_name: str
    modules: List[AcademyJourneyModule]

class AcademyMissionCompleteResponse(BaseModel):
    message: str
    mission_id: int
    xp_earned: int
    total_xp: int
    current_level: int
    level_name: str