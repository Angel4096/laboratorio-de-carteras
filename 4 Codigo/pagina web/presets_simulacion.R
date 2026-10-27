# Genera presets.json: pesos de las carteras de minima varianza y de mejor relacion
# entre 5.000 carteras aleatorias (misma semilla que la seccion 10 del informe).
# Ejecutar desde cualquier carpeta: Rscript presets_simulacion.R
suppressMessages({library(tidyverse)})
setwd("C:/Users/norba/OneDrive/NUESTRO HOGAR/1. ANGEL SANTIAGO/6 SEMESTRE/Proyecto TRADING/Proyecto Trading U")
arch <- c("Tesla"="TSLA","Google"="GOOGL","Microsoft"="MSFT","Petroleo WTI"="PETROLEO","Gas natural"="GASNATURAL",
          "Oro"="ORO","Diamante (proxy)"="DIAMANTE","S&P 500"="SP500","STOXX Europe 600"="STOXX600",
          "Nasdaq 100 (QQQ)"="QQQ","Plata"="PLATA","Cobre"="COBRE","Bonos Tesoro 20+"="TLT",
          "Indice dolar"="DOLAR","Euro (FXE)"="EURO","Bitcoin"="BTC","Ethereum"="ETH","VIX"="VIX",
          "Short S&P 500 (SH)"="SH","Short Nasdaq (PSQ)"="PSQ","UltraShort Oro (GLL)"="GLL")
act <- map(arch, ~ read.csv(paste0("datos_csv/", .x, ".csv")))
precios <- map_dfr(names(act), ~ data.frame(Date = as.Date(act[[.x]]$Date), Activo = .x, Close = act[[.x]]$Close)) |>
  pivot_wider(names_from = Activo, values_from = Close) |> arrange(Date)
comunes <- precios[complete.cases(precios[ , names(act)]), ]
X <- apply(as.matrix(comunes[ , names(act)]), 2, function(p) diff(log(p)))
invertibles <- setdiff(colnames(X), "VIX")
R <- exp(X[ , invertibles]) - 1
set.seed(2026)
S <- 5000
W <- matrix(rexp(S * ncol(R)), nrow = ncol(R)); W <- t(t(W) / colSums(W)); rownames(W) <- colnames(R)
RP <- R %*% W
vol <- apply(RP, 2, sd); rend <- apply(1 + RP, 2, prod)^(252 / nrow(R)) - 1
imin <- which.min(vol); imax <- which.max(rend / vol)
a_json <- function(w) paste0("{", paste0('"', arch[names(w)], '":', sprintf("%.6f", w), collapse = ","), "}")
cat('{"minvar":', a_json(W[ , imin]), ',"mejor":', a_json(W[ , imax]), '}', sep = "", file = "../Pagina web/fuente/presets.json")
cat("min var vol", round(vol[imin]*sqrt(252)*100,2), " mejor rend", round(rend[imax]*100,2), "\n")
