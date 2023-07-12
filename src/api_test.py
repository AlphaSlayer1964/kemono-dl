import unittest
import requests
from numbers import Number
from requests.adapters import HTTPAdapter, Retry

class ApiTest(unittest.TestCase):
    site = ''
    timeout = 5
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'}
    def getSession(self):
        retries = Retry(
            total = 3,
            backoff_factor = 0.1,
            status_forcelist = [ 500, 502, 503, 504 ]
        )
        session = requests.Session()
        session.mount('https://', HTTPAdapter(max_retries=retries))
        session.mount('http://', HTTPAdapter(max_retries=retries))
        return session
    def callApi(self, url):
        print(f'Requst {url}')
        response = self.getSession().get(url=url, headers=self.headers, timeout=self.timeout)
        if response.status_code == 401:
            raise Exception(f'HTTP 401 bad cookie | {response.status_code} {response.reason}')
        elif not response.ok:
            raise Exception(f'HTTP not ok, | {response.status_code} {response.reason}')
        print(f'Response {response.text}')
        return response.json()

class KemonoApiTest(ApiTest, unittest.TestCase):
    site = 'kemono.party'
    patreonUser = '35150295'
    patreonPost = '65210116'

    def test_creators(self):
        print('Start test for creators')
        creators = self.callApi(url=f'https://{self.site}/api/creators/')
        self.assertGreaterEqual(len(creators), 1, 'creator can not be empty')
        creator = creators[0]
        self.assertTrue(isinstance(creator['favorited'], Number), 'favorited must be number')
        self.assertTrue(isinstance(creator['indexed'], Number), 'indexed must be number')
        self.assertTrue(isinstance(creator['updated'], Number), 'updated must be number')
        self.assertTrue(isinstance(creator['id'], str), 'favorited must be str')
        self.assertTrue(isinstance(creator['name'], str), 'favorited must be str')
        self.assertTrue(isinstance(creator['service'], str), 'favorited must be str')

    def test_patreon_post(self):
        print('Start test for Patreon post api')
        post = self.callApi(url=f"https://{self.site}/api/patreon/user/{self.patreonUser}/post/{self.patreonPost}")
        self.assertEqual(len(post), 1, 'Post list must equal to 1')
        post = post[0]
        self.assertEqual(post['added'], 'Thu, 28 Apr 2022 03:16:21 GMT', 'added not equal')
        self.assertEqual(post['attachments'], [{'name': 'Nelves_Moonwell_Final.jpg', 
                        'path': '/59/ca/59ca91127d30cd44c85a8fd71a7a560b74c4eb7e0a2873065057fe20f7e3c5b8.jpg'}],
                        'attachment not equal')
        self.assertEqual(post['content'], "<p>Made a quick render of night elves \"bathing\" \
in a moonwell while waiting for simulations on the Miss Fortune animation. I'm in the polishing stage of the Miss \
Fortune animation and will be hiring a VA soon as well as beginning the render!</p><p>Hope you all enjoy this scene :)</p>", 
        'content not equal')
        self.assertEqual(post['edited'], 'Sat, 16 Apr 2022 14:03:04 GMT', 'edited not equal')
        self.assertEqual(post['embed'], {}, 'embed not equal')
        self.assertEqual(post['file'], {'name': 'Nelves_Moonwell_Final.jpg', 
                        'path': '/59/ca/59ca91127d30cd44c85a8fd71a7a560b74c4eb7e0a2873065057fe20f7e3c5b8.jpg'},
                        'file not equal')
        self.assertEqual(post['id'], '65210116', 'post id not equal')
        self.assertEqual(post['published'], 'Sat, 16 Apr 2022 14:03:04 GMT', 'published not equal')
        self.assertEqual(post['title'], 'Moonwell Bathing and Miss Fortune Update', 'title not equal')
        self.assertEqual(post['user'], self.patreonUser, 'user must be same')
        self.assertEqual(post['service'], 'patreon', 'service must be patreon')
        self.assertFalse(post['shared_file'], 'shared file must be false in this post')


class CoomerApiTest(ApiTest, unittest.TestCase):
    site = 'coomer.party'
    

if __name__ == '__main__':
    unittest.main()