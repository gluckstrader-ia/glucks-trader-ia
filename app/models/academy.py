from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Float,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


class AcademyCourse(Base):
    __tablename__ = "academy_courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, default=997.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    modules = relationship("AcademyModule", back_populates="course")


class AcademyModule(Base):
    __tablename__ = "academy_modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("academy_courses.id"), nullable=False)

    level = Column(Integer, default=0)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)

    required_xp = Column(Integer, default=0)
    reward_xp = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("AcademyCourse", back_populates="modules")
    lessons = relationship("AcademyLesson", back_populates="module")


class AcademyLesson(Base):
    __tablename__ = "academy_lessons"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("academy_modules.id"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=True)
    duration_minutes = Column(Integer, default=0)
    order_index = Column(Integer, default=0)

    reward_xp = Column(Integer, default=20)
    has_quiz = Column(Boolean, default=False)
    has_mission = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    module = relationship("AcademyModule", back_populates="lessons")


class AcademyUserProgress(Base):
    __tablename__ = "academy_user_progress"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("academy_courses.id"), nullable=False)

    total_xp = Column(Integer, default=0)
    current_level = Column(Integer, default=0)
    current_module_id = Column(Integer, ForeignKey("academy_modules.id"), nullable=True)
    current_lesson_id = Column(Integer, ForeignKey("academy_lessons.id"), nullable=True)

    streak_days = Column(Integer, default=0)
    last_access_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AcademyLessonProgress(Base):
    __tablename__ = "academy_lesson_progress"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("academy_lessons.id"), nullable=False)

    status = Column(String(50), default="not_started")
    watch_percentage = Column(Float, default=0.0)
    completed_at = Column(DateTime, nullable=True)
    xp_earned = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)


class AcademyXPLog(Base):
    __tablename__ = "academy_xp_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    source_type = Column(String(100), nullable=False)
    source_id = Column(Integer, nullable=True)

    xp_amount = Column(Integer, default=0)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class AcademyQuiz(Base):
    __tablename__ = "academy_quizzes"

    id = Column(Integer, primary_key=True, index=True)

    lesson_id = Column(Integer, ForeignKey("academy_lessons.id"), nullable=False)

    question = Column(Text, nullable=False)
    options_json = Column(JSON, nullable=False)
    correct_answer = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=True)

    reward_xp = Column(Integer, default=30)
    difficulty = Column(String(50), default="basic")

    created_at = Column(DateTime, default=datetime.utcnow)


class AcademyQuizResult(Base):
    __tablename__ = "academy_quiz_results"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    quiz_id = Column(Integer, ForeignKey("academy_quizzes.id"), nullable=False)

    selected_answer = Column(String(255), nullable=False)
    is_correct = Column(Boolean, default=False)
    xp_earned = Column(Integer, default=0)

    answered_at = Column(DateTime, default=datetime.utcnow)


class AcademyMission(Base):
    __tablename__ = "academy_missions"

    id = Column(Integer, primary_key=True, index=True)

    module_id = Column(Integer, ForeignKey("academy_modules.id"), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    mission_type = Column(String(100), default="study")
    required_action = Column(String(255), nullable=True)
    reward_xp = Column(Integer, default=50)
    difficulty = Column(String(50), default="basic")

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AcademyUserMission(Base):
    __tablename__ = "academy_user_missions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey("academy_missions.id"), nullable=False)

    status = Column(String(50), default="not_started")
    progress = Column(Float, default=0.0)
    completed_at = Column(DateTime, nullable=True)
    xp_earned = Column(Integer, default=0)
    ai_feedback = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class AcademyAchievement(Base):
    __tablename__ = "academy_achievements"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    icon = Column(String(255), nullable=True)

    condition_key = Column(String(255), nullable=True)
    reward_xp = Column(Integer, default=0)
    is_secret = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class AcademyUserAchievement(Base):
    __tablename__ = "academy_user_achievements"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("academy_achievements.id"), nullable=False)

    unlocked_at = Column(DateTime, default=datetime.utcnow)


class AcademySimulatorSession(Base):
    __tablename__ = "academy_simulator_sessions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    mode = Column(String(100), default="replay")
    asset = Column(String(50), nullable=True)
    timeframe = Column(String(50), nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    score = Column(Float, default=0.0)
    xp_earned = Column(Integer, default=0)


class AcademySimulatorTrade(Base):
    __tablename__ = "academy_simulator_trades"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(Integer, ForeignKey("academy_simulator_sessions.id"), nullable=False)

    side = Column(String(20), nullable=False)

    entry_price = Column(Float, nullable=False)
    stop_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)

    result_points = Column(Float, default=0.0)
    rr_ratio = Column(Float, default=0.0)

    structure_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    discipline_score = Column(Float, default=0.0)
    execution_score = Column(Float, default=0.0)
    context_score = Column(Float, default=0.0)
    final_gta_score = Column(Float, default=0.0)

    ai_feedback = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class AcademyAIInteraction(Base):
    __tablename__ = "academy_ai_interactions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    interaction_type = Column(String(100), default="chat")
    context_type = Column(String(100), nullable=True)
    context_id = Column(Integer, nullable=True)

    message = Column(Text, nullable=False)
    response = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class AcademyCertificate(Base):
    __tablename__ = "academy_certificates"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    certificate_type = Column(String(100), nullable=False)
    certificate_code = Column(String(255), unique=True, index=True, nullable=False)

    qr_code_url = Column(String(500), nullable=True)
    pdf_url = Column(String(500), nullable=True)

    score = Column(Float, default=0.0)
    issued_at = Column(DateTime, default=datetime.utcnow)