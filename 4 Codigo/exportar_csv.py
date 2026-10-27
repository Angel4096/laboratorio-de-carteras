"""
Exporta cada hoja del Excel del scrapper a un CSV con el formato clasico de
Yahoo Finance (Date, Open, High, Low, Close, Adj Close, Volume) para que R
lo lea con read.csv().

Se recorta a una ventana comun de 5 anios para que los 21 activos sean
comparables entre si (mismo numero aproximado de observaciones).
"""

import io
import sys
import unicodedata

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EXCEL   = "../Scrapper precio acciones/datos/Activos_1d_max.xlsx"
SALIDA  = "datos_csv"
ANIOS   = 5
# Ultimo dia de la ventana. Se fija para que el informe sea reproducible aunque
# el scrapper se vuelva a ejecutar. None = usar el ultimo dato disponible.
FECHA_FIN = "2026-09-04"

# hoja del Excel : nombre del archivo csv (sin tildes ni espacios, para R)
HOJAS = {
    "Tesla":             "TSLA",
    "Google (Alphabet)": "GOOGL",
    "Microsoft":         "MSFT",
    "Petroleo WTI":      "PETROLEO",
    "Gas Natural":       "GASNATURAL",
    "Oro":               "ORO",
    "Diamante (proxy)":  "DIAMANTE",
    "S&P 500":           "SP500",
    "STOXX Europe 600":  "STOXX600",
    "Nasdaq 100 (QQQ)":  "QQQ",
    "Plata":             "PLATA",
    "Cobre":             "COBRE",
    "Bonos Tesoro 20+":  "TLT",
    "Indice Dolar":      "DOLAR",
    "Euro (FXE)":        "EURO",
    "Bitcoin":           "BTC",
    "Ethereum":          "ETH",
    "VIX":               "VIX",
    "Short S&P 500 (SH)":   "SH",
    "Short Nasdaq (PSQ)":   "PSQ",
    "UltraShort Oro (GLL)": "GLL",
}

COLS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def main():
    print("━" * 70)
    print(f"  Exportando hojas a CSV (ventana comun de {ANIOS} anios)")
    print("━" * 70)

    hojas = pd.read_excel(EXCEL, sheet_name=None, index_col=0)

    # Fecha de corte: 5 anios antes del ultimo dato disponible
    if FECHA_FIN:
        ultima = pd.Timestamp(FECHA_FIN)
    else:
        ultima = max(df.index.max() for n, df in hojas.items() if n != "Resumen")
    corte = ultima - pd.DateOffset(years=ANIOS)
    print(f"  Ventana: {corte:%Y-%m-%d} → {ultima:%Y-%m-%d}\n")

    for hoja, archivo in HOJAS.items():
        df = hojas[hoja].copy()
        df.index = pd.to_datetime(df.index)
        df = df.loc[(df.index >= corte) & (df.index <= ultima), [c for c in COLS if c in df.columns]]

        df.index.name = "Date"
        df = df.reset_index()
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

        ruta = f"{SALIDA}/{archivo}.csv"
        df.to_csv(ruta, index=False)
        print(f"  ✅ {hoja:<20} → {ruta:<28} | {len(df):>5,} filas")

    print("━" * 70)


if __name__ == "__main__":
    main()
