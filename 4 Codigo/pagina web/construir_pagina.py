"""
Construye el Laboratorio de carteras a partir de los CSV del informe.

Lee los 21 CSV de "Proyecto Trading U/datos_csv", alinea los precios de cierre
por fecha (solo las jornadas en que cotizaron todos los activos, igual que en el
informe), añade las carteras de referencia y escribe dos archivos:

  ../Laboratorio de carteras.html      documento completo para abrir en el navegador
  fragmento_publicacion.html           mismo contenido sin <html>/<head>/<body>,
                                       para publicarlo como página web

Las carteras de mínima varianza y de mejor relación salen de presets.json,
que genera presets_simulacion.R con la misma semilla que la sección 10 del informe.
"""

import io
import json
import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
CSV = RAIZ / "Proyecto Trading U" / "datos_csv"
SALIDA_COMPLETA = AQUI.parent / "Laboratorio de carteras.html"
SALIDA_FRAGMENTO = AQUI / "fragmento_publicacion.html"

# id, archivo, nombre, ticker, clase, invertible, nota
ACTIVOS = [
    ("SP500", "SP500", "S&P 500", "^GSPC", "Índices", True, "Índice de referencia del mercado estadounidense."),
    ("STOXX600", "STOXX600", "STOXX Europe 600", "^STOXX", "Índices", True, "Cierra horas antes que Nueva York, lo que reduce su correlación del mismo día con EE. UU."),
    ("QQQ", "QQQ", "Nasdaq-100", "QQQ", "Índices", True, "Fondo cotizado que replica el Nasdaq-100."),
    ("TSLA", "TSLA", "Tesla", "TSLA", "Acciones", True, "La beta más alta entre los activos invertibles."),
    ("GOOGL", "GOOGL", "Google", "GOOGL", "Acciones", True, ""),
    ("MSFT", "MSFT", "Microsoft", "MSFT", "Acciones", True, "Paga dividendos que no están incluidos."),
    ("DIAMANTE", "DIAMANTE", "Diamante (Anglo American)", "NGLOY", "Acciones", True, "Aproximación: el diamante no cotiza en bolsa. Es una acción minera dueña de De Beers."),
    ("PETROLEO", "PETROLEO", "Petróleo WTI", "CL=F", "Materias primas", True, "Futuro continuo: puede tener saltos al cambiar de contrato."),
    ("GASNATURAL", "GASNATURAL", "Gas natural", "NG=F", "Materias primas", True, "Futuro continuo con días extremos que conviene verificar."),
    ("ORO", "ORO", "Oro", "GC=F", "Materias primas", True, "Futuro continuo. Casi sin relación con las acciones en el periodo."),
    ("PLATA", "PLATA", "Plata", "SI=F", "Materias primas", True, "Futuro continuo."),
    ("COBRE", "COBRE", "Cobre", "HG=F", "Materias primas", True, "Futuro continuo, ligado a la actividad industrial."),
    ("TLT", "TLT", "Bonos del Tesoro 20+", "TLT", "Renta fija", True, "Solo precio: los intereses mensuales del fondo no están incluidos."),
    ("DOLAR", "DOLAR", "Índice del dólar", "DX-Y.NYB", "Divisas", True, "Índice: en la práctica se invierte con futuros o fondos."),
    ("EURO", "EURO", "Euro", "FXE", "Divisas", True, "Fondo del euro frente al dólar. Correlación de −0,94 con el índice del dólar."),
    ("BTC", "BTC", "Bitcoin", "BTC-USD", "Criptoactivos", True, "Cotiza todos los días; sus fines de semana se acumulan en el lunes."),
    ("ETH", "ETH", "Ethereum", "ETH-USD", "Criptoactivos", True, "Cotiza todos los días."),
    ("SH", "SH", "Short S&P 500", "SH", "Inversos", True, "Inverso −1x diario del S&P 500. Pierde valor en mercados alcistas."),
    ("PSQ", "PSQ", "Short Nasdaq-100", "PSQ", "Inversos", True, "Inverso −1x diario del Nasdaq-100."),
    ("GLL", "GLL", "UltraShort oro", "GLL", "Inversos", True, "Inverso −2x diario del oro. El reajuste diario erosiona su valor."),
    ("VIX", "VIX", "VIX", "^VIX", "Volatilidad", False, "Indicador de volatilidad esperada. No se puede comprar directamente."),
]


def cargar_precios():
    series = {}
    for id_, archivo, *_ in ACTIVOS:
        df = pd.read_csv(CSV / f"{archivo}.csv", usecols=["Date", "Close"])
        series[id_] = df.set_index("Date")["Close"]
    tabla = pd.concat(series, axis=1, join="inner").sort_index()
    return tabla


def redondear(x):
    return float(f"{x:.7g}")


def presets(simulados):
    invertibles = [a[0] for a in ACTIVOS if a[5]]
    iguales = {i: 1 / len(invertibles) for i in invertibles}
    return [
        {"id": "diversificada", "nombre": "Diversificada",
         "desc": "35 % S&P 500, 20 % oro, 10 % Nasdaq-100, 10 % STOXX 600, 10 % bonos y 5 % en cobre, bitcoin y petróleo. En el informe superó al S&P 500 con menos volatilidad.",
         "pesos": {"SP500": .35, "QQQ": .10, "STOXX600": .10, "ORO": .20, "COBRE": .05, "TLT": .10, "BTC": .05, "PETROLEO": .05}},
        {"id": "sp500", "nombre": "Solo S&P 500",
         "desc": "Todo en el índice. Es la referencia contra la que se compara el resto.",
         "pesos": {"SP500": 1}},
        {"id": "iguales", "nombre": "Pesos iguales",
         "desc": "5 % en cada uno de los 20 activos invertibles. No requiere ninguna decisión y aun así superó al índice en rendimiento por unidad de riesgo.",
         "pesos": iguales},
        {"id": "6040", "nombre": "60/40",
         "desc": "60 % S&P 500 y 40 % bonos del Tesoro. Fue la peor del informe: los bonos perdieron 44 % de su precio y no protegieron.",
         "pesos": {"SP500": .6, "TLT": .4}},
        {"id": "cubierta", "nombre": "Cubierta 50/50",
         "desc": "50 % S&P 500 y 50 % Short S&P 500. La correlación de −0,99 anula el riesgo y también el rendimiento.",
         "pesos": {"SP500": .5, "SH": .5}},
        {"id": "minvar", "nombre": "Mínima varianza",
         "desc": "La de menor volatilidad entre 5.000 carteras aleatorias. Se apoya en dólar, euro y Short S&P 500, por eso rinde poco.",
         "pesos": simulados["minvar"]},
        {"id": "mejor", "nombre": "Mejor relación",
         "desc": "La de mejor rendimiento por unidad de riesgo entre 5.000 carteras aleatorias. Elegida mirando los mismos datos, así que su resultado está sobreestimado.",
         "pesos": simulados["mejor"]},
    ]


def main():
    tabla = cargar_precios()
    simulados = json.loads((AQUI / "presets.json").read_text(encoding="utf-8"))
    datos = {
        "fechas": list(tabla.index),
        "activos": [
            {"id": a[0], "nombre": a[2], "ticker": a[3], "clase": a[4], "invertible": a[5], "nota": a[6]}
            for a in ACTIVOS
        ],
        "precios": {id_: [redondear(v) for v in tabla[id_].tolist()] for id_ in tabla.columns},
        "presets": presets(simulados),
    }
    js = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    plantilla = (AQUI / "plantilla.html").read_text(encoding="utf-8")
    marca = "/*__DATA__*/null"
    assert plantilla.count(marca) == 1
    fragmento = plantilla.replace(marca, js)

    SALIDA_FRAGMENTO.write_text(fragmento, encoding="utf-8", newline="\n")
    completo = (
        '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        "</head>\n<body>\n" + fragmento + "\n</body>\n</html>\n"
    )
    SALIDA_COMPLETA.write_text(completo, encoding="utf-8", newline="\n")

    print(f"Fechas alineadas : {len(tabla)}  ({tabla.index[0]} a {tabla.index[-1]})")
    print(f"Activos          : {len(tabla.columns)}")
    print(f"Página completa  : {SALIDA_COMPLETA.name}  ({SALIDA_COMPLETA.stat().st_size / 1024:.0f} KB)")
    print(f"Fragmento        : {SALIDA_FRAGMENTO.name}  ({SALIDA_FRAGMENTO.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
