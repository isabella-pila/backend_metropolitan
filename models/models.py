from datetime import datetime
from sqlalchemy import (Column, Integer, String, DateTime, Float, ForeignKey, 
                        Boolean, Date, Numeric, UniqueConstraint, func, JSON) 

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=False)
    cpf = Column(String(14), nullable=False, unique=True, index=True)
    
    password_hash = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
     # --- CAMPOS NOVOS ---
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True, index=True)
    verification_expires_at = Column(DateTime, nullable=True)
    # --- FIM DOS CAMPOS NOVOS ---
    # Relacionamentos
    perfil = relationship("PerfilUsuario", back_populates="user", uselist=False, cascade="all, delete-orphan")
    simulacoes = relationship("Simulacao", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("cpf", name="uq_users_cpf"),
    )


class PerfilUsuario(Base):
    __tablename__ = "perfis_usuarios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Dados pessoais
    data_nascimento = Column(Date, nullable=True)
    genero = Column(String(20), nullable=True)
    escolaridade = Column(String(100), nullable=True)
    estado_civil = Column(String(50), nullable=True)
    nome_mae = Column(String(150), nullable=True)


    # Endereço
    cep = Column(String(10), nullable=True)
    logradouro = Column(String(150), nullable=True)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)

    # Dados financeiros
    possui_veiculo = Column(Boolean, default=False)
    possui_imovel = Column(Boolean, default=False)
    profissao = Column(String(100), nullable=True)
    data_admissao = Column(Date, nullable=True)
    renda_mensal = Column(Numeric(10, 2), nullable=True)

    # Relacionamento
    user = relationship("User", back_populates="perfil")


class Simulacao(Base):
    __tablename__ = "simulacoes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 1. DADOS GERAIS DA SIMULAÇÃO
    # (Renomeei seus campos para bater com o schema que definimos antes)
    valor_desejado = Column(Numeric(12, 2), nullable=False)  # (Seu 'valor')
    prazo_meses = Column(Integer, nullable=False)            # (Seu 'parcelas')
    motivo_emprestimo = Column(String(150), nullable=False) # (Seu 'finalidade')
    tipo_emprestimo = Column(String(50), nullable=False)   # (Este já estava certo)

    # 2. O CAMPO FLEXÍVEL (A MUDANÇA CRÍTICA)
    # Aqui é onde os 14 tipos de formulários serão salvos.
    # Use JSONB no Postgres, ou JSON no SQLite/MySQL.
    dados_especificos = Column(JSON, nullable=True)

    # 3. DADOS DE CÁLCULO (Calculados pelo backend)
    # É bom deixar como nullable=True, pois serão preenchidos
    # depois que a simulação for criada e calculada.
    valor_parcela = Column(Numeric(12, 2), nullable=True)
    valor_total = Column(Numeric(12, 2), nullable=True)
    juros_total = Column(Numeric(12, 2), nullable=True)
    
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamento
    user = relationship("User", back_populates="simulacoes")
