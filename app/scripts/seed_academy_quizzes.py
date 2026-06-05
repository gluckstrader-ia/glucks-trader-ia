from app.database import SessionLocal
from app.models.academy import AcademyLesson, AcademyQuiz


def seed_academy_quizzes():
    db = SessionLocal()

    try:
        lessons = db.query(AcademyLesson).all()

        if not lessons:
            print("Nenhuma aula encontrada. Rode primeiro o seed_academy.py.")
            return

        existing_quiz = db.query(AcademyQuiz).first()

        if existing_quiz:
            print("Quizzes já cadastrados.")
            return

        for lesson in lessons:
            quiz = AcademyQuiz(
                lesson_id=lesson.id,
                question=f"Qual é o principal objetivo da aula: {lesson.title}?",
                options_json=[
                    "Decorar conceitos sem prática",
                    "Entender e aplicar o conteúdo na jornada trader",
                    "Operar sem gestão de risco",
                    "Ignorar o simulador",
                ],
                correct_answer="Entender e aplicar o conteúdo na jornada trader",
                explanation="O objetivo da Academy é transformar conhecimento em prática através do Método GTA, missões, simulador e Alan IA.",
                reward_xp=30,
                difficulty="basic",
            )

            db.add(quiz)

        db.commit()

        print("Quizzes iniciais criados com sucesso.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_academy_quizzes()