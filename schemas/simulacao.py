# schemas/simulacao.py

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class SimulacaoBase(BaseModel):
    # === 1. DADOS GERAIS DA SIMULAÇÃO ===
    # (Campos fixos que você usa para calcular)
    
    valor_desejado: float   # "Quanto você precisa?"
    prazo_meses: int        # "Em quanto tempo?"
    
    # --- CAMPO QUE VOCÊ ACABOU DE MENCIONAR ---
    motivo_emprestimo: str  # "Para que a pessoa precisa do empréstimo"
    # ----------------------------------------
    
    tipo_emprestimo: str    # "home_equity", "car_equity", "med_plan"

    
    # === 2. DADOS ESPECÍFICOS ===
    # (O JSON flexível que NÃO atrapalha)
    # Aqui entram as perguntas de Home Equity, Car Equity, MedPlan...
    dados_especificos: Dict[str, Any] 

class SimulacaoCreate(SimulacaoBase):
    pass

class SimulacaoOut(SimulacaoBase):
    id: int
    user_id: int
    criado_em: datetime
    status: Optional[str] = None

    class Config:
        orm_mode = True