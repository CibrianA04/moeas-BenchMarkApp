# -*- coding: utf-8 -*-
"""
Capa de DATOS: entrada/salida y persistencia.

Regla dura: NADA aqui importa Streamlit. Tampoco 'domain', SALVO 'domain.model'
(las dataclasses PFA/ConfigCSV son la unica forma compartida que viaja entre
capas). Solo lee/escribe datos (archivos .pof de PFA, referencias, SQLite).
"""
