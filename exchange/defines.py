NBRB_URL = 'http://www.nbrb.by/Services/XmlExRates.aspx'
IDEABANK_URL = 'https://www.ideabank.by/o-banke/kursy-valyut/'

MTBANK_IDENTIFIER = 'http://select.by/content/view/410/339/'
IDEABANK_IDENTIFIER = 'http://select.by/content/view/532/411/'

MTBANK_COMMON_OFFICE = '1001'
MTBANK_68_OFFICE = '1068'

IDEABANK_ONLINE_OFFICE = '1101'


MTBANK_COMMON_BODY = r'a:4:{s:6:"source";s:35:"O:9:"front_api":1:{s:6:"result";N;}";s:9:"' \
                      r'className";s:9:"front_api";s:6:"method";s:6:"xroute";s:9:"arguments";s:183:"a:2:' \
                      r'{i:0;a:1:{s:7:"catalog";a:1:{s:9:"get_rates";a:6:{s:5:"depId";s:11:"301,302,303";s:7:"dateNow";' \
                      r'N;s:11:"doNotUseTxt";b:1;s:3:"brs";b:1;s:2:"or";b:1;s:10:"simpleForm";b:1;}}}i:1;N;}";}'

MTBANK_68_BODY = r'a:4:{s:6:"source";s:35:"O:9:"front_api":1:{s:6:"result";N;}";s:9:"' \
                      r'className";s:9:"front_api";s:6:"method";s:6:"xroute";s:9:"arguments";s:187:"a:2:' \
                      r'{i:0;a:1:{s:7:"catalog";a:1:{s:9:"get_rates";a:6:{s:5:"depId";s:15:"168,768,968,868";s:7:"dateNow";' \
                      r'N;s:11:"doNotUseTxt";b:1;s:3:"brs";b:1;s:2:"or";b:1;s:10:"simpleForm";b:1;}}}i:1;N;}";}'

MTBANK_RATES_START_LINE = '"rates":'

IDEA_REMOTE_DATE_FORMAT = '%d-%m-%Y'
DEFAULT_DATE_FORMAT = '%d.%m.%Y'

SELECTBY_EXCHANGE_OFFICE_PAGE_PATTERN = 'https://select.by/kurs/karta/id%s'
