class RpycConnector(object):
    __c = None
    @staticmethod 
    def get_c():
        """ This connects to rpyc server started in ctxctl python console.
        If connection is already existing, return the current hook
        """
        if (RpycConnector.__c == None):
            
            print('Rpyc : Creating connection to host')
            RpycConnector.__c = rpyc.classic.connect("localhost", 1300)   
            print('Rpyc : ..done!')
            
            RPYC_TIMEOUT = 600 #defines a higher timeout
            print('Rpyc : Setting rpyc timeout to', RPYC_TIMEOUT , ' sec')
            RpycConnector.__c._config["sync_request_timeout"] = RPYC_TIMEOUT  # Set timeout to higher level
            
            return RpycConnector.__c
        else:
            print('Rpyc : Connection already existing')
            return RpycConnector.__c
