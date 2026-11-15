# Gráficos dos experimentos: lê as tabelas de experimentos/resultados/ e grava os PNG.
# Uso: python graficos.py
# Precisa do matplotlib:  python -m pip install matplotlib

import csv
import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados")
COR = {"sequencial": "#1f77b4", "concorrente": "#ff7f0e"}


def numero(texto):
    return float(texto.replace(",", "."))


def ler(nome):
    with open(os.path.join(RESULTADOS, nome), newline="", encoding="utf-8-sig") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def salvar(figura, nome):
    figura.tight_layout()
    figura.savefig(os.path.join(RESULTADOS, nome), dpi=150)
    plt.close(figura)
    print("gravado:", nome)


def grafico_latencia():
    linhas = ler("exp3_resumo.csv")
    figura, eixo = plt.subplots(figsize=(8, 5))
    for modo in ("sequencial", "concorrente"):
        dados = [l for l in linhas if l["modo"] == modo]
        x = [numero(l["atraso_por_fornecedor_s"]) for l in dados]
        y = [numero(l["media_ms"]) / 1000 for l in dados]
        erro = [numero(l["desvio_ms"]) / 1000 for l in dados]
        teorico = [numero(l["teorico_ms"]) / 1000 for l in dados]
        eixo.errorbar(x, y, yerr=erro, marker="o", capsize=3, color=COR[modo], label=f"{modo} (medido)")
        eixo.plot(x, teorico, linestyle="--", color=COR[modo], alpha=0.5, label=f"{modo} (teórico)")
    eixo.set_xticks(x)
    eixo.set_xlabel("Atraso de cada fornecedor (s)")
    eixo.set_ylabel("Tempo total da pesquisa (s)")
    eixo.set_title("Experimento 3: tempo da pesquisa × atraso dos fornecedores")
    eixo.grid(alpha=0.3)
    eixo.legend()
    salvar(figura, "grafico_1_latencia.png")


def grafico_clientes():
    linhas = ler("exp4_resumo.csv")
    figura, eixo = plt.subplots(figsize=(8, 5))
    quantidades = []
    for modo in ("sequencial", "concorrente"):
        dados = [l for l in linhas if l["modo"] == modo]
        x = [int(l["clientes"]) for l in dados]
        y = [numero(l["media_por_cliente_ms"]) / 1000 for l in dados]
        quantidades = x
        eixo.plot(x, y, marker="o", color=COR[modo], label=modo)
    eixo.set_xticks(quantidades)
    eixo.set_xlabel("Clientes pesquisando ao mesmo tempo")
    eixo.set_ylabel("Tempo médio por cliente (s)")
    eixo.set_title("Experimento 4: tempo por cliente × número de clientes")
    eixo.set_ylim(bottom=0)
    eixo.grid(alpha=0.3)
    eixo.legend()
    salvar(figura, "grafico_2_clientes.png")


def grafico_falhas():
    linhas = ler("exp5_resumo.csv")
    cenarios = []
    for l in linhas:
        if l["cenario"] not in cenarios:
            cenarios.append(l["cenario"])
    figura, eixo = plt.subplots(figsize=(9, 5))
    largura = 0.38
    for i, modo in enumerate(("sequencial", "concorrente")):
        valores, erros = [], []
        for c in cenarios:
            linha = next(l for l in linhas if l["cenario"] == c and l["modo"] == modo)
            valores.append(numero(linha["media_ms"]) / 1000)
            erros.append(numero(linha["desvio_ms"]) / 1000)
        posicoes = [p + (i - 0.5) * largura for p in range(len(cenarios))]
        barras = eixo.bar(posicoes, valores, largura, yerr=erros, capsize=3, color=COR[modo], label=modo)
        eixo.bar_label(barras, labels=[f"{v:.2f}".replace(".", ",") for v in valores], padding=3, fontsize=9)
    eixo.set_xticks(range(len(cenarios)))
    eixo.set_xticklabels([textwrap.fill(c, 20) for c in cenarios])
    eixo.set_ylabel("Tempo total da pesquisa (s)")
    eixo.set_title("Experimento 5: tempo da pesquisa com um fornecedor indisponível")
    eixo.set_ylim(0, eixo.get_ylim()[1] * 1.1)
    eixo.grid(axis="y", alpha=0.3)
    eixo.legend()
    salvar(figura, "grafico_3_falhas.png")


if __name__ == "__main__":
    grafico_latencia()
    grafico_clientes()
    grafico_falhas()
