# routes/simulations.py

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

# Imports dos módulos do projeto
import schemas.simulacao as schemas 
import security
from db import get_db
from models.models import Simulacao, User 

router = APIRouter(
    prefix="/api/simulacoes",
    tags=["Simulações"],
    dependencies=[Depends(security.get_current_active_user)]
)

# --- INÍCIO DA MUDANÇA ---

def calcular_valores_simulacao(valor_desejado: float, prazo_meses: int, tipo_emprestimo: str):
    """
    Função de exemplo para calcular os totais.
    SUBSTITUA PELA SUA REGRA DE NEGÓCIO REAL.
    """
    
    
    taxa_juros_mensal = 0.02 
    
    if tipo_emprestimo == 'imovel-garantia':
        taxa_juros_mensal = 0.01
    elif tipo_emprestimo == 'veiculo-garantia':
        taxa_juros_mensal = 0.015

    # Cálculo de juros simples (apenas para exemplo)
    juros_total = (valor_desejado * taxa_juros_mensal) * prazo_meses
    valor_total = valor_desejado + juros_total
    valor_parcela = valor_total / prazo_meses
    
    return {
        "valor_parcela": round(valor_parcela, 2),
        "valor_total": round(valor_total, 2),
        "juros_total": round(juros_total, 2)
    }

# --- FIM DA MUDANÇA ---


@router.post("/", response_model=schemas.SimulacaoOut, status_code=status.HTTP_201_CREATED, summary="Criar uma nova simulação flexível")
def criar_simulacao(
    payload: schemas.SimulacaoCreate, # <--- Continua usando o schema base
    db: Session = Depends(get_db), 
    current_user: User = Depends(security.get_current_active_user)
):
    """
    Cria um novo registro de simulação.
    """
    
    # 1. Converte o payload Pydantic para um dict
    simulacao_data = payload.model_dump() 
    
    # --- INÍCIO DA MUDANÇA ---
    
    # 2. Chama a função de cálculo
    calculos = calcular_valores_simulacao(
        valor_desejado=payload.valor_desejado,
        prazo_meses=payload.prazo_meses,
        tipo_emprestimo=payload.tipo_emprestimo
    )
    
    # 3. Adiciona os valores calculados ao dicionário
    #    (Os nomes das chaves devem bater com o seu models.py)
    simulacao_data['valor_parcela'] = calculos['valor_parcela']
    simulacao_data['valor_total'] = calculos['valor_total']
    simulacao_data['juros_total'] = calculos['juros_total']
    
    # --- FIM DA MUDANÇA ---

    # 4. Cria o modelo SQLAlchemy
    #    O **simulacao_data agora contém TUDO:
    #    (valor_desejado, prazo_meses, ... E valor_parcela, valor_total)
    nova_simulacao = Simulacao(
        **simulacao_data,
        user_id=current_user.id
    )
    
    db.add(nova_simulacao)
    db.commit()
    db.refresh(nova_simulacao)
    
    return nova_simulacao


@router.get("/", response_model=List[schemas.SimulacaoOut], summary="Listar simulações do usuário logado")
def listar_simulacoes(db: Session = Depends(get_db), current_user: User = Depends(security.get_current_active_user)):
    """
    Retorna uma lista de todas as simulações feitas pelo usuário logado.
    """
    simulacoes = db.query(Simulacao).filter(Simulacao.user_id == current_user.id).all()
    return simulacoes