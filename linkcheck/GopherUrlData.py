from UrlData import UrlData

class GopherUrlData(UrlData):
    "Url link with gopher scheme"

    def __str__(self):
        return "Gopher link\n"+UrlData.__str__(self)
    
    
