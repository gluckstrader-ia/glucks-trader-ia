from app.database import SessionLocal
from app.models.academy import AcademyMission, AcademyModule


def seed_academy_missions():
    db = SessionLocal()

    try:
        existing = db.query(AcademyMission).first()

        if existing:
            print("Missões já cadastradas.")
            return

        modules = db.query(AcademyModule).order_by(AcademyModule.order_index.asc()).all()

        if not modules:
            print("Nenhum módulo encontrado. Rode primeiro o seed_academy.py.")
            return

        missions_by_module = {
            0: [
                {
                    "title": "Conheça a Academy",
                    "description": "Assista às primeiras aulas e entenda como funciona a jornada GTA.",
                    "mission_type": "study",
                    "required_action": "complete_intro_lessons",
                    "reward_xp": 50,
                    "difficulty": "basic",
                },
                {
                    "title": "Primeira conversa com Alan IA",
                    "description": "Abra o Alan IA e faça sua primeira pergunta sobre a Academy.",
                    "mission_type": "alan_ai",
                    "required_action": "first_ai_interaction",
                    "reward_xp": 80,
                    "difficulty": "basic",
                },
            ],
            1: [
                {
                    "title": "Configurar ambiente de estudos",
                    "description": "Escolha sua plataforma principal e prepare sua conta demo.",
                    "mission_type": "platform_setup",
                    "required_action": "setup_platform",
                    "reward_xp": 100,
                    "difficulty": "basic",
                },
                {
                    "title": "Primeira operação simulada",
                    "description": "Faça sua primeira operação simulada com entrada, stop e alvo.",
                    "mission_type": "simulator",
                    "required_action": "first_simulated_trade",
                    "reward_xp": 150,
                    "difficulty": "basic",
                },
            ],
            2: [
                {
                    "title": "Marcar suportes e resistências",
                    "description": "Marque 5 suportes e 5 resistências em gráficos diferentes.",
                    "mission_type": "analysis",
                    "required_action": "mark_support_resistance",
                    "reward_xp": 150,
                    "difficulty": "intermediate",
                },
                {
                    "title": "Identificar pullbacks",
                    "description": "Encontre 5 pullbacks válidos e envie para correção.",
                    "mission_type": "analysis",
                    "required_action": "identify_pullbacks",
                    "reward_xp": 200,
                    "difficulty": "intermediate",
                },
            ],
            3: [
                {
                    "title": "Confluência técnica",
                    "description": "Encontre 3 pontos onde VWAP, tendência e volume estejam alinhados.",
                    "mission_type": "technical",
                    "required_action": "technical_confluence",
                    "reward_xp": 200,
                    "difficulty": "intermediate",
                }
            ],
            4: [
                {
                    "title": "Traçar Fibonacci",
                    "description": "Trace Fibonacci em 10 movimentos e identifique retrações importantes.",
                    "mission_type": "fibonacci",
                    "required_action": "draw_fibonacci",
                    "reward_xp": 300,
                    "difficulty": "advanced",
                }
            ],
            5: [
                {
                    "title": "Contagem Elliott",
                    "description": "Identifique 5 estruturas impulsivas e 5 estruturas corretivas.",
                    "mission_type": "elliott",
                    "required_action": "elliott_wave_count",
                    "reward_xp": 350,
                    "difficulty": "advanced",
                }
            ],
            6: [
                {
                    "title": "Plano operacional",
                    "description": "Crie seu primeiro plano operacional completo.",
                    "mission_type": "strategy",
                    "required_action": "create_trading_plan",
                    "reward_xp": 300,
                    "difficulty": "advanced",
                }
            ],
            7: [
                {
                    "title": "Desafio Elite GTA IA",
                    "description": "Execute uma análise completa com estrutura, Fibonacci, Elliott, gestão e IA.",
                    "mission_type": "elite",
                    "required_action": "elite_gta_challenge",
                    "reward_xp": 500,
                    "difficulty": "elite",
                }
            ],
        }

        for module in modules:
            mission_templates = missions_by_module.get(module.level, [])

            for mission_data in mission_templates:
                mission = AcademyMission(
                    module_id=module.id,
                    title=mission_data["title"],
                    description=mission_data["description"],
                    mission_type=mission_data["mission_type"],
                    required_action=mission_data["required_action"],
                    reward_xp=mission_data["reward_xp"],
                    difficulty=mission_data["difficulty"],
                    is_active=True,
                )

                db.add(mission)

        db.commit()

        print("Missões iniciais criadas com sucesso.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_academy_missions()