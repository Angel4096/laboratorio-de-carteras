"""
QuantEdge · Scrapper Multi-Activo (Yahoo Finance a Excel)

Descarga el histórico de precios de acciones, materias primas e índices
y lo exporta a UN solo archivo Excel con una hoja por activo + un resumen.
"""

import io
import sys
import time
import warnings

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

# La consola de Windows usa cp1252 y rompe con los emojis: forzamos UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────────────
# CONFIGURACIÓN DE DESCARGA
# ─────────────────────────────────────────────────────
PERIODO   = "max"    # max, 20y, 10y, 5y, 1y...
INTERVALO = "1d"     # 1d, 1wk, 1mo
CARPETA   = "datos"
FILE_NAME = f"{CARPETA}/Activos_{INTERVALO}_{PERIODO}.xlsx"

# ── Universo de activos ──
# nombre : (ticker Yahoo, categoría, nota)
ACTIVOS = {
    "Tesla":              ("TSLA",  "Acción",        ""),
    "Google (Alphabet)":  ("GOOGL", "Acción",        ""),
    "Microsoft":          ("MSFT",  "Acción",        ""),
    "Petroleo WTI":       ("CL=F",  "Materia prima", "Futuro Crude Oil WTI"),
    "Gas Natural":        ("NG=F",  "Materia prima", "Futuro Henry Hub"),
    "Oro":                ("GC=F",  "Materia prima", "Futuro Gold COMEX"),
    "Diamante (proxy)":   ("NGLOY", "Proxy",         "No existe futuro de diamante cotizado. "
                                                     "Se usa Anglo American (dueña de De Beers)"),
    "S&P 500":            ("^GSPC", "Índice",        ""),
    "STOXX Europe 600":   ("^STOXX", "Índice",       ""),
    "Nasdaq 100 (QQQ)":   ("QQQ",   "Índice",        "ETF que replica el Nasdaq-100"),
    "Plata":              ("SI=F",  "Materia prima", "Futuro Silver COMEX"),
    "Cobre":              ("HG=F",  "Materia prima", "Futuro Copper COMEX"),
    "Bonos Tesoro 20+":   ("TLT",   "Renta fija",    "ETF de bonos del Tesoro de EE. UU. a más de 20 años"),
    "Indice Dolar":       ("DX-Y.NYB", "Divisa",     "Índice del dólar frente a seis divisas (ICE)"),
    "Euro (FXE)":         ("FXE",   "Divisa",        "ETF del euro frente al dólar. Cotiza en NY con el mismo cierre que las acciones"),
    "Bitcoin":            ("BTC-USD", "Cripto",      "Cotiza todos los días del año"),
    "Ethereum":           ("ETH-USD", "Cripto",      "Cotiza todos los días del año"),
    "VIX":                ("^VIX",  "Volatilidad",   "Volatilidad implícita del S&P 500. No es invertible"),
    "Short S&P 500 (SH)": ("SH",    "Inverso",       "ETF inverso -1x diario del S&P 500"),
    "Short Nasdaq (PSQ)": ("PSQ",   "Inverso",       "ETF inverso -1x diario del Nasdaq-100"),
    "UltraShort Oro (GLL)": ("GLL", "Inverso",       "ETF inverso -2x diario del oro"),
}

COLUMNAS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def descargar_activo(nombre, ticker):
    """Descarga el histórico de un activo y devuelve un DataFrame limpio."""
    activo = yf.Ticker(ticker)
    df = activo.history(period=PERIODO, interval=INTERVALO, auto_adjust=False)

    if df.empty:
        print(f"  ⚠️  {nombre:<20} ({ticker:<6}) | sin datos devueltos por Yahoo")
        return pd.DataFrame()

    # Excel no admite fechas con zona horaria -> las quitamos
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)
    df.index.name = "Fecha"

    # Nos quedamos solo con las columnas de precio/volumen que existan
    df = df[[c for c in COLUMNAS if c in df.columns]].copy()

    # Métricas derivadas útiles para el backtesting
    df["Retorno %"] = df["Close"].pct_change() * 100
    df["Rango %"] = (df["High"] - df["Low"]) / df["Low"] * 100

    df = df.sort_index()
    print(f"  ✅ {nombre:<20} ({ticker:<6}) | {len(df):>6,} velas | "
          f"{df.index[0]:%Y-%m-%d} → {df.index[-1]:%Y-%m-%d}")
    return df


def nombre_hoja(nombre):
    """Excel limita las hojas a 31 caracteres y prohíbe algunos símbolos."""
    limpio = nombre
    for c in "[]:*?/\\":
        limpio = limpio.replace(c, "-")
    return limpio[:31]


def construir_excel(filename):
    print("━" * 70)
    print(f"  Iniciando descarga de {len(ACTIVOS)} activos ({INTERVALO}, periodo {PERIODO})")
    print("━" * 70)

    datos = {}
    resumen = []

    for nombre, (ticker, categoria, nota) in ACTIVOS.items():
        try:
            df = descargar_activo(nombre, ticker)
        except Exception as e:
            print(f"  ❌ {nombre:<20} ({ticker:<6}) | fallo: {e}")
            df = pd.DataFrame()

        if not df.empty:
            datos[nombre] = df
            variacion = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
            resumen.append({
                "Activo":         nombre,
                "Ticker":         ticker,
                "Categoria":      categoria,
                "Velas":          len(df),
                "Desde":          df.index[0].strftime("%Y-%m-%d"),
                "Hasta":          df.index[-1].strftime("%Y-%m-%d"),
                "Ultimo cierre":  round(float(df["Close"].iloc[-1]), 4),
                "Variacion %":    round(float(variacion), 2),
                "Nota":           nota,
            })

        time.sleep(0.5)  # cortesía con la API de Yahoo

    if not datos:
        print("❌ No se descargó ningún activo. Revisa tu conexión.")
        return

    # ── Exportar a Excel ──
    df_resumen = pd.DataFrame(resumen)

    with pd.ExcelWriter(filename, engine="openpyxl", datetime_format="yyyy-mm-dd") as writer:
        df_resumen.to_excel(writer, sheet_name="Resumen", index=False)
        for nombre, df in datos.items():
            df.to_excel(writer, sheet_name=nombre_hoja(nombre))

        # Formato: ancho de columnas y paneles congelados
        for hoja in writer.book.worksheets:
            hoja.freeze_panes = "B2"
            for col in hoja.columns:
                largo = max((len(str(c.value)) for c in col if c.value is not None), default=10)
                hoja.column_dimensions[col[0].column_letter].width = min(max(largo + 2, 12), 40)

    print("━" * 70)
    print(f"  ✅ Descarga completada con éxito.")
    print(f"  📊 Archivo guardado como : {filename}")
    print(f"  📈 Activos exportados    : {len(datos)} hojas + Resumen")
    print("━" * 70)
    print(df_resumen.to_string(index=False))
    print("━" * 70)


if __name__ == "__main__":
    construir_excel(FILE_NAME)
