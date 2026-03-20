
# backend/seed_data.py
# Run once: python seed_data.py
# This creates test data so you can test APIs in Phase 3
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from datetime import date, datetime

from app.models.base import Base
from app.models.school import School, SubscriptionTier
from app.models.user import User, UserRole
from app.models.class_ import Class_
from app.models.student import Student
from app.models.marks import Marks, ExamType
from app.models.attendance import Attendance, AttendanceStatus
from app.models.fee import FeeRecord, FeeStatus, FeeType
from app.models.agent_log import AgentLog
from app.models.notif_queue import NotificationQueue
from app.models.notification import Notification

DATABASE_URL = "postgresql://schooladmin:schoolpass123@localhost:5432/schoolos"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()
print("Clearing existing seed data...")

db.execute(text("""
TRUNCATE TABLE 
    agent_logs,
    notification_queue,
    notifications,
    fee_records,
    attendance,
    marks,
    students,
    classes,
    users,
    schools
CASCADE;
"""))

db.commit()
print("Database cleared.")
pwd = CryptContext(schemes=["bcrypt"])

print("Seeding database...")

# 1. Create school
school = School(
    name="Delhi Public School",
    email="admin@dps.edu.in",
    phone="011-12345678",
    city="New Delhi",
    state="Delhi",
    subscription_tier=SubscriptionTier.pro
)
db.add(school)
db.flush()  # get school.id without committing
print(f"Created school: {school.name} (id={school.id})")

# 2. Create admin user
admin = User(
    school_id=school.id, role=UserRole.admin,
    first_name="Rajesh", last_name="Sharma",
    email="admin@dps.edu.in",
    hashed_password=pwd.hash("admin123")
)
db.add(admin)

# 3. Create teachers
teachers = []
for i, (fn, ln, subj) in enumerate([
    ("Priya", "Mehta", "Mathematics"),
    ("Amit", "Kumar", "Science"),
    ("Sunita", "Verma", "English"),
]):
    t = User(
        school_id=school.id, role=UserRole.teacher,
        first_name=fn, last_name=ln,
        email=f"teacher{i+1}@dps.edu.in",
        hashed_password=pwd.hash("teacher123")
    )
    db.add(t)
    teachers.append(t)
db.flush()
print(f"Created {len(teachers)} teachers")

# 4. Create classes
classes = []
for grade, section in [("8", "A"), ("8", "B"), ("9", "A")]:
    c = Class_(
        school_id=school.id,
        class_teacher_id=teachers[0].id,
        grade=grade, section=section,
        academic_year="2024-25"
    )
    db.add(c)
    classes.append(c)
db.flush()
print(f"Created {len(classes)} classes")

# 5. Create parents + students
for i in range(5):
    parent = User(
        school_id=school.id, role=UserRole.parent,
        first_name=f"Parent{i+1}", last_name="Kumar",
        email=f"parent{i+1}@gmail.com",
        phone="+919517249884",  # same phone for all parents for testing
        # phone=f"+919517249884{i}",  # unique phone for each parent
        hashed_password=pwd.hash("parent123")
    )
    db.add(parent)
    db.flush()

    student = Student(
        school_id=school.id,
        class_id=classes[i % len(classes)].id,
        parent_id=parent.id,
        first_name=f"Student{i+1}", last_name="Kumar",
        roll_number=f"2024{i+1:03d}",
        date_of_birth=date(2010, 1, i+1)
    )
    db.add(student)
    db.flush()

    # Add sample marks
    for subj in ["Mathematics", "Science", "English"]:
        m = Marks(
            school_id=school.id, student_id=student.id,
            class_id=student.class_id, entered_by=teachers[0].id,
            subject=subj, exam_type=ExamType.unit_test,
            exam_date=date(2024, 10, 15),
            score=round(60 + i * 5, 1), max_score=100
        )
        db.add(m)

    # Add attendance records
    for day in range(1, 6):
        a = Attendance(
            school_id=school.id, student_id=student.id,
            class_id=student.class_id, marked_by=teachers[0].id,
            date=date(2024, 10, day),
            status=AttendanceStatus.present if day != 3 else AttendanceStatus.absent
        )
        db.add(a)

    # Add fee record
    f = FeeRecord(
        school_id=school.id, student_id=student.id,
        fee_type=FeeType.tuition, amount=15000.0,
        due_date=date(2024, 11, 1),
        status=FeeStatus.due, academic_year="2024-25"
    )
    db.add(f)

db.commit()
print("Seed data inserted successfully!")
print("\nTest credentials:")
print("  Admin:   admin@dps.edu.in / admin123")
print("  Teacher: teacher1@dps.edu.in / teacher123")
print("  Parent:  parent1@gmail.com / parent123")
db.close()