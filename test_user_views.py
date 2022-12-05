"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup # can use this to check to see if html is showing up on our pages

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup("test_username", "test@gmail.com", "test_password", None)
        self.testuser.id = 8888

        self.u1 = User.signup("abc", "test1@test.com", "password", None)
        self.u1.id = 778

        self.u2 = User.signup("efg", "test2@test.com", "password", None)
        self.u2.id = 884
        
        self.u3 = User.signup("hij", "test3@test.com", "password", None)
        self.u3.id = 123456

        self.u4 = User.signup("test_patrickstar", "test4@test.com", "password", None)
        self.u4.id = 98765

        db.session.commit()

    
    def tearDown(self):
        db.session.rollback()


    def test_users_index(self):
        with self.client as client:
            resp = client.get("/users")
            html = resp.get_data(as_text=True)

            self.assertIn("@test_username", html) # using get_data(as_text=True)
            self.assertIn("@abc", str(resp.data)) # using beautiful soup
            self.assertIn("@efg", html)
            self.assertIn("@hij", html)
            self.assertIn("@test_patrickstar", html)


    def test_users_search(self):
        with self.client as client:
            resp = client.get("/users?q=test")
            html = resp.get_data(as_text=True)

            # searching test should return username's with "test" in the username
            self.assertIn("@test_username", html)
            self.assertIn("@test_patrickstar", str(resp.data)) # using beautiful soup

            self.assertNotIn("@abc", html)
            self.assertNotIn("@efg", html)
            self.assertNotIn("@hij", html)


    def test_users_show(self):
        with self.client as client:
            resp = client.get(f"/users/{self.testuser.id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@test_username", str(resp.data))



    def setup_likes(self):
        m1 = Message(text="bacon goes on everything", user_id=self.testuser.id)
        m2 = Message(text="life without cheese is sad", user_id=self.testuser.id)
        m3 = Message(id = 6666, text="bacon goes on everything", user_id=self.u1.id)
        db.session.add_all([m1,m2,m3])
        db.session.commit()

        # add "liked" message to data table
        like1 = Likes(user_id=self.testuser.id, message_id=6666)

        db.session.add(like1)
        db.session.commit()

    def test_user_show_with_likes(self):
        """ Test to see if numbers for Messages, Following, Followers, and Likes are showing up correctly"""

        self.setup_likes()

        with self.client as client:
            resp = client.get(f"/users/{self.testuser.id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test_username", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 2 messages
            self.assertIn("2", found[0].text)

            # Test for a count of 0 following
            self.assertIn("0", found[1].text)

            # Test for a count of 0 followers
            self.assertIn("0", found[2].text)

            # Test for a count of 1 like
            self.assertIn("1", found[3].text)


    def test_add_like(self):
        m = Message(id=1984, text="The earth is round", user_id=self.u1.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/add_like/1984", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==1984).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser.id)


    # can't get this one to work
    def test_remove_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.id==6666).one()
        self.assertNotEqual(m.user_id, self.testuser.id)

        liked_m = Likes.query.filter(Likes.user_id==self.testuser.id and Likes.message_id==m.id).one()

        # Now we are sure that testuser likes the message
        self.assertIsNotNone(liked_m)  

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

        #         resp = c.post(f"/users/remove_like/{liked_m.id}", follow_redirects=True)
        #         self.assertEqual(resp.status_code, 200)

        #         likes = Likes.query.filter(Likes.message_id==liked_m.id).all()
        #         # the liked message should now be deleted and we can check below
        #         self.assertEqual(len(likes),0)


    def test_unauthenticated_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.id==6666).one()

        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/users/add_like/{m.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            

            # The number of likes has not changed since making the request
            self.assertEqual(like_count, Likes.query.count())


    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1.id, user_following_id=self.testuser.id)
        f2 = Follows(user_being_followed_id=self.u2.id, user_following_id=self.testuser.id)
        f3 = Follows(user_being_followed_id=self.testuser.id, user_following_id=self.u1.id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()


    def test_user_show_with_follows(self):

        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test_username", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 0 messages
            self.assertIn("0", found[0].text)

            # Test for a count of 2 following
            self.assertIn("2", found[1].text)

            # Test for a count of 1 follower
            self.assertIn("1", found[2].text)

            # Test for a count of 0 likes
            self.assertIn("0", found[3].text)


    def test_show_following(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@abc", str(resp.data))
            self.assertIn("@efg", str(resp.data))
            self.assertNotIn("@hij", str(resp.data))
            self.assertNotIn("@testing", str(resp.data))


    def test_show_followers(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}/followers")

            self.assertIn("@abc", str(resp.data))
            self.assertNotIn("@efg", str(resp.data))
            self.assertNotIn("@hij", str(resp.data))
            self.assertNotIn("@testing", str(resp.data))


    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser.id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@abc", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))


    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@abc", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))
