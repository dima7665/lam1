from flask import Flask, url_for
from .tools import info

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'fjdhsguihorhgpwgh geigh weioghweg og'

    from .work import work
    from .remain import remain
    from .monfin import monfin
    from .support import support

    app.register_blueprint(work, url_prefix='/')
    app.register_blueprint(remain, url_prefix='/')
    app.register_blueprint(monfin, url_prefix='/')
    app.register_blueprint(support, url_prefix='/')

    return app