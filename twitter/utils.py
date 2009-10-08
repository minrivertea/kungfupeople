import oauth
import httplib
from django.conf import settings

CONSUMER = oauth.OAuthConsumer(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
CONNECTION = httplib.HTTPSConnection(settings.OAUTH_SERVER)
SIGNATURE_METHOD = oauth.OAuthSignatureMethod_HMAC_SHA1()

# No rate limit for the following 3 URLs
REQUEST_TOKEN_URL = 'https://%s/oauth/request_token' % settings.OAUTH_SERVER
ACCESS_TOKEN_URL = 'https://%s/oauth/access_token' % settings.OAUTH_SERVER
AUTHORIZATION_URL = 'http://%s/oauth/authorize' % settings.OAUTH_SERVER

# /!\ Rate limit: 15 requests/hour /!\
TWITTER_CHECK_AUTH = 'https://twitter.com/account/verify_credentials.json'


def is_authenticated(access_token, consumer=CONSUMER, connection=CONNECTION):
    oauth_request = request_oauth_resource(TWITTER_CHECK_AUTH, access_token)
    json = fetch_response(oauth_request, connection=connection)
    if 'screen_name' in json:
        return json
    return False

def request_oauth_resource(url, access_token, parameters=None,
        consumer=CONSUMER, signature_method=SIGNATURE_METHOD,
        http_method='GET'):
    """
    Returns a OAuthRequest object
    """
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
            token=access_token, http_method=http_method, http_url=url,
            parameters=parameters)
    oauth_request.sign_request(signature_method, consumer, access_token)
    return oauth_request

def fetch_response(oauth_request, connection=CONNECTION):
    url = oauth_request.to_url()
    connection.request(oauth_request.http_method, url)
    response = connection.getresponse()
    s = response.read()
    return s

def get_unauthorised_request_token(consumer, connection, signature_method=SIGNATURE_METHOD):
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, http_url=REQUEST_TOKEN_URL)
    oauth_request.sign_request(signature_method, consumer, None)
    resp = fetch_response(oauth_request)
    token = oauth.OAuthToken.from_string(resp)
    return token

def get_authorisation_url(consumer, token, signature_method=SIGNATURE_METHOD):
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=token, http_url=AUTHORIZATION_URL)
    oauth_request.sign_request(signature_method, consumer, token)
    return oauth_request.to_url()

def exchange_request_token_for_access_token(consumer, connection,
        request_token, signature_method=SIGNATURE_METHOD):
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=request_token, http_url=ACCESS_TOKEN_URL)
    oauth_request.sign_request(signature_method, consumer, request_token)
    resp = fetch_response(oauth_request, connection)
    return oauth.OAuthToken.from_string(resp)
