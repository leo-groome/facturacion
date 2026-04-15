import logging
from fastapi import APIRouter, HTTPException, Request, status
from psycopg.rows import dict_row
from app.slices.auth import schemas, security

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
async def signup(user: schemas.UserSignup, request: Request):
    db_pool = request.app.state.db_pool
    hashed_pwd = security.hash_password(user.password)

    query = """
        INSERT INTO clientes (nombre_empresa, rfc, contrasena)
        VALUES (%s, %s, %s)
        RETURNING id, rfc;
    """

    try:
        async with db_pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    query,
                    (user.nombre_empresa, user.rfc.upper(), hashed_pwd)
                )
                new_user = await cur.fetchone()
                await conn.commit()
    except Exception:
        logger.exception("Error en registro de usuario")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Condicion de conflicto: El RFC registrado ya existe o hubo un error estructural."
        )

    access_token = security.create_access_token(
        data={"id": str(new_user["id"]), "org": new_user["rfc"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


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
