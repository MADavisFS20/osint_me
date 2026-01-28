#!/data/data/com.termux/files/usr/bin/env python3
"""
SQLModel DB models for Termux-OSINT Manager v1.1.0
"""
from typing import Optional
from sqlmodel import SQLModel, Field, Column, String, JSON
import time

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, nullable=False, sa_column=Column(String, unique=True))
    pw_hash: str
    role: str = "operator"  # operator / admin
    created_at: float = Field(default_factory=lambda: time.time())

class RevokedToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    jti: str  # token id
    revoked_at: float = Field(default_factory=lambda: time.time())

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    owner: Optional[str] = None
    created_at: float = Field(default_factory=lambda: time.time())

class Target(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int
    value: str  # domain or IP
    note: Optional[str] = None
    in_scope: bool = True
    created_at: float = Field(default_factory=lambda: time.time())

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_type: str
    target: str
    project_id: Optional[int] = None
    requested_by: Optional[str] = None
    status: str = "queued"  # queued / running / done / error
    created_at: float = Field(default_factory=lambda: time.time())
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

class Result(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int
    output: Optional[str] = None
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: float = Field(default_factory=lambda: time.time())

class Investigation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    owner: Optional[str] = None
    scope_note: Optional[str] = None
    created_at: float = Field(default_factory=lambda: time.time())

class Evidence(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    investigation_id: int
    kind: str  # result, file, profile, image, crawler
    title: Optional[str] = None
    reference: Optional[str] = None  # path or "job:<id>" or URL
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: float = Field(default_factory=lambda: time.time())