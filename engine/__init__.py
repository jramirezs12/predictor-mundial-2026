"""Motor de predicción del Mundial 2026.

Combina cuatro enfoques descritos en la investigación del proyecto:
  - ELO Rating      -> fuerza relativa de cada selección
  - Poisson         -> distribución de goles
  - Dixon-Coles     -> corrección de marcadores bajos (0-0, 1-0, 1-1)
  - Monte Carlo     -> simulación del torneo completo
"""
