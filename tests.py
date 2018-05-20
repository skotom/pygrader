#!/usr/bin/env python
from datetime import datetime, timedelta
import unittest
from app import create_app, db
from app.models import User, Course
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    ELASTICSEARCH_URL = None


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=identicon&s=128'))

    def test_enrollment(self):
        u = User(username='john', email='john@example.com')
        c = Course(title='matematika')
        db.session.add(u)
        db.session.add(c)
        db.session.commit()
        self.assertEqual(u.courses.all(), [])
        self.assertEqual(c.users.all(), [])

        u.enroll(c)
        db.session.commit()
        self.assertTrue(u.is_enrolled(c))
        self.assertEqual(u.courses.count(), 1)
        self.assertEqual(u.courses.first().title, 'matematika')
        self.assertEqual(c.users.count(), 1)
        self.assertEqual(c.users.first().username, 'john')

        u.withdraw(c)
        db.session.commit()
        self.assertFalse(u.is_enrolled(c))
        self.assertEqual(u.courses.count(), 0)
        self.assertEqual(c.users.count(), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
