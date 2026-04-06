from pydantic import BaseModel


class ClassCreate(BaseModel):
    grade: str
    section: str
    academic_year: str
    class_teacher_id: int | None = None


class ClassResponse(BaseModel):
    id: int
    school_id: int
    grade: str
    section: str
    academic_year: str
    class_teacher_id: int | None
    subject_teachers: str | None

    class Config:
        from_attributes = True
