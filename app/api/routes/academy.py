from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.academy import (
    AcademyAchievement,
    AcademyCourse,
    AcademyLesson,
    AcademyLessonProgress,
    AcademyMission,
    AcademyModule,
    AcademyQuiz,
    AcademyQuizResult,
    AcademyUserProgress,
    AcademyXPLog,
    AcademyUserMission,
)

from app.schemas.academy import (
    AcademyHomeMission,
    AcademyHomeNextLesson,
    AcademyHomeResponse,
    AcademyJourneyModule,
    AcademyJourneyResponse,
    AcademyLessonResponse,
    AcademyModuleResponse,
    AcademyQuizAnswerRequest,
    AcademyQuizAnswerResponse,
    AcademyQuizResponse,
    AcademyMissionCompleteResponse,
)

from app.schemas.academy import AcademyMissionResponse

router = APIRouter(prefix="/academy", tags=["Academy"])


# =====================================================
# HELPERS
# =====================================================

def get_level_name(total_xp: int) -> str:
    if total_xp >= 20000:
        return "Elite GTA IA"
    if total_xp >= 10000:
        return "Trader Profissional"
    if total_xp >= 6000:
        return "Analista Elliott"
    if total_xp >= 3000:
        return "Especialista Fibonacci"
    if total_xp >= 1500:
        return "Estrategista"
    if total_xp >= 500:
        return "Operador Técnico"
    if total_xp >= 100:
        return "Aprendiz de Mercado"
    return "Recruta"


def get_level_number(total_xp: int) -> int:
    if total_xp >= 20000:
        return 7
    if total_xp >= 10000:
        return 6
    if total_xp >= 6000:
        return 5
    if total_xp >= 3000:
        return 4
    if total_xp >= 1500:
        return 3
    if total_xp >= 500:
        return 2
    if total_xp >= 100:
        return 1
    return 0


def get_or_create_progress(db: Session, user_id: int, course_id: int) -> AcademyUserProgress:
    progress = (
        db.query(AcademyUserProgress)
        .filter(
            AcademyUserProgress.user_id == user_id,
            AcademyUserProgress.course_id == course_id,
        )
        .first()
    )

    if progress:
        return progress

    progress = AcademyUserProgress(
        user_id=user_id,
        course_id=course_id,
        total_xp=0,
        current_level=0,
        streak_days=0,
        last_access_at=datetime.utcnow(),
    )

    db.add(progress)
    db.commit()
    db.refresh(progress)

    return progress


def add_xp(
    db: Session,
    user_id: int,
    progress: AcademyUserProgress,
    amount: int,
    source_type: str,
    source_id: int | None = None,
    description: str | None = None,
) -> AcademyUserProgress:
    progress.total_xp += amount
    progress.current_level = get_level_number(progress.total_xp)
    progress.last_access_at = datetime.utcnow()

    xp_log = AcademyXPLog(
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        xp_amount=amount,
        description=description,
    )

    db.add(xp_log)
    db.commit()
    db.refresh(progress)

    return progress


# =====================================================
# TEMP AUTH HELPER
# =====================================================
# IMPORTANTE:
# Depois vamos trocar isso pelo usuário autenticado via JWT.
# Por enquanto usamos user_id=1 para testar rápido no Swagger.
# =====================================================

def get_current_user_id() -> int:
    return 1


# =====================================================
# ROUTES
# =====================================================

@router.get("/home", response_model=AcademyHomeResponse)
def get_academy_home(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    course = db.query(AcademyCourse).filter(AcademyCourse.is_active == True).first()

    if not course:
        raise HTTPException(status_code=404, detail="Nenhum curso Academy ativo encontrado.")

    progress = get_or_create_progress(db, user_id=user_id, course_id=course.id)

    next_lesson = (
        db.query(AcademyLesson)
        .join(AcademyModule, AcademyLesson.module_id == AcademyModule.id)
        .filter(AcademyLesson.is_active == True)
        .order_by(AcademyModule.order_index.asc(), AcademyLesson.order_index.asc())
        .first()
    )

    active_mission = (
        db.query(AcademyMission)
        .filter(AcademyMission.is_active == True)
        .order_by(AcademyMission.id.asc())
        .first()
    )

    total_lessons = db.query(AcademyLesson).filter(AcademyLesson.is_active == True).count()

    completed_lessons = (
        db.query(AcademyLessonProgress)
        .filter(
            AcademyLessonProgress.user_id == user_id,
            AcademyLessonProgress.status == "completed",
        )
        .count()
    )

    completion_percent = 0
    if total_lessons > 0:
        completion_percent = round((completed_lessons / total_lessons) * 100, 2)

    return AcademyHomeResponse(
        total_xp=progress.total_xp,
        current_level=progress.current_level,
        level_name=get_level_name(progress.total_xp),
        streak_days=progress.streak_days,
        completion_percent=completion_percent,
        next_lesson=AcademyHomeNextLesson(
            id=next_lesson.id if next_lesson else None,
            title=next_lesson.title if next_lesson else None,
            module_title=next_lesson.module.title if next_lesson and next_lesson.module else None,
        ),
        active_mission=AcademyHomeMission(
            id=active_mission.id if active_mission else None,
            title=active_mission.title if active_mission else None,
            reward_xp=active_mission.reward_xp if active_mission else None,
        ),
        recent_badges=[],
    )


@router.get("/journey", response_model=AcademyJourneyResponse)
def get_academy_journey(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    course = db.query(AcademyCourse).filter(AcademyCourse.is_active == True).first()

    if not course:
        raise HTTPException(status_code=404, detail="Nenhum curso Academy ativo encontrado.")

    progress = get_or_create_progress(db, user_id=user_id, course_id=course.id)

    modules = (
        db.query(AcademyModule)
        .filter(AcademyModule.course_id == course.id, AcademyModule.is_active == True)
        .order_by(AcademyModule.order_index.asc())
        .all()
    )

    response_modules = []

    for module in modules:
        lessons_count = (
            db.query(AcademyLesson)
            .filter(
                AcademyLesson.module_id == module.id,
                AcademyLesson.is_active == True,
            )
            .count()
        )

        completed_lessons = (
            db.query(AcademyLessonProgress)
            .join(AcademyLesson, AcademyLessonProgress.lesson_id == AcademyLesson.id)
            .filter(
                AcademyLessonProgress.user_id == user_id,
                AcademyLessonProgress.status == "completed",
                AcademyLesson.module_id == module.id,
            )
            .count()
        )

        response_modules.append(
            AcademyJourneyModule(
                id=module.id,
                level=module.level,
                title=module.title,
                description=module.description,
                order_index=module.order_index,
                required_xp=module.required_xp,
                reward_xp=module.reward_xp,
                unlocked=progress.total_xp >= module.required_xp,
                completed=lessons_count > 0 and completed_lessons >= lessons_count,
                lessons_count=lessons_count,
            )
        )

    return AcademyJourneyResponse(
        total_xp=progress.total_xp,
        current_level=progress.current_level,
        level_name=get_level_name(progress.total_xp),
        modules=response_modules,
    )


@router.get("/modules", response_model=List[AcademyModuleResponse])
def list_academy_modules(db: Session = Depends(get_db)):
    course = db.query(AcademyCourse).filter(AcademyCourse.is_active == True).first()

    if not course:
        raise HTTPException(status_code=404, detail="Nenhum curso Academy ativo encontrado.")

    return (
        db.query(AcademyModule)
        .filter(AcademyModule.course_id == course.id, AcademyModule.is_active == True)
        .order_by(AcademyModule.order_index.asc())
        .all()
    )


@router.get("/lessons/{lesson_id}", response_model=AcademyLessonResponse)
def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
):
    lesson = (
        db.query(AcademyLesson)
        .filter(AcademyLesson.id == lesson_id, AcademyLesson.is_active == True)
        .first()
    )

    if not lesson:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")

    return lesson


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    lesson = (
        db.query(AcademyLesson)
        .filter(AcademyLesson.id == lesson_id, AcademyLesson.is_active == True)
        .first()
    )

    if not lesson:
        raise HTTPException(status_code=404, detail="Aula não encontrada.")

    course = db.query(AcademyCourse).filter(AcademyCourse.is_active == True).first()

    if not course:
        raise HTTPException(status_code=404, detail="Nenhum curso Academy ativo encontrado.")

    progress = get_or_create_progress(db, user_id=user_id, course_id=course.id)

    lesson_progress = (
        db.query(AcademyLessonProgress)
        .filter(
            AcademyLessonProgress.user_id == user_id,
            AcademyLessonProgress.lesson_id == lesson.id,
        )
        .first()
    )

    if lesson_progress and lesson_progress.status == "completed":
        return {
            "message": "Aula já estava concluída.",
            "xp_earned": 0,
            "total_xp": progress.total_xp,
            "current_level": progress.current_level,
            "level_name": get_level_name(progress.total_xp),
        }

    if not lesson_progress:
        lesson_progress = AcademyLessonProgress(
            user_id=user_id,
            lesson_id=lesson.id,
            status="completed",
            watch_percentage=100,
            completed_at=datetime.utcnow(),
            xp_earned=lesson.reward_xp,
        )
        db.add(lesson_progress)
    else:
        lesson_progress.status = "completed"
        lesson_progress.watch_percentage = 100
        lesson_progress.completed_at = datetime.utcnow()
        lesson_progress.xp_earned = lesson.reward_xp

    progress.current_lesson_id = lesson.id
    progress.current_module_id = lesson.module_id

    add_xp(
        db=db,
        user_id=user_id,
        progress=progress,
        amount=lesson.reward_xp,
        source_type="lesson",
        source_id=lesson.id,
        description=f"Aula concluída: {lesson.title}",
    )

    return {
        "message": "Aula concluída com sucesso.",
        "xp_earned": lesson.reward_xp,
        "total_xp": progress.total_xp,
        "current_level": progress.current_level,
        "level_name": get_level_name(progress.total_xp),
    }


@router.get("/quizzes/lesson/{lesson_id}", response_model=List[AcademyQuizResponse])
def get_lesson_quizzes(
    lesson_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(AcademyQuiz)
        .filter(AcademyQuiz.lesson_id == lesson_id)
        .order_by(AcademyQuiz.id.asc())
        .all()
    )


@router.post("/quizzes/{quiz_id}/answer", response_model=AcademyQuizAnswerResponse)
def answer_quiz(
    quiz_id: int,
    payload: AcademyQuizAnswerRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    quiz = db.query(AcademyQuiz).filter(AcademyQuiz.id == quiz_id).first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz não encontrado.")

    is_correct = payload.selected_answer == quiz.correct_answer
    xp_earned = quiz.reward_xp if is_correct else 0

    result = AcademyQuizResult(
        user_id=user_id,
        quiz_id=quiz.id,
        selected_answer=payload.selected_answer,
        is_correct=is_correct,
        xp_earned=xp_earned,
    )

    db.add(result)

    course = db.query(AcademyCourse).filter(AcademyCourse.is_active == True).first()

    if not course:
        raise HTTPException(status_code=404, detail="Nenhum curso Academy ativo encontrado.")

    progress = get_or_create_progress(db, user_id=user_id, course_id=course.id)

    if xp_earned > 0:
        add_xp(
            db=db,
            user_id=user_id,
            progress=progress,
            amount=xp_earned,
            source_type="quiz",
            source_id=quiz.id,
            description=f"Quiz respondido corretamente: {quiz.question[:60]}",
        )
    else:
        db.commit()

    return AcademyQuizAnswerResponse(
        quiz_id=quiz.id,
        selected_answer=payload.selected_answer,
        is_correct=is_correct,
        xp_earned=xp_earned,
        explanation=quiz.explanation,
    )

@router.get("/missions", response_model=list[AcademyMissionResponse])
def list_academy_missions(
    db: Session = Depends(get_db),
):
    return (
        db.query(AcademyMission)
        .filter(AcademyMission.is_active == True)
        .order_by(AcademyMission.id.asc())
        .all()
    )

@router.post(
    "/missions/{mission_id}/complete",
    response_model=AcademyMissionCompleteResponse,
)
def complete_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    mission = (
        db.query(AcademyMission)
        .filter(
            AcademyMission.id == mission_id,
            AcademyMission.is_active == True,
        )
        .first()
    )

    if not mission:
        raise HTTPException(status_code=404, detail="Missão não encontrada.")

    existing = (
        db.query(AcademyUserMission)
        .filter(
            AcademyUserMission.user_id == user_id,
            AcademyUserMission.mission_id == mission.id,
            AcademyUserMission.status == "completed",
        )
        .first()
    )

    course = db.query(AcademyCourse).filter(
        AcademyCourse.is_active == True
    ).first()

    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado.")

    progress = get_or_create_progress(
        db=db,
        user_id=user_id,
        course_id=course.id,
    )

    if existing:
        return AcademyMissionCompleteResponse(
            message="Missão já concluída.",
            mission_id=mission.id,
            xp_earned=0,
            total_xp=progress.total_xp,
            current_level=progress.current_level,
            level_name=get_level_name(progress.total_xp),
        )

    user_mission = AcademyUserMission(
        user_id=user_id,
        mission_id=mission.id,
        status="completed",
        progress=100,
        completed_at=datetime.utcnow(),
        xp_earned=mission.reward_xp,
        ai_feedback="Excelente trabalho. Continue evoluindo na jornada GTA.",
    )

    db.add(user_mission)

    add_xp(
        db=db,
        user_id=user_id,
        progress=progress,
        amount=mission.reward_xp,
        source_type="mission",
        source_id=mission.id,
        description=f"Missão concluída: {mission.title}",
    )

    return AcademyMissionCompleteResponse(
        message="Missão concluída com sucesso.",
        mission_id=mission.id,
        xp_earned=mission.reward_xp,
        total_xp=progress.total_xp,
        current_level=progress.current_level,
        level_name=get_level_name(progress.total_xp),
    )