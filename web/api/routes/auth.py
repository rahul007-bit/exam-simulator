from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from web.api import users
from web.api.auth_sessions import (
    AUTH_COOKIE,
    SESSION_TTL_SECONDS,
    create_session,
    destroy_session,
    resolve_session,
)
from web.api.schemas import CreateUserRequest, LoginRequest
from web.api.security import require_admin

router = APIRouter()


@router.post("/api/auth/login")
def auth_login(req: LoginRequest, response: Response):
    """Verifies credentials and issues an auth session cookie."""
    user = users.get_user(req.username)
    if not user or not users.verify_password(req.password, user.get("password_hash") or ""):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_session(user["username"], user["role"])
    response.set_cookie(
        key=AUTH_COOKIE,
        value=token,
        httponly=True,
        max_age=SESSION_TTL_SECONDS,
        path="/",
        samesite="lax",
    )
    return {"status": "ok", "username": user["username"], "role": user["role"]}


@router.post("/api/auth/logout")
def auth_logout(request: Request, response: Response):
    """Destroys the auth session and clears the cookie."""
    destroy_session(request)
    response.delete_cookie(key=AUTH_COOKIE, path="/")
    return {"status": "ok", "authenticated": False}


@router.get("/api/auth/me")
def auth_me(request: Request):
    """Returns the authenticated user for the current session."""
    session = resolve_session(request)
    if not session:
        return JSONResponse(status_code=401, content={"authenticated": False})
    return {
        "username": session["username"],
        "role": session["role"],
        "authenticated": True,
    }


@router.post("/api/admin/users")
def admin_create_user(req: CreateUserRequest, request: Request):
    """Creates a user (admin only)."""
    require_admin(request)
    try:
        user = users.create_user(req.username, req.password, req.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok", "user": {k: v for k, v in user.items() if k != "password_hash"}}


@router.get("/api/admin/users")
def admin_list_users(request: Request):
    """Lists all users (admin only)."""
    require_admin(request)
    all_users = users.list_users()
    return {"users": all_users, "total": len(all_users)}


@router.delete("/api/admin/users/{username}")
def admin_delete_user(username: str, request: Request):
    """Deletes a user (admin only); never the caller or the last admin."""
    require_admin(request)

    session = resolve_session(request)
    caller = session.get("username") if session else None
    if caller and caller == username:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    target = users.get_user(username)
    if not target:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    if target.get("role") == "admin":
        admins = [u for u in users.list_users() if u.get("role") == "admin"]
        if len(admins) <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin")

    users.delete_user(username)
    return {"status": "ok", "username": username}
