# Fornecedor de hospedagens (servidor TCP).
# Uso: python fornecedor.py <letra> <porta> [atraso em segundos]
# Exemplo: python fornecedor.py A 5001 0.5

import json
import socket
import sys
import threading
import time
import unicodedata
from datetime import datetime

from dados_fornecedores import BASE

HOST = "127.0.0.1"


def normalizar(texto):
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    return sem_acento.strip().lower()


def resposta_erro(fonte, mensagem):
    return {"fonte": fonte, "status": "erro", "mensagem": mensagem}


def montar_resposta(texto, letra, atraso):
    fonte = f"Fornecedor {letra}"

    try:
        pedido = json.loads(texto)
    except json.JSONDecodeError:
        return resposta_erro(fonte, "pedido não é um JSON válido")
    if not isinstance(pedido, dict):
        return resposta_erro(fonte, "pedido não é um JSON válido")

    if pedido.get("operacao") != "consultar":
        return resposta_erro(fonte, "operação desconhecida")

    destino = pedido.get("destino")
    if not isinstance(destino, str) or destino.strip() == "":
        return resposta_erro(fonte, "destino inválido")

    hospedes = pedido.get("hospedes")
    if isinstance(hospedes, bool) or not isinstance(hospedes, int) or hospedes < 1:
        return resposta_erro(fonte, "hospedes deve ser um número inteiro maior ou igual a 1")

    try:
        checkin = datetime.strptime(pedido.get("checkin"), "%d/%m/%Y")
        checkout = datetime.strptime(pedido.get("checkout"), "%d/%m/%Y")
    except (ValueError, TypeError):
        return resposta_erro(fonte, "data inválida (use DD/MM/AAAA)")

    noites = (checkout - checkin).days
    if noites < 1:
        return resposta_erro(fonte, "checkout deve ser depois do checkin")

    # simula a demora do fornecedor para responder
    time.sleep(atraso)

    itens = BASE[letra].get(normalizar(destino), [])
    hospedagens = []
    for nome, tipo, estrelas, preco_diaria in itens:
        hospedagens.append({
            "nome": nome,
            "tipo": tipo,
            "estrelas": estrelas,
            "preco_diaria": preco_diaria,
            "preco_total": round(preco_diaria * noites, 2),
        })

    return {"fonte": fonte, "status": "sucesso", "hospedagens": hospedagens}


def ler_linha(conexao):
    # a mensagem termina no \n; o pedido pode chegar em pedaços
    dados = b""
    while b"\n" not in dados:
        pedaco = conexao.recv(1024)
        if not pedaco:
            break
        dados += pedaco
    return dados.split(b"\n")[0].decode("utf-8", errors="replace")


def atender(conexao, endereco, letra, atraso):
    try:
        conexao.settimeout(10)  # não ficar preso se o cliente não enviar nada
        texto = ler_linha(conexao)
        try:
            resposta = montar_resposta(texto, letra, atraso)
        except Exception as erro:
            print(f"[Fornecedor {letra}] erro interno: {erro!r}", flush=True)
            resposta = resposta_erro(f"Fornecedor {letra}", "erro interno no fornecedor")

        mensagem = json.dumps(resposta, ensure_ascii=False) + "\n"
        conexao.sendall(mensagem.encode("utf-8"))

        quantidade = len(resposta.get("hospedagens", []))
        print(f"[Fornecedor {letra}] {endereco[1]} -> status={resposta['status']}, "
              f"hospedagens={quantidade}", flush=True)
    except OSError as erro:
        print(f"[Fornecedor {letra}] falha na conexão: {erro}", flush=True)
    finally:
        conexao.close()


def main():
    if len(sys.argv) < 3:
        print("Uso: python fornecedor.py <letra A-D> <porta> [atraso em segundos]")
        sys.exit(1)

    letra = sys.argv[1].upper()
    if letra not in BASE:
        print("A letra deve ser A, B, C ou D.")
        sys.exit(1)

    try:
        porta = int(sys.argv[2])
        atraso = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    except ValueError:
        print("A porta deve ser um número inteiro e o atraso um número (ex.: 0.5).")
        sys.exit(1)

    if not 1 <= porta <= 65535:
        print("A porta deve estar entre 1 e 65535.")
        sys.exit(1)
    if not 0 <= atraso <= 60:
        print("O atraso deve estar entre 0 e 60 segundos.")
        sys.exit(1)

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        servidor.bind((HOST, porta))
    except OSError:
        print(f"Não foi possível usar a porta {porta}. Ela já está em uso?")
        sys.exit(1)
    servidor.listen()
    print(f"Fornecedor {letra} esperando na porta {porta} (atraso de {atraso} s)...", flush=True)

    try:
        while True:
            conexao, endereco = servidor.accept()
            # uma thread por conexão, para atender vários pedidos ao mesmo tempo
            threading.Thread(target=atender, args=(conexao, endereco, letra, atraso),
                             daemon=True).start()
    except KeyboardInterrupt:
        print(f"\nFornecedor {letra} encerrado.")
    finally:
        servidor.close()


if __name__ == "__main__":
    main()
