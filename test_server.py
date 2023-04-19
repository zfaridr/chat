import unittest
from socket import *
import time
import server
s = socket(AF_INET, SOCK_STREAM)
s.bind(('', 8886))
s.listen(10)


class TestServer(unittest.TestCase):
    def testpresence(self):
        client, addr = s.accept()
        
        self.assertEqual(server.process_message(), 'You are online')

    def testjoin(self):
        client, addr = s.accept()
        

        self.assertEqual(server.process_message(), 'You are in the chat')

    def testchatmessage(self):
        client, addr = s.accept()
          
        self.assertAlmostEqual(server.process_message(), 'Your message was recieved in the chat')

    def testchatquit(self):
        client, addr = s.accept()
        self.assertEqual(server.process_message(), 'Client leaved the chat')

        

   
if __name__ == '__main__':
    unittest.main()