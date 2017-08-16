from nose.tools import *
import bin.app as app
import tests.tools as tools


def test_index():

    # check that we get a 404 on the /url

    resp= app.app.request("/")
    tools.assert_response(resp, status="404")


    resp= app.app.request("/hello")
    tools.assert_response(resp)

    resp= app.app.request("/hello", method="POST")
    tools.assert_response(resp, contains="Nobody")

    data = {'name': 'Zed', 'greet':'Hola'}
    resp=app.app.request("/hello", method="POST", data=data)
    tools.assert_response(resp,contains="Zed")