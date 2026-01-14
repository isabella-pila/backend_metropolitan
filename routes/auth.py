# routes/auth.py

from datetime import timedelta, datetime, timezone
import random
import string

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

# Seus imports existentes
import schemas.user as schemas
import security
from db import get_db
from models.models import User

# Imports para envio de e-mail
from fastapi_mail import FastMail, MessageSchema
from routes.contact import conf 

router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticação"]
)

class ForgotPasswordPayload(BaseModel):
    email: EmailStr

class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str

class VerificationPayload(BaseModel):
    email: EmailStr
    code: str

class ResendVerificationPayload(BaseModel):
    email: EmailStr

# --- Função auxiliar para gerar código ---
def create_verification_code(length: int = 6) -> str:
    """Gera um código de verificação numérico aleatório."""
    return "".join(random.choices(string.digits, k=length))


# ==============================================================================
# ROTA 1: LOGIN (MODIFICADA - Bypassed)
# ==============================================================================
@router.post("/token")
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = security.get_user_by_email(db, email=form_data.username)
    
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # --- MUDANÇA TEMPORÁRIA: Verificação comentada ---
    # if not user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Email not verified. Please check your inbox for the verification code."
    #     )
    # -------------------------------------------------
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ==============================================================================
# ROTA 2: CADASTRO (MODIFICADA - Já nasce verificado e não envia e-mail)
# ==============================================================================
@router.post("/clientes", status_code=status.HTTP_201_CREATED, summary="Criar um novo cliente")
def criar_cliente(payload: schemas.UserCreate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    if db.query(User).filter(User.cpf == payload.cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado")

    verification_code = create_verification_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15) 

    hashed_pwd = security.hash_password(payload.password)
    
    # --- MUDANÇA 1: is_verified=True direto ---
    novo_usuario = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower().strip(),
        phone=payload.phone.strip(),
        cpf=payload.cpf.strip(),
        password_hash=hashed_pwd,
        is_verified=True,  # <--- FORÇANDO VERDADEIRO
        verification_code=verification_code,
        verification_expires_at=expires_at
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    # --- MUDANÇA 2: Envio de e-mail comentado ---
    # html_body = f""" ... (seu html) ... """
    
    # message = MessageSchema(
    #     subject="Seu Código de Verificação - Metropolitan",
    #     recipients=[novo_usuario.email],
    #     body="Seu código é: " + verification_code, # Simplifiquei aqui só pra comentar
    #     subtype="html"
    # )
    
    # fm = FastMail(conf)
    # background_tasks.add_task(fm.send_message, message) # <--- COMENTADO PARA NÃO TRAVAR O SERVER
    # ---------------------------------------------------

    return {"message": "Cliente criado com sucesso. Login liberado automaticamente (Modo de Teste)."}


# ==============================================================================
# OUTRAS ROTAS (Reenviar código e Verificar)
# ==============================================================================
@router.post("/resend-verification", status_code=status.HTTP_200_OK, summary="Reenviar código de verificação")
def resend_verification_code(
    payload: ResendVerificationPayload,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # Comentado o envio de e-mail para não travar
    return {"message": "Funcionalidade de e-mail temporariamente desativada."}


@router.post("/verify", status_code=status.HTTP_200_OK, summary="Verificar e-mail do usuário")
def verify_user_email(payload: VerificationPayload, db: Session = Depends(get_db)):
    # Essa rota fica meio inútil agora, mas pode deixar ativa caso alguém tente usar
    user = security.get_user_by_email(db, email=payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    
    user.is_verified = True
    db.commit()
    return {"message": "E-mail verificado com sucesso!"}


# ==============================================================================
# RECUPERAÇÃO DE SENHA (MODIFICADA - Não envia e-mail)
# ==============================================================================
@router.post("/forgot-password", status_code=status.HTTP_200_OK, summary="Solicitar redefinição de senha")
def request_password_reset(
    payload: ForgotPasswordPayload,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    user = security.get_user_by_email(db, email=payload.email)

    if user:
        expires_delta = timedelta(minutes=15)
        reset_token = security.create_access_token(
            data={"sub": user.email, "type": "reset"}, expires_delta=expires_delta
        )
        
        # --- MUDANÇA: Comentei o envio de e-mail para não dar erro 500 ---
        # message = MessageSchema(...)
        # fm = FastMail(conf)
        # background_tasks.add_task(fm.send_message, message)
        
        # Para você conseguir testar localmente, vou imprimir o link no log do servidor
        print(f"LINK DE RESET (MODO DEBUG): http://bancometropolitan.com.br/redefinir-senha?token={reset_token}")

    return {"message": "Se uma conta existir, o link foi gerado (verifique o console do servidor em modo debug)."}


@router.post("/reset-password", status_code=status.HTTP_200_OK, summary="Redefinir a senha")
def reset_password(payload: ResetPasswordPayload, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = security.verify_token(payload.token, credentials_exception)
    user = security.get_user_by_email(db, email=email)

    if not user:
        raise credentials_exception

    new_hashed_password = security.hash_password(payload.new_password)
    user.password_hash = new_hashed_password
    db.commit()

    return {"message": "Sua senha foi redefinida com sucesso!"}