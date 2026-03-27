from app.auth import hash_password
from app.database import SessionLocal
from app.models import User

db = SessionLocal()

email = "admin@glucks.com"

existing = db.query(User).filter(User.email == email).first()

if existing:
    existing.name = "Administrador"
    existing.password_hash = hash_password("123456")
    existing.is_active = True
    existing.is_blocked = False
    existing.is_admin = True
    existing.plan = "pro"
    db.commit()
    print("Admin atualizado com sucesso")
else:
    user = User(
        name="Administrador",
        email=email,
        password_hash=hash_password("123456"),
        is_active=True,
        is_blocked=False,
        is_admin=True,
        plan="pro",
    )
    db.add(user)
    db.commit()
    print("Admin criado com sucesso")

db.close()