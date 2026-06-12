"""Las 48 selecciones del Mundial 2026, su grupo, ELO y ranking FIFA.

Fuentes (junio 2026):
  - Sorteo oficial (5 dic 2025, Washington D.C.) — verificado con Wikipedia + ESPN.
  - ELO: World Football Elo Ratings (eloratings.net vía Wikipedia, 10 jun 2026).
  - Ranking FIFA: actualización 11 jun 2026 (Sofascore/Wikipedia).

`elo` es el input principal de fuerza. `fifa_rank` es informativo.
"""

# (nombre, código, ELO, ranking FIFA, confederación)
TEAM_DATA = {
    # Grupo A
    "Mexico":       {"code": "MEX", "elo": 1875, "fifa_rank": 14, "confederation": "CONCACAF"},
    "South Africa": {"code": "RSA", "elo": 1517, "fifa_rank": 60, "confederation": "CAF"},
    "South Korea":  {"code": "KOR", "elo": 1758, "fifa_rank": 25, "confederation": "AFC"},
    "Czechia":      {"code": "CZE", "elo": 1740, "fifa_rank": 40, "confederation": "UEFA"},
    # Grupo B
    "Canada":       {"code": "CAN", "elo": 1788, "fifa_rank": 30, "confederation": "CONCACAF"},
    "Switzerland":  {"code": "SUI", "elo": 1891, "fifa_rank": 19, "confederation": "UEFA"},
    "Qatar":        {"code": "QAT", "elo": 1421, "fifa_rank": 55, "confederation": "AFC"},
    "Bosnia & Herzegovina": {"code": "BIH", "elo": 1595, "fifa_rank": 64, "confederation": "UEFA"},
    # Grupo C
    "Brazil":       {"code": "BRA", "elo": 1991, "fifa_rank": 6, "confederation": "CONMEBOL"},
    "Morocco":      {"code": "MAR", "elo": 1827, "fifa_rank": 7, "confederation": "CAF"},
    "Haiti":        {"code": "HAI", "elo": 1548, "fifa_rank": 83, "confederation": "CONCACAF"},
    "Scotland":     {"code": "SCO", "elo": 1782, "fifa_rank": 42, "confederation": "UEFA"},
    # Grupo D
    "United States": {"code": "USA", "elo": 1726, "fifa_rank": 17, "confederation": "CONCACAF"},
    "Paraguay":     {"code": "PAR", "elo": 1834, "fifa_rank": 41, "confederation": "CONMEBOL"},
    "Australia":    {"code": "AUS", "elo": 1777, "fifa_rank": 27, "confederation": "AFC"},
    "Türkiye":      {"code": "TUR", "elo": 1911, "fifa_rank": 22, "confederation": "UEFA"},
    # Grupo E
    "Germany":      {"code": "GER", "elo": 1932, "fifa_rank": 10, "confederation": "UEFA"},
    "Curaçao":      {"code": "CUW", "elo": 1434, "fifa_rank": 82, "confederation": "CONCACAF"},
    "Ivory Coast":  {"code": "CIV", "elo": 1695, "fifa_rank": 33, "confederation": "CAF"},
    "Ecuador":      {"code": "ECU", "elo": 1938, "fifa_rank": 23, "confederation": "CONMEBOL"},
    # Grupo F
    "Netherlands":  {"code": "NED", "elo": 1948, "fifa_rank": 8, "confederation": "UEFA"},
    "Japan":        {"code": "JPN", "elo": 1906, "fifa_rank": 18, "confederation": "AFC"},
    "Tunisia":      {"code": "TUN", "elo": 1628, "fifa_rank": 49, "confederation": "CAF"},
    "Sweden":       {"code": "SWE", "elo": 1712, "fifa_rank": 43, "confederation": "UEFA"},
    # Grupo G
    "Belgium":      {"code": "BEL", "elo": 1894, "fifa_rank": 9, "confederation": "UEFA"},
    "Egypt":        {"code": "EGY", "elo": 1696, "fifa_rank": 29, "confederation": "CAF"},
    "Iran":         {"code": "IRN", "elo": 1772, "fifa_rank": 20, "confederation": "AFC"},
    "New Zealand":  {"code": "NZL", "elo": 1562, "fifa_rank": 85, "confederation": "OFC"},
    # Grupo H
    "Spain":        {"code": "ESP", "elo": 2157, "fifa_rank": 2, "confederation": "UEFA"},
    "Cape Verde":   {"code": "CPV", "elo": 1578, "fifa_rank": 67, "confederation": "CAF"},
    "Saudi Arabia": {"code": "KSA", "elo": 1576, "fifa_rank": 61, "confederation": "AFC"},
    "Uruguay":      {"code": "URU", "elo": 1892, "fifa_rank": 16, "confederation": "CONMEBOL"},
    # Grupo I
    "France":       {"code": "FRA", "elo": 2063, "fifa_rank": 3, "confederation": "UEFA"},
    "Senegal":      {"code": "SEN", "elo": 1860, "fifa_rank": 15, "confederation": "CAF"},
    "Norway":       {"code": "NOR", "elo": 1914, "fifa_rank": 31, "confederation": "UEFA"},
    "Iraq":         {"code": "IRQ", "elo": 1607, "fifa_rank": 57, "confederation": "AFC"},
    # Grupo J
    "Argentina":    {"code": "ARG", "elo": 2115, "fifa_rank": 1, "confederation": "CONMEBOL"},
    "Algeria":      {"code": "ALG", "elo": 1772, "fifa_rank": 28, "confederation": "CAF"},
    "Austria":      {"code": "AUT", "elo": 1830, "fifa_rank": 24, "confederation": "UEFA"},
    "Jordan":       {"code": "JOR", "elo": 1680, "fifa_rank": 63, "confederation": "AFC"},
    # Grupo K
    "Portugal":     {"code": "POR", "elo": 1989, "fifa_rank": 5, "confederation": "UEFA"},
    "Uzbekistan":   {"code": "UZB", "elo": 1714, "fifa_rank": 50, "confederation": "AFC"},
    "Colombia":     {"code": "COL", "elo": 1982, "fifa_rank": 13, "confederation": "CONMEBOL"},
    "DR Congo":     {"code": "COD", "elo": 1652, "fifa_rank": 46, "confederation": "CAF"},
    # Grupo L
    "England":      {"code": "ENG", "elo": 2024, "fifa_rank": 4, "confederation": "UEFA"},
    "Croatia":      {"code": "CRO", "elo": 1912, "fifa_rank": 11, "confederation": "UEFA"},
    "Ghana":        {"code": "GHA", "elo": 1510, "fifa_rank": 73, "confederation": "CAF"},
    "Panama":       {"code": "PAN", "elo": 1730, "fifa_rank": 34, "confederation": "CONCACAF"},
}

# Sorteo oficial: 12 grupos de 4.
GROUP_DRAW = {
    "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "B": ["Canada", "Switzerland", "Qatar", "Bosnia & Herzegovina"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Türkiye"],
    "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Tunisia", "Sweden"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Norway", "Iraq"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "Uzbekistan", "Colombia", "DR Congo"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

# Selecciones anfitrionas (juegan de local en sus partidos de grupo).
HOSTS = {"Mexico", "Canada", "United States"}
