from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..services.blueprints import (
    activate_blueprint,
    create_blueprint,
    create_milestone,
    create_phase,
    delete_blueprint,
    delete_milestone,
    delete_phase,
    get_active_blueprint,
    get_blueprint,
    list_blueprints,
    toggle_milestone,
    update_blueprint,
    update_phase,
)
from ..services.habits import get_demo_user_id

router = APIRouter()


class BlueprintCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None
    vision: Optional[str] = None
    target_date: Optional[str] = None
    set_active: Optional[bool] = True


class BlueprintUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    vision: Optional[str] = None
    target_date: Optional[str] = None
    status: Optional[str] = None


class PhaseCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None
    phase_number: Optional[int] = None
    area_id: Optional[int] = None


class PhaseUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class MilestoneCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None
    target_date: Optional[str] = None


@router.get("", response_model=Dict[str, Any])
async def get_all_blueprints() -> Dict[str, Any]:
    user_id = get_demo_user_id()
    blueprints = list_blueprints(user_id)
    return {"blueprints": blueprints, "count": len(blueprints)}


@router.get("/active", response_model=Dict[str, Any])
async def get_active_blueprint_endpoint() -> Dict[str, Any]:
    user_id = get_demo_user_id()
    bp = get_active_blueprint(user_id)
    return {"blueprint": bp}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_new_blueprint(payload: BlueprintCreateSchema) -> Dict[str, Any]:
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Blueprint title is required.")

    user_id = get_demo_user_id()
    bp = create_blueprint(
        user_id=user_id,
        title=payload.title,
        description=payload.description,
        vision=payload.vision,
        target_date=payload.target_date,
        set_active=payload.set_active if payload.set_active is not None else True,
    )
    return {"message": "Blueprint created successfully.", "blueprint": bp}


@router.get("/{blueprint_id}")
async def get_blueprint_by_id(blueprint_id: int) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    bp = get_blueprint(user_id, blueprint_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Blueprint not found.")
    return {"blueprint": bp}


@router.patch("/{blueprint_id}")
async def update_blueprint_endpoint(blueprint_id: int, payload: BlueprintUpdateSchema) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    bp = update_blueprint(
        user_id=user_id,
        blueprint_id=blueprint_id,
        title=payload.title,
        description=payload.description,
        vision=payload.vision,
        target_date=payload.target_date,
        status=payload.status,
    )
    if not bp:
        raise HTTPException(status_code=404, detail="Blueprint not found.")
    return {"message": "Blueprint updated.", "blueprint": bp}


@router.post("/{blueprint_id}/activate")
async def activate_blueprint_endpoint(blueprint_id: int) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    bp = activate_blueprint(user_id, blueprint_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Blueprint not found.")
    return {"message": "Blueprint activated.", "blueprint": bp}


@router.delete("/{blueprint_id}")
async def delete_blueprint_endpoint(blueprint_id: int) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    success = delete_blueprint(user_id, blueprint_id)
    if not success:
        raise HTTPException(status_code=404, detail="Blueprint not found.")
    return {"message": "Blueprint deleted successfully."}


# -------------------------------------------------------------------
# Phase Endpoints
# -------------------------------------------------------------------

@router.post("/{blueprint_id}/phases", status_code=status.HTTP_201_CREATED)
async def create_phase_endpoint(blueprint_id: int, payload: PhaseCreateSchema) -> Dict[str, Any]:
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Phase title is required.")

    user_id = get_demo_user_id()
    bp = create_phase(
        user_id=user_id,
        blueprint_id=blueprint_id,
        title=payload.title,
        description=payload.description,
        phase_number=payload.phase_number,
        area_id=payload.area_id,
    )
    if not bp:
        raise HTTPException(status_code=404, detail="Blueprint not found.")
    return {"message": "Phase added.", "blueprint": bp}


@router.patch("/phases/{phase_id}")
async def update_phase_endpoint(phase_id: int, payload: PhaseUpdateSchema) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    bp = update_phase(
        user_id=user_id,
        phase_id=phase_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
    )
    if not bp:
        raise HTTPException(status_code=404, detail="Phase not found.")
    return {"message": "Phase updated.", "blueprint": bp}


@router.delete("/phases/{phase_id}")
async def delete_phase_endpoint(phase_id: int) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    success = delete_phase(user_id, phase_id)
    if not success:
        raise HTTPException(status_code=404, detail="Phase not found.")
    return {"message": "Phase deleted successfully."}


# -------------------------------------------------------------------
# Milestone Endpoints
# -------------------------------------------------------------------

@router.post("/phases/{phase_id}/milestones", status_code=status.HTTP_201_CREATED)
async def create_milestone_endpoint(phase_id: int, payload: MilestoneCreateSchema) -> Dict[str, Any]:
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Milestone title is required.")

    user_id = get_demo_user_id()
    bp = create_milestone(
        user_id=user_id,
        phase_id=phase_id,
        title=payload.title,
        description=payload.description,
        target_date=payload.target_date,
    )
    if not bp:
        raise HTTPException(status_code=404, detail="Phase not found.")
    return {"message": "Milestone added.", "blueprint": bp}


@router.post("/milestones/{milestone_id}/toggle")
async def toggle_milestone_endpoint(milestone_id: int) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    bp = toggle_milestone(user_id, milestone_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Milestone not found.")
    return {"message": "Milestone status updated.", "blueprint": bp}


@router.delete("/milestones/{milestone_id}")
async def delete_milestone_endpoint(milestone_id: int) -> Dict[str, Any]:
    user_id = get_demo_user_id()
    success = delete_milestone(user_id, milestone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Milestone not found.")
    return {"message": "Milestone deleted successfully."}
