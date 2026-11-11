set -e

mvn package
rm -rf saida-dados saida-analise

# 1. Hadoop: busca as colunas numericas do dataset
hadoop jar target/kmeans-silhouette-1.0.jar br.pucpr.bigdata.dados.DadosMain input/forestfireinput.csv saida-dados

# 2. Python: z-score, K-means de 2 a 10, Silhouette e correlacoes
if [ ! -d .venv ]; then
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi
.venv/bin/python analise.py saida-dados saida-analise
