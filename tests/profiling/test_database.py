# test_student_profile.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from agents.profiling.database import Base, StudentProfile
import datetime

# Configure test database
DATABASE_URI = 'sqlite:///:memory:'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

@pytest.fixture(scope='module')
def session():
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.close()

def test_create_student_profile(session):
    # Test creating a student profile
    new_student = StudentProfile(
        student_id='12345',
        performance_score=88.5,
        learning_preferences='visual',
        recent_topics='algebra, geometry'
    )
    session.add(new_student)
    session.commit()

    retrieved_student = session.query(StudentProfile).filter_by(student_id='12345').one()
    assert retrieved_student.student_id == '12345'
    assert retrieved_student.performance_score == 88.5
    assert retrieved_student.learning_preferences == 'visual'
    assert 'algebra' in retrieved_student.recent_topics

def test_update_student_profile(session):
    # Test updating a student profile
    student = session.query(StudentProfile).filter_by(student_id='12345').one()
    student.performance_score = 92.3
    student.recent_topics += ', calculus'
    session.commit()

    updated_student = session.query(StudentProfile).filter_by(student_id='12345').one()
    assert updated_student.performance_score == 92.3
    assert 'calculus' in updated_student.recent_topics

def test_datetime_set_on_creation(session):
    # Test that the datetime is set on creation
    student = session.query(StudentProfile).filter_by(student_id='12345').one()
    assert isinstance(student.last_interaction, datetime.datetime)
