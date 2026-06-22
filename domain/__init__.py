# -*- coding: utf-8 -*-
"""
Capa de DOMINIO (logica).

Regla dura: NADA en este paquete importa Streamlit. Recibe datos, devuelve datos
(numeros, DataFrames, objetos Figure de matplotlib construidos headless) y, si lo
necesita, se apoya en la capa de DATOS. La capa de PRESENTACION (ui/) consume esto.

Dependencia permitida (un solo sentido):
    ui  ->  domain  ->  data
"""
