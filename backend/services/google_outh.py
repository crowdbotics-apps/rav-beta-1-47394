"""
import requests

"""

import requests
from django.conf import settings


def exchange_code_for_tokens(code):
    """
    The function `exchange_code_for_tokens` exchanges an authorization code for access tokens using
    Google OAuth2.

    :param code: The `code` parameter in the `exchange_code_for_tokens` function is typically the
    authorization code that is received from the OAuth2 authorization flow. This code is exchanged for
    an access token and possibly a refresh token, depending on the OAuth2 implementation. The
    authorization code is a temporary code that the client
    :return: The function `exchange_code_for_tokens` is returning the JSON response from the POST
    request made to the token endpoint after exchanging the provided authorization code for tokens.
    """

    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    redirect_uri = settings.GOOGLE_REDIRECT_URI

    token_endpoint = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(token_endpoint, data=payload, headers=headers)
    return response.json()


def get_user_info_from_google(access_token):
    """
    The function `get_user_info_from_google` retrieves user information from Google using an access
    token.

    :param access_token: The `access_token` parameter is a credential that represents the authorization
    granted to the application by the user. It allows the application to access the user's information
    on Google's API on behalf of the user
    :return: The function `get_user_info_from_google` makes a GET request to the Google OAuth2 user info
    endpoint with the provided access token and returns the JSON response containing the user
    information.
    """
    user_info_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
    params = {
        "access_token": access_token,
    }

    response = requests.get(user_info_endpoint, params=params)
    return response.json()
