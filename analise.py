# Le os dados que o job do Hadoop entregou, roda o K-means de 2 a 10 e calcula o Silhouette e as correlacoes
import glob
import os
import sys

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

COLUNAS = ["X", "Y", "FFMC", "DMC", "DC", "ISI", "temp", "RH", "wind", "rain", "area"]
K_MINIMO, K_MAXIMO = 2, 10
# o K-means roda 100 vezes com centroides iniciais diferentes e fica com a de menor erro
# (com 10, o K = 3 as vezes nao achava o agrupamento de menor erro e o melhor K mudava conforme a semente)
TENTATIVAS = 100
SEMENTE = 42     # deixa o resultado igual em toda execucao

entrada, saida = sys.argv[1], sys.argv[2]
os.makedirs(saida, exist_ok=True)

# 1. dados vindos do Hadoop: uma linha por registro, so com as 11 colunas numericas
arquivos = sorted(glob.glob(os.path.join(entrada, "part-*")))
dados = pd.concat([pd.read_csv(a, header=None, names=COLUNAS) for a in arquivos], ignore_index=True)
print(f"Linhas recebidas do Hadoop: {len(dados)}")

# 2. z-score: cada coluna fica com media 0 e desvio padrao 1, para nenhuma pesar mais na distancia
padronizados = StandardScaler().fit_transform(dados)

silhuetas, correlacoes, medias = [], [], []


# guarda o tamanho, a media de cada coluna e a matriz de correlacao (todas contra todas) de um grupo
def guardar(k, cluster, grupo):
    medias.append({"k": k, "cluster": cluster, "linhas": len(grupo), **grupo.mean().to_dict()})
    matriz = grupo.corr()  # Pearson, nos valores originais
    matriz.insert(0, "coluna", matriz.index)
    matriz.insert(0, "linhas", len(grupo))
    matriz.insert(0, "cluster", cluster)
    matriz.insert(0, "k", k)
    correlacoes.append(matriz)


guardar("todos", "todos", dados)  # dataset inteiro, para comparar com os clusters

# 3. K-means e Silhouette para cada K
for k in range(K_MINIMO, K_MAXIMO + 1):
    rotulos = KMeans(n_clusters=k, n_init=TENTATIVAS, random_state=SEMENTE).fit_predict(padronizados)
    silhuetas.append({"k": k, "silhouette": silhouette_score(padronizados, rotulos)})

    # o K-means numera os clusters sem ordem; aqui o cluster 1 passa a ser o maior
    tamanhos = np.bincount(rotulos)
    ordem = sorted(range(k), key=lambda r: (-tamanhos[r], r))
    numero = {rotulo: i + 1 for i, rotulo in enumerate(ordem)}
    clusters = np.array([numero[r] for r in rotulos])

    for c in range(1, k + 1):
        guardar(k, c, dados[clusters == c])

tabela = pd.DataFrame(silhuetas)
correlacoes = pd.concat(correlacoes, ignore_index=True)
medias = pd.DataFrame(medias)

tabela.to_csv(os.path.join(saida, "silhouette.csv"), index=False)
correlacoes.to_csv(os.path.join(saida, "correlacoes.csv"), index=False)
medias.to_csv(os.path.join(saida, "medias.csv"), index=False)

# 4. melhor K: o de maior Silhouette (clusters mais separados entre si e mais coesos por dentro)
melhor_k = int(tabela.loc[tabela["silhouette"].idxmax(), "k"])

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", None)
print("\n=== Silhouette por K ===")
print(tabela.round(4).to_string(index=False))
print(f"\nMelhor K: {melhor_k}")

print(f"\n=== Linhas e media de cada coluna (dataset inteiro e clusters do K = {melhor_k}) ===")
print(medias[medias["k"].isin(["todos", melhor_k])].round(2).to_string(index=False))

for cluster in ["todos"] + list(range(1, melhor_k + 1)):
    k = "todos" if cluster == "todos" else melhor_k
    matriz = correlacoes[(correlacoes["k"] == k) & (correlacoes["cluster"] == cluster)]
    print(f"\n=== Correlacao, K = {k}, cluster {cluster} ({matriz['linhas'].iloc[0]} linhas) ===")
    print(matriz.set_index("coluna")[COLUNAS].round(2).to_string())
