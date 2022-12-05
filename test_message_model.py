"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

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
    """ Test views for messages """

    def setUp(self):
        """ Set up before each test and sample data """

        db.drop_all()
        db.create_all()

        sample_user = User.signup("test_username", "test@gmail.com", "test_password", None)
        sample_user.id = 1111
        db.session.commit()

        self.user = User.query.get(sample_user.id)

        self.client = app.test_client()


    def tearDown(self):
        db.session.rollback()

    
    def test_message_model(self):
        """ Check if model works """

        message = Message(text="a test", user_id=self.user.id)

        db.session.add(message)
        db.session.commit()

        # Should only have one message added by user with id 1111
        self.assertEqual(len(self.user.messages), 1)

    
    def test_message_likes(self):
        test_user = User.signup("test_user", "test@email.com", "test_password", None)
        test_user.id = 9999
        
        # messages created by user with id 1111
        m1 = Message(text="this is a text", user_id=self.user.id)
        m2 = Message(text="testing is tedious...", user_id=self.user.id)

        db.session.add_all([test_user, m1, m2])
        db.session.commit()

        # add m1 to likes (relationship between User and Message with secondary = likes table) for test_user
        test_user.likes.append(m1)
        db.session.commit()

        # query for messages liked by test_user; should only be 1 message here
        liked_stuff = Likes.query.filter(Likes.user_id == test_user.id).all()
        self.assertEqual(len(liked_stuff), 1)
        self.assertEqual(liked_stuff[0].message_id, m1.id)

        # "like" another message
        test_user.likes.append(m2)
        db.session.commit()

        liked_stuff = Likes.query.filter(Likes.user_id == test_user.id).all()
        self.assertEqual(len(liked_stuff),2)
        self.assertEqual(liked_stuff[1].message_id, m2.id)
    
    
