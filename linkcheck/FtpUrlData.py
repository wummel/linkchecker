import ftplib
from UrlData import UrlData

class FtpUrlData(UrlData):
    """
    Url link with ftp scheme. 
    """
    
    def checkConnection(self, config):
        _user, _password = self._getUserPassword(config)
        self.urlConnection = ftplib.FTP(self.urlTuple[1], _user, _password)
        info = self.urlConnection.getwelcome()
        if not info:
            self.closeConnection()
            raise Exception, "Got no answer from FTP server"
        self.setInfo(info)
       
    def closeConnection(self):
        try: self.urlConnection.quit()
        except: pass
        self.urlConnection = None
       
    def __str__(self):
        return "FTP link\n"+UrlData.__str__(self)

    
