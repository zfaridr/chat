import unittest
import client


class TestClient(unittest.TestCase):
    def testpresenceaction(self):
        self.assertEqual(client.main(1)['action'], 'presence')

    def testjoin(self):
        self.assertEqual(client.main(2), 'You are in the chat')

    def testchatmessage(self):
        self.assertAlmostEqual(client.main(3), 'Your message was recieved in the chat')

    def testchatquit(self):
        self.assertEqual(client.main(4), 'Client leaved the chat')

        

   
if __name__ == '__main__':
    unittest.main()