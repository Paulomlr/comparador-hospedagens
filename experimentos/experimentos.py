# Experimentos 1 a 5: sobe os fornecedores e o agregador, faz as medições e grava
# as tabelas em experimentos/resultados/. Os gráficos são feitos por graficos.py.
# Uso: python experimentos.py            (execução completa, cerca de 10 minutos)
#      python experimentos.py --rapido   (poucas repetições, só para testar)
# Feche os fornecedores e o agregador antes: o script abre os seus próprios.

import csv
import json
import os
import socket
import statistics
import subprocess
import sys
import threading
import time
from collections import Counter
from datetime import datetime

PASTA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA)
RESULTADOS = os.path.join(PASTA, "resultados")
FORNECEDOR = os.path.join(RAIZ, "fornecedores", "fornecedor.py")
AGREGADOR = os.path.join(RAIZ, "agregador", "agregador.py")

HOST = "127.0.0.1"
PORTA_AGREGADOR = 5000
PORTAS = {"A": 5001, "B": 5002, "C": 5003, "D": 5004}
ATRASOS_BASE = {"A": 0.5, "B": 1.0, "C": 1.5, "D": 2.0}
MODOS = ["sequencial", "concorrente"]
INSTANTE_QUEDA = 1.0  # segundos depois do início da pesquisa (experimento 5)

RAPIDO = "--rapido" in sys.argv
REPETICOES_BASE = 2 if RAPIDO else 10
REPETICOES_LATENCIA = 1 if RAPIDO else 5
REPETICOES_CLIENTES = 1 if RAPIDO else 3
REPETICOES_FALHAS = 1 if RAPIDO else 5
ATRASOS_LATENCIA = [0.5, 1.0, 2.0] if RAPIDO else [0.5, 1.0, 1.5, 2.0, 2.5]
NUMEROS_CLIENTES = [1, 5] if RAPIDO else [1, 5, 10, 20]

processos = {}


# ---------- controle dos programas ----------

def porta_aberta(porta):
    try:
        with socket.create_connection((HOST, porta), timeout=1):
            return True
    except OSError:
        return False


def esperar_porta(porta, limite=20):
    fim = time.time() + limite
    while time.time() < fim:
        if porta_aberta(porta):
            return
        time.sleep(0.3)
    raise RuntimeError(f"a porta {porta} não abriu")


def ambiente():
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["REGISTRO_TEMPOS"] = os.path.join(RESULTADOS, "registro_tempos_experimentos.csv")
    return env


def subir_fornecedor(letra, atraso):
    processos[letra] = subprocess.Popen(
        [sys.executable, FORNECEDOR, letra, str(PORTAS[letra]), str(atraso)],
        env=ambiente(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    esperar_porta(PORTAS[letra])


def subir_agregador():
    processos["agregador"] = subprocess.Popen(
        [sys.executable, AGREGADOR],
        env=ambiente(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    esperar_porta(PORTA_AGREGADOR)


def derrubar(nome):
    processo = processos.pop(nome, None)
    if processo is not None and processo.poll() is None:
        processo.kill()
        processo.wait()


def configurar(atrasos):
    # reinicia os quatro fornecedores com os atrasos pedidos
    for letra in PORTAS:
        derrubar(letra)
    for letra in PORTAS:
        subir_fornecedor(letra, atrasos[letra])


# ---------- uma pesquisa ----------

def pesquisar(modo, destino="Rio de Janeiro"):
    pedido = {"operacao": "pesquisar", "destino": destino, "checkin": "10/12/2026",
              "checkout": "15/12/2026", "hospedes": 2, "modo": modo}
    resultado = {"modo": modo, "ok": False, "status": "falha de comunicação"}
    inicio = time.perf_counter()
    try:
        with socket.create_connection((HOST, PORTA_AGREGADOR), timeout=5) as conexao:
            conexao.settimeout(60)
            conexao.sendall((json.dumps(pedido) + "\n").encode("utf-8"))
            dados = b""
            while b"\n" not in dados:
                pedaco = conexao.recv(4096)
                if not pedaco:
                    break
                dados += pedaco
        resposta = json.loads(dados.split(b"\n")[0].decode("utf-8"))
    except (OSError, ValueError):
        resultado["rtt_ms"] = round((time.perf_counter() - inicio) * 1000)
        return resultado

    resultado["rtt_ms"] = round((time.perf_counter() - inicio) * 1000)
    resultado["status"] = resposta.get("status")
    if resposta.get("status") == "sucesso":
        resultado["ok"] = True
        resultado["tempo_total_ms"] = resposta["tempo_total_ms"]
        resultado["resultados"] = len(resposta["resultados"])
        for f in resposta["fornecedores"]:
            letra = f["fonte"][-1]
            resultado[f"tempo_{letra}_ms"] = f["tempo_ms"]
            resultado[f"status_{letra}"] = f["status"]
        mais = resposta["mais_economica"]
        reais = f"{mais['preco_total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if mais else ""
        resultado["mais_economica"] = f"{mais['nome']} ({mais['fonte']}) R$ {reais}" if mais else ""
    return resultado


# ---------- tabelas ----------

def virgula(valor, casas=1):
    return f"{valor:.{casas}f}".replace(".", ",")


def curto(valor):
    # 0.5 -> "0,5"; 2.0 -> "2"
    return f"{valor:g}".replace(".", ",")


def estatisticas(valores):
    desvio = statistics.stdev(valores) if len(valores) > 1 else 0.0
    return statistics.mean(valores), desvio, min(valores), max(valores)


def gravar_csv(nome, cabecalho, linhas):
    caminho = os.path.join(RESULTADOS, nome)
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)


def tabela_md(cabecalho, linhas):
    texto = "| " + " | ".join(cabecalho) + " |\n"
    texto += "|" + "---|" * len(cabecalho) + "\n"
    for linha in linhas:
        texto += "| " + " | ".join(str(c) for c in linha) + " |\n"
    return texto


def valor(resultado, chave, padrao=""):
    return resultado.get(chave, padrao)


# ---------- experimentos ----------

def experimento_1_2():
    print("Experimentos 1 e 2: consulta sequencial e concorrente...", flush=True)
    configurar(ATRASOS_BASE)
    for modo in MODOS:
        pesquisar(modo)  # aquecimento, descartado

    brutos = []
    por_modo = {modo: [] for modo in MODOS}
    for modo in MODOS:
        for repeticao in range(1, REPETICOES_BASE + 1):
            r = pesquisar(modo)
            if r["ok"]:
                por_modo[modo].append(r)
                brutos.append([modo, repeticao, r["tempo_total_ms"], r["rtt_ms"]]
                              + [r[f"tempo_{letra}_ms"] for letra in PORTAS])
    gravar_csv("exp1_2_repeticoes.csv",
               ["modo", "repeticao", "tempo_total_ms", "ida_e_volta_ms"]
               + [f"tempo_{letra}_ms" for letra in PORTAS], brutos)

    resumo = []
    medias = {}
    for modo in MODOS:
        rs = por_modo[modo]
        media, desvio, minimo, maximo = estatisticas([r["tempo_total_ms"] for r in rs])
        medias[modo] = media
        soma = statistics.mean(sum(r[f"tempo_{l}_ms"] for l in PORTAS) for r in rs)
        maior = statistics.mean(max(r[f"tempo_{l}_ms"] for l in PORTAS) for r in rs)
        resumo.append([modo, len(rs), virgula(media), virgula(desvio), minimo, maximo,
                       virgula(soma), virgula(maior)])
    cab = ["modo", "repeticoes", "media_ms", "desvio_ms", "min_ms", "max_ms",
           "soma_tempos_fornecedores_ms", "maior_tempo_fornecedor_ms"]
    gravar_csv("exp1_2_resumo.csv", cab, resumo)

    ganho = medias["sequencial"] / medias["concorrente"]
    texto = (f"Atrasos dos fornecedores: A {curto(ATRASOS_BASE['A'])} s, B {curto(ATRASOS_BASE['B'])} s, "
             f"C {curto(ATRASOS_BASE['C'])} s, D {curto(ATRASOS_BASE['D'])} s. "
             f"Repetições por modo: {REPETICOES_BASE} (mais uma de aquecimento, descartada).\n\n"
             + tabela_md(cab, resumo)
             + f"\nGanho do concorrente (média sequencial / média concorrente): {virgula(ganho, 2)}x\n")
    return "Experimentos 1 e 2: consulta sequencial e consulta concorrente", texto


def experimento_3():
    print("Experimento 3: simulação de latência...", flush=True)
    brutos = []
    resumo = []
    for atraso in ATRASOS_LATENCIA:
        configurar({letra: atraso for letra in PORTAS})
        for modo in MODOS:
            pesquisar(modo)  # aquecimento, descartado
        for modo in MODOS:
            tempos = []
            for repeticao in range(1, REPETICOES_LATENCIA + 1):
                r = pesquisar(modo)
                if r["ok"]:
                    tempos.append(r["tempo_total_ms"])
                    brutos.append([virgula(atraso, 2), modo, repeticao, r["tempo_total_ms"], r["rtt_ms"]])
            media, desvio, minimo, maximo = estatisticas(tempos)
            teorico = atraso * 1000 * (len(PORTAS) if modo == "sequencial" else 1)
            resumo.append([virgula(atraso, 2), modo, len(tempos), virgula(media), virgula(desvio),
                           minimo, maximo, round(teorico)])
        print(f"  atraso {atraso} s concluído", flush=True)
    gravar_csv("exp3_repeticoes.csv",
               ["atraso_por_fornecedor_s", "modo", "repeticao", "tempo_total_ms", "ida_e_volta_ms"], brutos)
    cab = ["atraso_por_fornecedor_s", "modo", "repeticoes", "media_ms", "desvio_ms", "min_ms",
           "max_ms", "teorico_ms"]
    gravar_csv("exp3_resumo.csv", cab, resumo)
    texto = ("Os quatro fornecedores usam o mesmo atraso em cada linha. "
             "Valor teórico: sequencial = 4 x atraso; concorrente = atraso.\n\n" + tabela_md(cab, resumo))
    return "Experimento 3: simulação de latência", texto


def clientes_simultaneos(modo, quantidade):
    resultados = [None] * quantidade
    largada = threading.Barrier(quantidade)

    def cliente(posicao):
        largada.wait()  # todos começam juntos
        resultados[posicao] = pesquisar(modo)

    inicio = time.perf_counter()
    threads = [threading.Thread(target=cliente, args=(i,)) for i in range(quantidade)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    parede = round((time.perf_counter() - inicio) * 1000)
    return resultados, parede


def experimento_4():
    print("Experimento 4: vários clientes ao mesmo tempo...", flush=True)
    configurar(ATRASOS_BASE)
    for modo in MODOS:
        pesquisar(modo)  # aquecimento, descartado

    brutos = []
    resumo = []
    for modo in MODOS:
        for quantidade in NUMEROS_CLIENTES:
            medias, maximos, paredes, falhas_total = [], [], [], 0
            for repeticao in range(1, REPETICOES_CLIENTES + 1):
                resultados, parede = clientes_simultaneos(modo, quantidade)
                tempos = [r["rtt_ms"] for r in resultados]
                falhas = sum(1 for r in resultados if not r["ok"])
                medias.append(statistics.mean(tempos))
                maximos.append(max(tempos))
                paredes.append(parede)
                falhas_total += falhas
                brutos.append([modo, quantidade, repeticao, round(statistics.mean(tempos)),
                               max(tempos), parede, falhas])
            resumo.append([modo, quantidade, REPETICOES_CLIENTES, virgula(statistics.mean(medias)),
                           virgula(statistics.mean(maximos)), virgula(statistics.mean(paredes)), falhas_total])
            print(f"  {modo}, {quantidade} cliente(s) concluído", flush=True)
    gravar_csv("exp4_repeticoes.csv",
               ["modo", "clientes", "repeticao", "media_por_cliente_ms", "maior_tempo_ms",
                "tempo_total_ms", "pesquisas_com_falha"], brutos)
    cab = ["modo", "clientes", "repeticoes", "media_por_cliente_ms", "maior_tempo_ms",
           "tempo_total_ms", "pesquisas_com_falha"]
    gravar_csv("exp4_resumo.csv", cab, resumo)
    texto = (f"Atrasos dos fornecedores: iguais aos do experimento 1. Cada rodada dispara todos os "
             f"clientes ao mesmo tempo. Tempos medidos pelo cliente (ida e volta).\n\n" + tabela_md(cab, resumo))
    return "Experimento 4: vários clientes ao mesmo tempo", texto


def experimento_5():
    print("Experimento 5: indisponibilidade de um fornecedor...", flush=True)
    configurar(ATRASOS_BASE)
    for modo in MODOS:
        pesquisar(modo)  # aquecimento, descartado

    linhas = []  # (cenario, modo, repeticao, resultado)

    for modo in MODOS:
        for repeticao in range(1, REPETICOES_FALHAS + 1):
            linhas.append(("todos ativos", modo, repeticao, pesquisar(modo)))

    derrubar("C")
    for modo in MODOS:
        for repeticao in range(1, REPETICOES_FALHAS + 1):
            linhas.append(("C desativado antes da pesquisa", modo, repeticao, pesquisar(modo)))
    subir_fornecedor("C", ATRASOS_BASE["C"])

    for modo in MODOS:
        for repeticao in range(1, REPETICOES_FALHAS + 1):
            resultado = {}
            pesquisa = threading.Thread(target=lambda: resultado.update(pesquisar(modo)))
            pesquisa.start()
            time.sleep(INSTANTE_QUEDA)
            derrubar("C")  # desativa o C no meio da pesquisa
            pesquisa.join()
            subir_fornecedor("C", ATRASOS_BASE["C"])
            linhas.append((f"C desativado {curto(INSTANTE_QUEDA)} s depois do início", modo, repeticao, resultado))
        print(f"  cenário 'durante' ({modo}) concluído", flush=True)

    brutos = [[c, m, i, valor(r, "tempo_total_ms"), r.get("rtt_ms", ""), valor(r, "status_C"),
               valor(r, "tempo_C_ms"), valor(r, "resultados"), valor(r, "mais_economica"), r["status"]]
              for c, m, i, r in linhas]
    gravar_csv("exp5_repeticoes.csv",
               ["cenario", "modo", "repeticao", "tempo_total_ms", "ida_e_volta_ms", "status_C",
                "tempo_C_ms", "hospedagens_encontradas", "mais_economica", "status_pesquisa"], brutos)

    resumo = []
    chaves = []
    for c, m, _, _ in linhas:
        if (c, m) not in chaves:
            chaves.append((c, m))
    for cenario, modo in chaves:
        rs = [r for c, m, _, r in linhas if c == cenario and m == modo and r["ok"]]
        if not rs:
            continue
        media, desvio, minimo, maximo = estatisticas([r["tempo_total_ms"] for r in rs])
        status_c = Counter(r["status_C"] for r in rs).most_common(1)[0][0]
        tempo_c = statistics.mean(r["tempo_C_ms"] for r in rs)
        mais = Counter(r["mais_economica"] for r in rs).most_common(1)[0][0]
        achadas = statistics.mean(r["resultados"] for r in rs)
        resumo.append([cenario, modo, len(rs), virgula(media), virgula(desvio), minimo, maximo,
                       status_c, virgula(tempo_c), curto(achadas), mais])
    cab = ["cenario", "modo", "repeticoes", "media_ms", "desvio_ms", "min_ms", "max_ms",
           "status_do_C", "tempo_do_C_ms", "hospedagens_encontradas", "mais_economica"]
    gravar_csv("exp5_resumo.csv", cab, resumo)
    texto = ("O fornecedor C tem atraso de 1,5 s. No último cenário, o processo do C é encerrado "
             f"{curto(INSTANTE_QUEDA)} s depois do início da pesquisa.\n\n" + tabela_md(cab, resumo))
    return "Experimento 5: indisponibilidade de um fornecedor", texto


# ---------- programa principal ----------

def main():
    os.makedirs(RESULTADOS, exist_ok=True)
    ocupadas = [p for p in [PORTA_AGREGADOR] + list(PORTAS.values()) if porta_aberta(p)]
    if ocupadas:
        print(f"As portas {ocupadas} já estão em uso. Feche os fornecedores e o agregador e tente de novo.")
        sys.exit(1)

    registro = os.path.join(RESULTADOS, "registro_tempos_experimentos.csv")
    if os.path.exists(registro):
        os.remove(registro)

    inicio = time.time()
    secoes = []
    try:
        subir_agregador()
        secoes.append(experimento_1_2())
        secoes.append(experimento_3())
        secoes.append(experimento_4())
        secoes.append(experimento_5())
    finally:
        for nome in list(processos):
            derrubar(nome)

    duracao = time.time() - inicio
    texto = "# Resultados dos experimentos\n\n"
    texto += (f"Executado em {datetime.now().strftime('%d/%m/%Y %H:%M')}, Python {sys.version.split()[0]}, "
              f"duração {duracao / 60:.1f} min{' (modo rápido)' if RAPIDO else ''}.\n"
              "Tempos em milissegundos. Média e desvio padrão amostral das repetições.\n\n")
    for titulo, conteudo in secoes:
        texto += f"## {titulo}\n\n{conteudo}\n"
    with open(os.path.join(RESULTADOS, "resultados.md"), "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
    print(f"\nConcluído em {duracao / 60:.1f} min. Tabelas gravadas em {RESULTADOS}", flush=True)


if __name__ == "__main__":
    main()
