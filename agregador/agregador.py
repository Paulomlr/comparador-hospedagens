# Agregador: recebe a pesquisa do cliente, consulta os fornecedores e devolve o resultado.
# Uso: python agregador.py
# Segue o protocolo descrito em docs/protocolo/protocolo.md

import csv
import json
import math
import os
import socket
import threading
import time
from datetime import datetime

HOST = "127.0.0.1"
PORTA = 5000
TIMEOUT = 3  # segundos de espera por cada fornecedor

# Endereços dos fornecedores (para usar outras máquinas, basta trocar aqui)
FORNECEDORES = [
    ("Fornecedor A", "127.0.0.1", 5001),
    ("Fornecedor B", "127.0.0.1", 5002),
    ("Fornecedor C", "127.0.0.1", 5003),
    ("Fornecedor D", "127.0.0.1", 5004),
]

# os experimentos usam a variável REGISTRO_TEMPOS para gravar em outro arquivo
ARQUIVO_REGISTRO = os.environ.get("REGISTRO_TEMPOS") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "registro_tempos.csv")
trava_registro = threading.Lock()


def ler_linha(conexao):
    # a mensagem termina no \n; pode chegar em pedaços
    dados = b""
    while b"\n" not in dados:
        pedaco = conexao.recv(4096)
        if not pedaco:
            break
        dados += pedaco
    return dados.split(b"\n")[0].decode("utf-8", errors="replace")


def resposta_erro(mensagem):
    return {"status": "erro", "mensagem": mensagem}


def validar_pesquisa(pedido):
    # devolve a mensagem de erro, ou None se o pedido está válido
    if pedido.get("operacao") != "pesquisar":
        return "operação desconhecida"

    destino = pedido.get("destino")
    if not isinstance(destino, str) or destino.strip() == "":
        return "destino inválido"

    hospedes = pedido.get("hospedes")
    if isinstance(hospedes, bool) or not isinstance(hospedes, int) or hospedes < 1:
        return "hospedes deve ser um número inteiro maior ou igual a 1"

    try:
        checkin = datetime.strptime(pedido.get("checkin"), "%d/%m/%Y")
        checkout = datetime.strptime(pedido.get("checkout"), "%d/%m/%Y")
    except (ValueError, TypeError):
        return "data inválida (use DD/MM/AAAA)"
    if (checkout - checkin).days < 1:
        return "checkout deve ser depois do checkin"

    if pedido.get("modo") not in ("sequencial", "concorrente"):
        return "modo deve ser sequencial ou concorrente"

    return None


def eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool) and math.isfinite(valor)


def hospedagens_validas(hospedagens):
    # confere se a resposta do fornecedor tem o formato do protocolo
    if not isinstance(hospedagens, list):
        return False
    for h in hospedagens:
        if not isinstance(h, dict):
            return False
        if not isinstance(h.get("nome"), str) or not isinstance(h.get("tipo"), str):
            return False
        if isinstance(h.get("estrelas"), bool) or not isinstance(h.get("estrelas"), int):
            return False
        if not eh_numero(h.get("preco_diaria")) or not eh_numero(h.get("preco_total")):
            return False
    return True


def consultar_fornecedor(nome, host, porta, pedido):
    inicio = time.perf_counter()
    resultado = {"fonte": nome, "status": "indisponivel", "hospedagens": []}

    try:
        with socket.create_connection((host, porta), timeout=TIMEOUT) as conexao:
            mensagem = json.dumps(pedido, ensure_ascii=False) + "\n"
            conexao.sendall(mensagem.encode("utf-8"))
            resposta = json.loads(ler_linha(conexao))
        if not isinstance(resposta, dict):
            raise ValueError("resposta inválida")

        if resposta.get("status") == "sucesso":
            if not hospedagens_validas(resposta.get("hospedagens")):
                raise ValueError("hospedagens fora do formato do protocolo")
            resultado["status"] = "sucesso"
            resultado["hospedagens"] = resposta["hospedagens"]
        else:
            resultado["status"] = "erro"
    except OSError:
        resultado["status"] = "indisponivel"  # recusou a conexão ou não respondeu em 3 s
    except ValueError:
        resultado["status"] = "erro"  # respondeu algo fora do protocolo

    resultado["tempo_ms"] = round((time.perf_counter() - inicio) * 1000)
    return resultado


def consultar_sequencial(pedido):
    resultados = []
    for nome, host, porta in FORNECEDORES:
        resultados.append(consultar_fornecedor(nome, host, porta, pedido))
    return resultados


def consultar_e_guardar(resultados, posicao, nome, host, porta, pedido):
    resultados[posicao] = consultar_fornecedor(nome, host, porta, pedido)


def consultar_concorrente(pedido):
    # cada fornecedor tem seu lugar na lista, assim a ordem não depende de quem responde primeiro
    resultados = [{"fonte": nome, "status": "erro", "hospedagens": [], "tempo_ms": 0}
                  for nome, _, _ in FORNECEDORES]

    threads = []
    for posicao, (nome, host, porta) in enumerate(FORNECEDORES):
        thread = threading.Thread(target=consultar_e_guardar,
                                  args=(resultados, posicao, nome, host, porta, pedido))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()  # espera todas as consultas terminarem
    return resultados


ESTRATEGIAS = {
    "sequencial": consultar_sequencial,
    "concorrente": consultar_concorrente,
}


def consolidar(resultados):
    hospedagens = []
    fornecedores = []
    for r in resultados:
        for h in r["hospedagens"]:
            hospedagens.append({
                "fonte": r["fonte"],
                "nome": h["nome"],
                "tipo": h["tipo"],
                "estrelas": h["estrelas"],
                "preco_diaria": h["preco_diaria"],
                "preco_total": h["preco_total"],
            })
        fornecedores.append({
            "fonte": r["fonte"],
            "status": r["status"],
            "quantidade": len(r["hospedagens"]),
            "tempo_ms": r["tempo_ms"],
        })

    # menor preço primeiro; em empate, mais estrelas primeiro
    hospedagens.sort(key=lambda h: (h["preco_total"], -h["estrelas"]))

    mais_economica = None
    if hospedagens:
        primeira = hospedagens[0]
        mais_economica = {
            "fonte": primeira["fonte"],
            "nome": primeira["nome"],
            "preco_total": primeira["preco_total"],
        }
    return hospedagens, mais_economica, fornecedores


def registrar_tempos(modo, destino, total_ms, resultados):
    if destino.startswith(("=", "+", "-", "@", "\t", "\r")):
        destino = "'" + destino  # evita que o Excel trate o destino como fórmula
    linha = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), modo, destino, total_ms]
    linha += [r["tempo_ms"] for r in resultados]
    linha.append(sum(1 for r in resultados if r["status"] == "sucesso"))

    cabecalho = ["data_hora", "modo", "destino", "tempo_total_ms"]
    cabecalho += [f"tempo_{nome.split()[-1]}_ms" for nome, _, _ in FORNECEDORES]
    cabecalho.append("fornecedores_ok")

    try:
        with trava_registro:
            novo = not os.path.exists(ARQUIVO_REGISTRO)
            codificacao = "utf-8-sig" if novo else "utf-8"  # o Excel precisa disso para os acentos
            with open(ARQUIVO_REGISTRO, "a", newline="", encoding=codificacao) as arquivo:
                escritor = csv.writer(arquivo, delimiter=";")
                if novo:
                    escritor.writerow(cabecalho)
                escritor.writerow(linha)
    except OSError as erro:
        print(f"[Agregador] não foi possível gravar o registro: {erro}", flush=True)


def processar(texto):
    try:
        pedido = json.loads(texto)
    except json.JSONDecodeError:
        return resposta_erro("pedido não é um JSON válido")
    if not isinstance(pedido, dict):
        return resposta_erro("pedido não é um JSON válido")

    erro = validar_pesquisa(pedido)
    if erro:
        return resposta_erro(erro)

    modo = pedido["modo"]
    estrategia = ESTRATEGIAS[modo]

    consulta = {
        "operacao": "consultar",
        "destino": pedido["destino"],
        "checkin": pedido["checkin"],
        "checkout": pedido["checkout"],
        "hospedes": pedido["hospedes"],
    }

    inicio = time.perf_counter()
    resultados = estrategia(consulta)
    total_ms = round((time.perf_counter() - inicio) * 1000)

    registrar_tempos(modo, pedido["destino"], total_ms, resultados)
    ok = sum(1 for r in resultados if r["status"] == "sucesso")
    print(f"[Agregador] {modo} | {pedido['destino']} | total={total_ms} ms | "
          f"fornecedores ok={ok}/{len(resultados)}", flush=True)

    if ok == 0:
        return resposta_erro("nenhum fornecedor respondeu")

    hospedagens, mais_economica, fornecedores = consolidar(resultados)
    return {
        "status": "sucesso",
        "modo": modo,
        "tempo_total_ms": total_ms,
        "resultados": hospedagens,
        "mais_economica": mais_economica,
        "fornecedores": fornecedores,
    }


def atender(conexao):
    try:
        conexao.settimeout(10)  # não ficar preso se o cliente não enviar nada
        texto = ler_linha(conexao)
        try:
            resposta = processar(texto)
        except Exception as erro:
            print(f"[Agregador] erro interno: {erro!r}", flush=True)
            resposta = resposta_erro("erro interno no agregador")

        mensagem = json.dumps(resposta, ensure_ascii=False) + "\n"
        conexao.sendall(mensagem.encode("utf-8"))
    except OSError as erro:
        print(f"[Agregador] falha na conexão com o cliente: {erro}", flush=True)
    finally:
        conexao.close()


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        servidor.bind((HOST, PORTA))
    except OSError:
        print(f"Não foi possível usar a porta {PORTA}. Ela já está em uso?")
        return
    servidor.listen()
    print(f"Agregador esperando na porta {PORTA}...", flush=True)

    try:
        while True:
            conexao, _ = servidor.accept()
            # uma thread por cliente, para atender vários clientes ao mesmo tempo
            threading.Thread(target=atender, args=(conexao,), daemon=True).start()
    except KeyboardInterrupt:
        print("\nAgregador encerrado.")
    finally:
        servidor.close()


if __name__ == "__main__":
    main()
