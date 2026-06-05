from app.database import SessionLocal
from app.models.academy import AcademyCourse, AcademyModule, AcademyLesson


def seed_academy():
    db = SessionLocal()

    try:
        existing = db.query(AcademyCourse).filter(
            AcademyCourse.title == "Gluck's Trader Academy IA"
        ).first()

        if existing:
            print("Academy já cadastrada.")
            return

        course = AcademyCourse(
            title="Gluck's Trader Academy IA",
            description="Formação trader gamificada com IA, simulador, Método GTA, Fibonacci e Elliott.",
            price=997.0,
            is_active=True,
        )

        db.add(course)
        db.commit()
        db.refresh(course)

        modules = [
            {
                "level": 0,
                "title": "Despertar do Trader",
                "description": "Boas-vindas, avatar, XP, Alan IA e primeira missão.",
                "order_index": 0,
                "required_xp": 0,
                "reward_xp": 300,
                "lessons": [
                    "Bem-vindo à Academy",
                    "Como funciona a plataforma",
                    "Criando seu avatar",
                    "XP, missões e certificação",
                    "Primeira conversa com Alan IA",
                ],
            },
            {
                "level": 1,
                "title": "Primeiros Passos do Trader",
                "description": "Corretoras, plataformas, contratos, lotes, replay e automações.",
                "order_index": 1,
                "required_xp": 100,
                "reward_xp": 700,
                "lessons": [
                    "O que é Bolsa de Valores",
                    "Como escolher uma corretora",
                    "Conta demo e conta real",
                    "Contratos e lotes",
                    "Instalando o Profit",
                    "Usando o replay no Profit",
                    "Instalando o MetaTrader 5",
                    "Usando o testador no MT5",
                    "Instalando o NinjaTrader",
                    "Automações nas plataformas",
                ],
            },
            {
                "level": 2,
                "title": "Aprendiz de Mercado",
                "description": "Candles, estrutura, tendências, suportes, resistências, pullbacks, pivôs e GAP.",
                "order_index": 2,
                "required_xp": 500,
                "reward_xp": 1200,
                "lessons": [
                    "O que é um candle",
                    "Psicologia dos candles",
                    "Tendência de alta e baixa",
                    "Topos e fundos",
                    "Suporte e resistência",
                    "Pullbacks",
                    "Pivôs",
                    "GAP",
                ],
            },
            {
                "level": 3,
                "title": "Operador Técnico",
                "description": "VWAP, médias, IFR, MACD, estocástico, volume e confluências.",
                "order_index": 3,
                "required_xp": 1500,
                "reward_xp": 1500,
                "lessons": [
                    "VWAP",
                    "Médias móveis",
                    "IFR",
                    "MACD",
                    "Estocástico",
                    "Volume",
                    "Confluências técnicas",
                ],
            },
            {
                "level": 4,
                "title": "Especialista Fibonacci",
                "description": "Retrações, projeções, expansões, alvos e Método GTA Fibonacci.",
                "order_index": 4,
                "required_xp": 3000,
                "reward_xp": 2500,
                "lessons": [
                    "Origem de Fibonacci",
                    "Sequência e proporção áurea",
                    "Retrações",
                    "Projeções",
                    "Expansões",
                    "Fibonacci no Day Trade",
                    "Fibonacci no Swing Trade",
                    "Método GTA Fibonacci",
                ],
            },
            {
                "level": 5,
                "title": "Analista Elliott",
                "description": "Ondas impulsivas, corretivas, fractais, ciclos e Método GTA Elliott.",
                "order_index": 5,
                "required_xp": 6000,
                "reward_xp": 3000,
                "lessons": [
                    "Fundamentos das Ondas de Elliott",
                    "Estrutura impulsiva",
                    "Estrutura corretiva",
                    "Zig Zag",
                    "Flat",
                    "Triângulos",
                    "Fractais",
                    "Elliott + Fibonacci",
                    "Método GTA Elliott",
                ],
            },
            {
                "level": 6,
                "title": "Trader Profissional GTA",
                "description": "Gestão, execução, contexto, diário operacional e consistência.",
                "order_index": 6,
                "required_xp": 10000,
                "reward_xp": 3500,
                "lessons": [
                    "Gestão de risco",
                    "Risco-retorno",
                    "Estatística operacional",
                    "Diário operacional",
                    "Controle emocional",
                    "Plano operacional",
                ],
            },
            {
                "level": 7,
                "title": "Elite GTA IA",
                "description": "Dashboard IA, Alan IA, simulador avançado, robôs, automações e certificação final.",
                "order_index": 7,
                "required_xp": 20000,
                "reward_xp": 5000,
                "lessons": [
                    "Operação com IA",
                    "Dashboard Gluck's Trader IA",
                    "Simulador avançado",
                    "Indicadores",
                    "Robôs e automações",
                    "Certificação profissional GTA",
                ],
            },
        ]

        for module_data in modules:
            lessons = module_data.pop("lessons")

            module = AcademyModule(
                course_id=course.id,
                **module_data,
                is_active=True,
            )

            db.add(module)
            db.commit()
            db.refresh(module)

            for index, lesson_title in enumerate(lessons):
                lesson = AcademyLesson(
                    module_id=module.id,
                    title=lesson_title,
                    description=f"Aula do módulo {module.title}: {lesson_title}",
                    duration_minutes=10,
                    order_index=index,
                    reward_xp=20,
                    has_quiz=True,
                    has_mission=True,
                    is_active=True,
                )
                db.add(lesson)

            db.commit()

        print("Seed da Academy criado com sucesso.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_academy()