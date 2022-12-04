"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app
app.config['SQLALCHEMY_ECHO'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        u1 = User.signup("test_username1", "test_email1", "test_password1", None)
        u1.id = 1234

        u2 = User.signup("test_username2", "test_email2", "test_password2", None)
        u2.id = 4567

        db.session.commit()

        u1 = User.query.get(u1.id) #1234
        u2 = User.query.get(u2.id) #4567

        self.u1 = u1
        self.u1_id = u1.id  

        self.u2 = u2
        self.u2_id = u2.id

        self.client = app.test_client()

    
    def tearDown(self):
        
        db.session.rollback()


    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


    ####
    # Following Tests

    def test_user_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.followers), 0)

        self.assertEqual(self.u2.followers[0].id, self.u1_id)
        self.assertEqual(self.u1.following[0].id, self.u2_id)


    def test_is_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))



    def test_is_followed_by(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertFalse(self.u1.is_followed_by(self.u2))
        self.assertTrue(self.u2.is_followed_by(self.u1))



    ###
    # Signup Tests
    #
    # def signup(cls, username, email, password, image_url)

    def test_valid_signup(self):
        new_user = User.signup("username_test", "test_email@gmail.com", "test_password", None)
        new_user.id = 9876
        db.session.commit()

        new_user = User.query.get(new_user.id)
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.username,"username_test")
        self.assertEqual(new_user.email, "test_email@gmail.com")

        # If password does not match then the password may have hashed properly
        self.assertNotEqual(new_user.password, "test_password")

        # can check to see if Bcrypt strings starts with $2b$
        self.assertTrue(new_user.password.startswith("$2b$"))


    # def test_invalid_username_signup(self):
    #     invalid_user = User.signup(None, "invalid@gmail.com", "test_password", None)
    #     invalid_user.id = 44444
    #     with self.assertRaises(IntegrityError) as context:
    #         db.session.commit()


    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", None, None)
                

    ###
    # Authentication Tests

    def test_valid_authentication(self):
        user = User.authenticate(self.u1.username, "test_password1")

        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.u1.id)


    def test_invalid_username(self):
        self.assertFalse(User.authenticate("invalidusername", "test_password"))


    def test_invalid_password(self):
        self.assertFalse(User.authenticate("test_username1", "incorrect_password"))
