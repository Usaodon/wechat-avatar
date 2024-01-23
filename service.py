import service.views as views
from gevent import pywsgi


if __name__ == '__main__':
    service = pywsgi.WSGIServer(('0.0.0.0', 8081), views.app)
    service.serve_forever()
