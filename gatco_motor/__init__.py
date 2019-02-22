from motor.motor_asyncio import AsyncIOMotorClient

__version__ = '0.1.0'

class _MotorState(object):
    """Remembers configuration for the (db, app) tuple."""

    def __init__(self, db):
        self.db = db
        self.connectors = {}

class Motor(object):
    app = None
    client = None
    db = None
    
    def __init__(self, app=None):
        self.open_connection = None
        self.close_connection = None
        if app is not None:
            self.init_app(app)
            
    def user_open_connection(self, open_connection):
        """Decorator to set a custom user open_connection"""
        self.open_connection = open_connection
        return open_connection
    
    def user_close_connection(self, close_connection):
        """Decorator to set a custom user open_connection"""
        self.close_connection = close_connection
        return close_connection
    
    def init_app(self, app, open_listener='before_server_start',
                 close_listener='before_server_stop', name=None, uri=None):
        app.config['MOTOR_URI'] = app.config.get('MOTOR_URI', 'mongodb://localhost:27017/motorapp')
        self.app = app
        
        if open_listener:
            @app.listener(open_listener)
            async def open_connection(app, loop):
                self.default_open_connection(app, loop, name, uri)
                if self.open_connection is not None:
                    await self.open_connection(app, loop, name, uri)

        if close_listener:
            @app.listener(close_listener)
            async def close_connection(app, loop):
                self.default_close_connection(app, loop)
                if self.close_connection is not None:
                    await self.close_connection(app, loop)
        
        
        if (not hasattr(app, 'extensions')) or (app.extensions is None):
            app.extensions = {}
        app.extensions['motor'] = _MotorState(self)
        
    def get_app(self, reference_app=None):
        """Helper method that implements the logic to look up an
        application."""

        if reference_app is not None:
            return reference_app

        if self.app is not None:
            return self.app

        raise RuntimeError(
            'No application found. Either work inside a view function or push'
            ' an application context.'
        )
        
    def default_open_connection(self, app, loop, name=None, uri=None):
        if not name:
            name = app.name
        #logger.info('opening motor connection for [{}]'.format(name))
        self.client = AsyncIOMotorClient(uri or app.config.MOTOR_URI, io_loop=loop)
        self.db = self.client.get_database()
        
        
    def default_close_connection(self, app, loop):
        if self.client is not None:
            self.client.close()
    