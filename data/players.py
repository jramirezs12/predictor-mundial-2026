"""Jugadores clave por selección (datos 2025/26, plantillas actuales).

`goal_share` = fracción aproximada de los goles del equipo que suele aportar el
jugador. No tiene que sumar 1 (el resto se reparte entre el plantel y autogoles).
Se usa para proyectar P(jugador marca) en cada partido.

Solo se cargan los principales contendientes con plantillas verificadas en la
investigación; las selecciones sin jugadores aquí simplemente no muestran
proyección individual (el modelo de goles del equipo sigue funcionando igual).
"""

KEY_PLAYERS = {
    "Argentina": [
        {"name": "Lionel Messi", "position": "Delantero", "club": "Inter Miami", "goal_share": 0.26},
        {"name": "Julián Álvarez", "position": "Delantero", "club": "Atlético Madrid", "goal_share": 0.22},
        {"name": "Lautaro Martínez", "position": "Delantero", "club": "Inter", "goal_share": 0.20},
    ],
    "France": [
        {"name": "Kylian Mbappé", "position": "Delantero", "club": "Real Madrid", "goal_share": 0.32},
        {"name": "Ousmane Dembélé", "position": "Extremo", "club": "Paris Saint-Germain", "goal_share": 0.20},
        {"name": "Bradley Barcola", "position": "Extremo", "club": "Paris Saint-Germain", "goal_share": 0.12},
    ],
    "Spain": [
        {"name": "Lamine Yamal", "position": "Extremo derecho", "club": "Barcelona", "goal_share": 0.22},
        {"name": "Mikel Oyarzabal", "position": "Delantero", "club": "Real Sociedad", "goal_share": 0.18},
        {"name": "Pedri", "position": "Centrocampista", "club": "Barcelona", "goal_share": 0.12},
    ],
    "England": [
        {"name": "Harry Kane", "position": "Delantero", "club": "Bayern Munich", "goal_share": 0.30},
        {"name": "Jude Bellingham", "position": "Mediapunta", "club": "Real Madrid", "goal_share": 0.20},
        {"name": "Bukayo Saka", "position": "Extremo", "club": "Arsenal", "goal_share": 0.15},
    ],
    "Brazil": [
        {"name": "Vinícius Júnior", "position": "Extremo", "club": "Real Madrid", "goal_share": 0.25},
        {"name": "Raphinha", "position": "Extremo izquierdo", "club": "Barcelona", "goal_share": 0.20},
        {"name": "Rodrygo", "position": "Extremo", "club": "Real Madrid", "goal_share": 0.15},
    ],
    "Portugal": [
        {"name": "Cristiano Ronaldo", "position": "Delantero", "club": "Al-Nassr", "goal_share": 0.26},
        {"name": "Bruno Fernandes", "position": "Mediapunta", "club": "Manchester United", "goal_share": 0.18},
        {"name": "Rafael Leão", "position": "Extremo", "club": "AC Milan", "goal_share": 0.15},
    ],
    "Germany": [
        {"name": "Florian Wirtz", "position": "Mediapunta", "club": "Liverpool", "goal_share": 0.20},
        {"name": "Jamal Musiala", "position": "Mediapunta", "club": "Bayern Munich", "goal_share": 0.20},
        {"name": "Kai Havertz", "position": "Delantero", "club": "Arsenal", "goal_share": 0.16},
    ],
    "Netherlands": [
        {"name": "Cody Gakpo", "position": "Extremo", "club": "Liverpool", "goal_share": 0.22},
        {"name": "Memphis Depay", "position": "Delantero", "club": "Corinthians", "goal_share": 0.20},
        {"name": "Virgil van Dijk", "position": "Defensa central", "club": "Liverpool", "goal_share": 0.06},
    ],
    "Belgium": [
        {"name": "Romelu Lukaku", "position": "Delantero", "club": "Napoli", "goal_share": 0.26},
        {"name": "Jérémy Doku", "position": "Extremo", "club": "Manchester City", "goal_share": 0.18},
        {"name": "Kevin De Bruyne", "position": "Mediapunta", "club": "Napoli", "goal_share": 0.15},
    ],
    "Croatia": [
        {"name": "Luka Modrić", "position": "Centrocampista", "club": "AC Milan", "goal_share": 0.12},
        {"name": "Andrej Kramarić", "position": "Delantero", "club": "Hoffenheim", "goal_share": 0.20},
        {"name": "Ante Budimir", "position": "Delantero", "club": "Osasuna", "goal_share": 0.18},
    ],
    "Uruguay": [
        {"name": "Darwin Núñez", "position": "Delantero", "club": "Al-Hilal", "goal_share": 0.24},
        {"name": "Federico Valverde", "position": "Centrocampista", "club": "Real Madrid", "goal_share": 0.16},
        {"name": "Facundo Pellistri", "position": "Extremo", "club": "Panathinaikos", "goal_share": 0.10},
    ],
    "Colombia": [
        {"name": "Luis Díaz", "position": "Extremo", "club": "Bayern Munich", "goal_share": 0.25},
        {"name": "James Rodríguez", "position": "Mediapunta", "club": "Club León", "goal_share": 0.18},
        {"name": "Jhon Córdoba", "position": "Delantero", "club": "Krasnodar", "goal_share": 0.15},
    ],
    "Morocco": [
        {"name": "Youssef En-Nesyri", "position": "Delantero", "club": "Fenerbahçe", "goal_share": 0.24},
        {"name": "Achraf Hakimi", "position": "Lateral derecho", "club": "Paris Saint-Germain", "goal_share": 0.12},
        {"name": "Brahim Díaz", "position": "Mediapunta", "club": "Real Madrid", "goal_share": 0.14},
    ],
    "Norway": [
        {"name": "Erling Haaland", "position": "Delantero", "club": "Manchester City", "goal_share": 0.40},
        {"name": "Alexander Sørloth", "position": "Delantero", "club": "Atlético Madrid", "goal_share": 0.18},
        {"name": "Martin Ødegaard", "position": "Mediapunta", "club": "Arsenal", "goal_share": 0.14},
    ],
    "United States": [
        {"name": "Christian Pulisic", "position": "Extremo", "club": "AC Milan", "goal_share": 0.26},
        {"name": "Folarin Balogun", "position": "Delantero", "club": "Mónaco", "goal_share": 0.18},
        {"name": "Weston McKennie", "position": "Centrocampista", "club": "Juventus", "goal_share": 0.12},
    ],
    "Switzerland": [
        {"name": "Breel Embolo", "position": "Delantero", "club": "Mónaco", "goal_share": 0.22},
        {"name": "Dan Ndoye", "position": "Extremo", "club": "Nottingham Forest", "goal_share": 0.16},
        {"name": "Granit Xhaka", "position": "Centrocampista", "club": "Bayer Leverkusen", "goal_share": 0.10},
    ],
    "Japan": [
        {"name": "Kaoru Mitoma", "position": "Extremo", "club": "Brighton", "goal_share": 0.20},
        {"name": "Takefusa Kubo", "position": "Extremo", "club": "Real Sociedad", "goal_share": 0.16},
        {"name": "Ayase Ueda", "position": "Delantero", "club": "Feyenoord", "goal_share": 0.18},
    ],
    "Mexico": [
        {"name": "Raúl Jiménez", "position": "Delantero", "club": "Fulham", "goal_share": 0.22},
        {"name": "Santiago Giménez", "position": "Delantero", "club": "AC Milan", "goal_share": 0.20},
        {"name": "Hirving Lozano", "position": "Extremo", "club": "San Diego FC", "goal_share": 0.14},
    ],
    "Senegal": [
        {"name": "Nicolas Jackson", "position": "Delantero", "club": "Bayern Munich", "goal_share": 0.22},
        {"name": "Sadio Mané", "position": "Extremo", "club": "Al-Nassr", "goal_share": 0.20},
        {"name": "Ismaïla Sarr", "position": "Extremo", "club": "Crystal Palace", "goal_share": 0.15},
    ],
    "Ecuador": [
        {"name": "Enner Valencia", "position": "Delantero", "club": "Internacional", "goal_share": 0.24},
        {"name": "Moisés Caicedo", "position": "Centrocampista", "club": "Chelsea", "goal_share": 0.10},
        {"name": "Kendry Páez", "position": "Mediapunta", "club": "Chelsea", "goal_share": 0.14},
    ],
}
