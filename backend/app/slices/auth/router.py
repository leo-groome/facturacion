from fastapi import APIRouter, HTTPException, Request, status
from psycopg.rows import dict_row
from app.slices.auth import schemas, security

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: schemas.UserSignup, request: Request):
    db_pool = request.app.state.db_pool
    hashed_pwd = security.hash_password(user.password)
    
    query = """
        INSERT INTO clientes (nombre_empresa, rfc, contrasena)
        VALUES (%s, %s, %s)
        RETURNING id;
    """
    
    try:
        async with db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    query, 
                    (user.nombre_empresa, user.rfc.upper(), hashed_pwd)
                )
                await conn.commit()
    except Exception as e:
        # Log interno para diagnostico (NUNCA exponer al cliente)
        import traceback
        traceback.print_exc()
        # Prevencion de exposicion de detalles internos y manejo de constraint violation (RFC unico)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Condicion de conflicto: El RFC registrado ya existe o hubo un error estructural."
        )

    return {"message": "Usuario creado satisfactoriamente"}


@router.post("/login", response_model=schemas.Token, status_code=status.HTTP_200_OK)
async def login(credentials: schemas.UserLogin, request: Request):
    db_pool = request.app.state.db_pool
    rfc_target = credentials.rfc.upper()
    
    query = "SELECT id, rfc, contrasena FROM clientes WHERE rfc = %s"
    
    async with db_pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, (rfc_target,))
            db_user = await cur.fetchone()

    # Evaluacion segura de hash contra ataques de timing
    if not db_user or not security.verify_password(credentials.password, db_user["contrasena"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas"
        )
        
    access_token = security.create_access_token(
        data={"id": str(db_user["id"]), "org": db_user["rfc"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
