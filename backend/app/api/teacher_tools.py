# backend/app/api/teacher_tools.py

import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.security import TeacherOrAdmin, get_current_school_id
from app.core.llm import (
    LLMConfigurationError,
    LLMServiceError,
    safe_llm_call,
)

router = APIRouter(prefix="/api/teacher-tools", tags=["Teacher Co-Pilot"])

AUTH_RESPONSES = {
    401: {
        "description": "Not authenticated. Send `Authorization: Bearer <access_token>`.",
    },
    403: {
        "description": "Authenticated, but only teachers and admins can use this endpoint.",
    },
    502: {
        "description": "The AI provider request failed. Check backend logs and OpenAI configuration.",
    },
    503: {
        "description": "The AI provider is not configured for this backend environment.",
    },
}


def parse_ai_json(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="AI returned invalid JSON") from exc


def raise_teacher_tool_error(exc: Exception) -> None:
    if isinstance(exc, LLMConfigurationError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if isinstance(exc, LLMServiceError):
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    raise exc


class LessonPlanRequest(BaseModel):
    subject:       str
    grade:         str
    topic:         str
    duration_mins: int = 45
    # Optional context for adaptive planning
    weak_areas:    Optional[list[str]] = None


class MCQRequest(BaseModel):
    subject: str
    topic:   str
    grade:   str
    count:   int = 10
    difficulty: str = "medium"   # easy | medium | hard


class WorksheetRequest(BaseModel):
    subject:    str
    topic:      str
    grade:      str
    question_count: int = 15


@router.post(
    "/lesson-plan",
    summary="Generate a lesson plan",
    responses=AUTH_RESPONSES,
)
async def generate_lesson_plan(
    payload: LessonPlanRequest,
    school_id: int = Depends(get_current_school_id),
    _=TeacherOrAdmin,
):
    """
    Generate a complete lesson plan for a topic.
    Requires a logged-in teacher/admin Bearer token.
    Uses GPT-4o for high quality structured output.
    Takes 5–15 seconds, which is expected for this tool.
    """
    weak_context = (
        f"\nNote: Students are weak in: {', '.join(payload.weak_areas)}. "
        "Spend extra time on these areas."
        if payload.weak_areas else ""
    )

    prompt = f"""
Create a detailed lesson plan for an Indian school teacher.

Subject:  {payload.subject}
Grade:    {payload.grade}
Topic:    {payload.topic}
Duration: {payload.duration_mins} minutes
{weak_context}

Return a JSON object with this exact structure:
{{
  "title": "Lesson title",
  "grade": "{payload.grade}",
  "subject": "{payload.subject}",
  "topic": "{payload.topic}",
  "duration_mins": {payload.duration_mins},
  "learning_objectives": ["objective 1", "objective 2", "objective 3"],
  "materials_needed": ["item 1", "item 2"],
  "sections": [
    {{
      "name": "Introduction",
      "duration_mins": 5,
      "activity": "Description of what teacher does",
      "teacher_actions": "Specific teacher instructions",
      "student_actions": "What students do"
    }},
    {{
      "name": "Main Teaching",
      "duration_mins": 25,
      "activity": "...",
      "teacher_actions": "...",
      "student_actions": "..."
    }},
    {{
      "name": "Practice",
      "duration_mins": 10,
      "activity": "...",
      "teacher_actions": "...",
      "student_actions": "..."
    }},
    {{
      "name": "Summary & Assessment",
      "duration_mins": 5,
      "activity": "...",
      "teacher_actions": "...",
      "student_actions": "..."
    }}
  ],
  "homework": "Homework assignment description",
  "assessment_questions": ["Question 1?", "Question 2?", "Question 3?"],
  "tips_for_teacher": ["Tip 1", "Tip 2"]
}}
"""
    try:
        text, cost = await safe_llm_call(
            prompt=prompt,
            model="gpt-4o",
            max_tokens=1500,
            expect_json=True,
        )
        result = parse_ai_json(text)
    except Exception as exc:
        raise_teacher_tool_error(exc)

    return {"lesson_plan": result, "cost_usd": round(cost, 6)}


@router.post(
    "/mcqs",
    summary="Generate MCQs",
    responses=AUTH_RESPONSES,
)
async def generate_mcqs(
    payload: MCQRequest,
    school_id: int = Depends(get_current_school_id),
    _=TeacherOrAdmin,
):
    """
    Generate multiple choice questions for a topic.
    Requires a logged-in teacher/admin Bearer token.
    Perfect for quick quizzes and exam preparation.
    """
    prompt = f"""
Generate {payload.count} multiple choice questions for an Indian school exam.

Subject:    {payload.subject}
Grade:      {payload.grade}
Topic:      {payload.topic}
Difficulty: {payload.difficulty}

Rules:
- Each question must have exactly 4 options (A, B, C, D)
- Only one correct answer per question
- Include a brief explanation for the correct answer
- Questions should test understanding, not just memorisation
- Use clear, simple English appropriate for Grade {payload.grade}

Return JSON only:
{{
  "subject": "{payload.subject}",
  "topic": "{payload.topic}",
  "grade": "{payload.grade}",
  "difficulty": "{payload.difficulty}",
  "questions": [
    {{
      "number": 1,
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct_answer": "B",
      "explanation": "Brief explanation of why B is correct"
    }}
  ]
}}
"""
    try:
        text, cost = await safe_llm_call(
            prompt=prompt,
            model="gpt-4o",
            max_tokens=2000,
            expect_json=True,
        )
        result = parse_ai_json(text)
    except Exception as exc:
        raise_teacher_tool_error(exc)

    return {"mcqs": result, "cost_usd": round(cost, 6)}


@router.post(
    "/worksheet",
    summary="Generate a worksheet",
    responses=AUTH_RESPONSES,
)
async def generate_worksheet(
    payload: WorksheetRequest,
    school_id: int = Depends(get_current_school_id),
    _=TeacherOrAdmin,
):
    """
    Generate a printable worksheet with mixed question types.
    Requires a logged-in teacher/admin Bearer token.
    """
    prompt = f"""
Create a student worksheet for an Indian school.

Subject:         {payload.subject}
Grade:           {payload.grade}
Topic:           {payload.topic}
Total questions: {payload.question_count}

Include a mix of:
- Fill in the blanks (3–4 questions)
- True or False (3–4 questions)
- Short answer (3–4 questions)
- One long answer / problem-solving question

Return JSON only:
{{
  "title": "Worksheet title",
  "subject": "{payload.subject}",
  "grade": "{payload.grade}",
  "topic": "{payload.topic}",
  "instructions": "General instructions for students",
  "sections": [
    {{
      "type": "fill_in_the_blank",
      "title": "Section A: Fill in the blanks",
      "marks_each": 1,
      "questions": [
        {{"number": 1, "question": "The _____ is the powerhouse of the cell.", "answer": "mitochondria"}}
      ]
    }},
    {{
      "type": "true_or_false",
      "title": "Section B: True or False",
      "marks_each": 1,
      "questions": [
        {{"number": 1, "question": "Statement here.", "answer": "True"}}
      ]
    }},
    {{
      "type": "short_answer",
      "title": "Section C: Short Answer",
      "marks_each": 2,
      "questions": [
        {{"number": 1, "question": "Question here?", "answer": "Model answer"}}
      ]
    }},
    {{
      "type": "long_answer",
      "title": "Section D: Long Answer",
      "marks_each": 5,
      "questions": [
        {{"number": 1, "question": "Detailed question here?", "answer": "Model answer points"}}
      ]
    }}
  ],
  "total_marks": {payload.question_count + 5}
}}
"""
    try:
        text, cost = await safe_llm_call(
            prompt=prompt,
            model="gpt-4o",
            max_tokens=2000,
            expect_json=True,
        )
        result = parse_ai_json(text)
    except Exception as exc:
        raise_teacher_tool_error(exc)

    return {"worksheet": result, "cost_usd": round(cost, 6)}
