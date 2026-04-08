def register_school(client):
    response = client.post(
        "/api/auth/register",
        json={
            "school_name": "Setup School",
            "school_email": "setup-admin@testschool.com",
            "school_phone": "9999999999",
            "school_city": "Delhi",
            "school_state": "Delhi",
            "admin_first_name": "Setup",
            "admin_last_name": "Admin",
            "admin_password": "testpass123",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_admin_can_create_classes_users_and_linked_student(client):
    token = register_school(client)
    headers = {"Authorization": f"Bearer {token}"}

    teacher_response = client.post(
        "/api/users",
        headers=headers,
        json={
            "role": "teacher",
            "first_name": "Priya",
            "last_name": "Mehta",
            "email": "priya@testschool.com",
            "password": "teacherpass123",
            "phone": "9876543210",
            "language": "en",
        },
    )
    assert teacher_response.status_code == 201
    teacher_id = teacher_response.json()["id"]

    parent_response = client.post(
        "/api/users",
        headers=headers,
        json={
            "role": "parent",
            "first_name": "Ravi",
            "last_name": "Kumar",
            "email": "ravi.parent@testschool.com",
            "password": "parentpass123",
            "phone": "9876543211",
            "language": "hi",
        },
    )
    assert parent_response.status_code == 201
    parent_id = parent_response.json()["id"]

    class_response = client.post(
        "/api/classes",
        headers=headers,
        json={
            "grade": "8",
            "section": "A",
            "academic_year": "2026-27",
            "class_teacher_id": teacher_id,
        },
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["id"]

    student_response = client.post(
        "/api/students",
        headers=headers,
        json={
            "class_id": class_id,
            "parent_id": parent_id,
            "first_name": "Rahul",
            "last_name": "Kumar",
            "roll_number": "2026001",
            "date_of_birth": "2012-05-10",
            "gender": "male",
            "phone": "9876543212",
            "address": "Delhi",
        },
    )
    assert student_response.status_code == 201
    assert student_response.json()["parent_id"] == parent_id

    list_response = client.get("/api/students", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_admin_can_create_student_with_localized_date_format(client):
    token = register_school(client)
    headers = {"Authorization": f"Bearer {token}"}

    class_response = client.post(
        "/api/classes",
        headers=headers,
        json={
            "grade": "9",
            "section": "A",
            "academic_year": "2026-27",
        },
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["id"]

    student_response = client.post(
        "/api/students",
        headers=headers,
        json={
            "class_id": class_id,
            "first_name": "Satyam",
            "last_name": "Tiwari",
            "roll_number": "25",
            "date_of_birth": "11/10/2004",
            "gender": "male",
            "phone": "9198530867",
            "address": "Gorakhpur",
        },
    )
    assert student_response.status_code == 201
    assert student_response.json()["date_of_birth"] == "2004-10-11"


def test_student_creation_rejects_class_from_another_school(client):
    token_school_a = register_school(client)
    headers_school_a = {"Authorization": f"Bearer {token_school_a}"}

    class_response = client.post(
        "/api/classes",
        headers=headers_school_a,
        json={
            "grade": "10",
            "section": "B",
            "academic_year": "2026-27",
        },
    )
    assert class_response.status_code == 201
    foreign_class_id = class_response.json()["id"]

    register_other_school = client.post(
        "/api/auth/register",
        json={
            "school_name": "Other School",
            "school_email": "other-admin@testschool.com",
            "school_phone": "8888888888",
            "school_city": "Lucknow",
            "school_state": "UP",
            "admin_first_name": "Other",
            "admin_last_name": "Admin",
            "admin_password": "testpass123",
        },
    )
    assert register_other_school.status_code == 201
    token_school_b = register_other_school.json()["access_token"]
    headers_school_b = {"Authorization": f"Bearer {token_school_b}"}

    student_response = client.post(
        "/api/students",
        headers=headers_school_b,
        json={
            "class_id": foreign_class_id,
            "first_name": "Cross",
            "last_name": "Tenant",
            "roll_number": "1",
        },
    )
    assert student_response.status_code == 400
    assert student_response.json()["detail"] == "Selected class was not found in your school."


def test_student_creation_rejects_non_parent_account_link(client):
    token = register_school(client)
    headers = {"Authorization": f"Bearer {token}"}

    teacher_response = client.post(
        "/api/users",
        headers=headers,
        json={
            "role": "teacher",
            "first_name": "Amit",
            "last_name": "Sir",
            "email": "amit.teacher@testschool.com",
            "password": "teacherpass123",
            "phone": "9876500000",
            "language": "en",
        },
    )
    assert teacher_response.status_code == 201
    teacher_id = teacher_response.json()["id"]

    class_response = client.post(
        "/api/classes",
        headers=headers,
        json={
            "grade": "6",
            "section": "C",
            "academic_year": "2026-27",
            "class_teacher_id": teacher_id,
        },
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["id"]

    student_response = client.post(
        "/api/students",
        headers=headers,
        json={
            "class_id": class_id,
            "parent_id": teacher_id,
            "first_name": "Wrong",
            "last_name": "Link",
            "roll_number": "66",
        },
    )
    assert student_response.status_code == 400
    assert student_response.json()["detail"] == "Selected parent account was not found."


def test_student_creation_succeeds_even_if_cache_invalidate_fails(client, monkeypatch):
    token = register_school(client)
    headers = {"Authorization": f"Bearer {token}"}

    class_response = client.post(
        "/api/classes",
        headers=headers,
        json={
            "grade": "7",
            "section": "D",
            "academic_year": "2026-27",
        },
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["id"]

    async def fail_cache_invalidate(_: str):
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr(
        "app.api.students.cache_invalidate",
        fail_cache_invalidate
    )

    student_response = client.post(
        "/api/students",
        headers=headers,
        json={
            "class_id": class_id,
            "first_name": "Cache",
            "last_name": "Safe",
            "roll_number": "77",
        },
    )
    assert student_response.status_code == 201


def test_attendance_mark_succeeds_even_if_cache_invalidate_fails(client, monkeypatch):
    token = register_school(client)
    headers = {"Authorization": f"Bearer {token}"}

    class_response = client.post(
        "/api/classes",
        headers=headers,
        json={
            "grade": "5",
            "section": "A",
            "academic_year": "2026-27",
        },
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["id"]

    student_response = client.post(
        "/api/students",
        headers=headers,
        json={
            "class_id": class_id,
            "first_name": "Attend",
            "last_name": "Safe",
            "roll_number": "501",
        },
    )
    assert student_response.status_code == 201
    student_id = student_response.json()["id"]

    async def fail_cache_invalidate(_: str):
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr(
        "app.api.attendance.cache_invalidate",
        fail_cache_invalidate
    )

    response = client.post(
        "/api/attendance",
        headers=headers,
        json={
            "student_id": student_id,
            "class_id": class_id,
            "date": "2026-04-08",
            "status": "present",
        },
    )
    assert response.status_code == 201


def test_marks_create_succeeds_even_if_cache_invalidate_fails(client, monkeypatch):
    token = register_school(client)
    headers = {"Authorization": f"Bearer {token}"}

    class_response = client.post(
        "/api/classes",
        headers=headers,
        json={
            "grade": "5",
            "section": "B",
            "academic_year": "2026-27",
        },
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["id"]

    student_response = client.post(
        "/api/students",
        headers=headers,
        json={
            "class_id": class_id,
            "first_name": "Marks",
            "last_name": "Safe",
            "roll_number": "502",
        },
    )
    assert student_response.status_code == 201
    student_id = student_response.json()["id"]

    async def fail_cache_invalidate(_: str):
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr(
        "app.api.marks.cache_invalidate",
        fail_cache_invalidate
    )

    response = client.post(
        "/api/marks",
        headers=headers,
        json={
            "student_id": student_id,
            "class_id": class_id,
            "subject": "Mathematics",
            "exam_type": "unit_test",
            "exam_date": "2026-04-08",
            "score": 45,
            "max_score": 100,
        },
    )
    assert response.status_code == 201
