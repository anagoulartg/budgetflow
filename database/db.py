from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "database"
DB_PATH = DATA_DIR / "budgetflow.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
Base = declarative_base()


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    from database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    migrate_db()
    seed_usuarios()


def get_session():
    return SessionLocal()


def seed_usuarios() -> None:
    from database.models import Usuario

    usuarios = [
        ("gestor.demo", "123456", "Gestor", None),
        ("controladoria.demo", "123456", "Controladoria", None),
        ("diretoria.demo", "123456", "Diretoria", "Comercial"),
        ("diretoria.adm", "123456", "Diretoria", "Administrativo"),
        ("diretoria.industrial", "123456", "Diretoria", "Industrial"),
        ("conselho.demo", "123456", "Conselho", None),
        ("admin.demo", "123456", "Admin", None),
    ]
    with get_session() as session:
        existentes = {u.nome for u in session.query(Usuario).all()}
        for nome, senha, perfil, area in usuarios:
            if nome not in existentes:
                session.add(Usuario(nome=nome, senha=senha, perfil=perfil, area_responsavel=area))
            else:
                usuario = session.query(Usuario).filter(Usuario.nome == nome).one()
                usuario.area_responsavel = area
        session.commit()


def migrate_db() -> None:
    inspector = inspect(engine)
    if "usuarios" in inspector.get_table_names():
        colunas = {coluna["name"] for coluna in inspector.get_columns("usuarios")}
        with engine.begin() as conn:
            if "senha" not in colunas:
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN senha VARCHAR(120) NOT NULL DEFAULT '123456'"))
            if "area_responsavel" not in colunas:
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN area_responsavel VARCHAR(120)"))
