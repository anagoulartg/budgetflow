from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


class Orcamento(Base):
    __tablename__ = "orcamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    gestor: Mapped[str] = mapped_column(String(120), nullable=False)
    area: Mapped[str] = mapped_column(String(120), nullable=False)
    centro_custo: Mapped[str] = mapped_column(String(80), nullable=False)
    conta_contabil: Mapped[str] = mapped_column(String(80), nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    mes: Mapped[str] = mapped_column(String(2), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    valor_solicitado: Mapped[float] = mapped_column(Float, nullable=False)
    valor_aprovado: Mapped[float | None] = mapped_column(Float, nullable=True)
    valor_final: Mapped[float | None] = mapped_column(Float, nullable=True)
    justificativa: Mapped[str] = mapped_column(Text, nullable=False)
    prioridade: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="Pendente")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    historicos = relationship("HistoricoAprovacao", back_populates="orcamento", cascade="all, delete-orphan")


class HistoricoAprovacao(Base):
    __tablename__ = "historico_aprovacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    orcamento_id: Mapped[int] = mapped_column(ForeignKey("orcamentos.id"), nullable=False)
    usuario_decisor: Mapped[str] = mapped_column(String(120), nullable=False)
    perfil_decisor: Mapped[str] = mapped_column(String(40), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status_anterior: Mapped[str] = mapped_column(String(40), nullable=False)
    novo_status: Mapped[str] = mapped_column(String(40), nullable=False)
    valor_anterior: Mapped[float | None] = mapped_column(Float, nullable=True)
    novo_valor: Mapped[float | None] = mapped_column(Float, nullable=True)
    comentario: Mapped[str] = mapped_column(Text, nullable=False)

    orcamento = relationship("Orcamento", back_populates="historicos")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    senha: Mapped[str] = mapped_column(String(120), nullable=False, default="123456")
    perfil: Mapped[str] = mapped_column(String(40), nullable=False)
    area_responsavel: Mapped[str | None] = mapped_column(String(120), nullable=True)


class MetaOrcamentaria(Base):
    __tablename__ = "metas_orcamentarias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    area: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    valor_meta: Mapped[float] = mapped_column(Float, nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
