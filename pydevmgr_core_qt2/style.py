from enum import Enum 

class _S(str):
    def __init__(self, s, style=""):
        super().__init__(s)
        self.style = style
        
class Style(str, Enum):
    """ A collection of style IDs derived from GROUPs in pydevmgr + extra stuff """
    IDL       = "IDL"
    WARNING   = "WARNING"
    ERROR     = "ERROR"
    OK        = "OK"
    NOK       = "NOK"
    BUZY      = "BUZY"
    UNKNOWN   = "UNKNOWN"
    NORMAL    = "NORMAL"
    ODD       = "ODD"
    EVEN      = "EVEN"
    ERROR_TXT = "ERROR_TXT"
    OK_TXT    = "OK_TXT"
    DIFFERENT = "DIFFERENT"
    SIMILAR   = "SMILAR"
    GOOD_VALUE = "GOOD_VALUE"
    BAD_VALUE = "BAD_VALUE"
    
""" Associate STYLE IDs to qt stylSheet """
Style.NORMAL.style = "background-color: white;"
Style.IDL.style = "background-color: white;"
Style.WARNING.style = "background-color: #ff9966;"
Style.ERROR.style = "background-color: #cc3300;"
Style.OK.style = "background-color: #99cc33;"
Style.NOK.style = "background-color: #ff9966;"
Style.BUZY.style = "background-color: #ffcc00;"
Style.UNKNOWN.style = ""
Style.ODD.style = "background-color: #E0E0E0;"
Style.EVEN.style = "background-color: #F8F8F8;"
Style.ERROR_TXT.style = "color: #cc3300;"
Style.OK_TXT.style = "color: black;"
Style.DIFFERENT.style = "color: #cc3300;"
Style.SIMILAR.style = "color: black;"
Style.GOOD_VALUE.style = "border-color: black;"
Style.BAD_VALUE.style = "border: 1px solid #cc3300;"

def get_style(style):
    """ return the style of a given style name """
    if not style: return ""
    return getattr( Style(style), "style", "")


if __name__ == "__main__":
    assert get_style("BAD_VALUE") == "border-color: #cc3300;"
    assert get_style(Style.BAD_VALUE) == "border-color: #cc3300;"

