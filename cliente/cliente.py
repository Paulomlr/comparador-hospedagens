# Cliente de terminal do Comparador de Hospedagens.
# Uso: python cliente.py   (o agregador precisa estar em execução)
# Segue o protocolo descrito em docs/protocolo/protocolo.md

import json
import socket
import time
from datetime import datetime

HOST = "127.0.0.1"
PORTA = 5000
FORMATO_DATA = "%d/%m/%Y"

TEXTO_STATUS = {"indisponivel": "indisponível", "erro": "retornou erro"}


def ler_linha(conexao):
    # a mensagem termina no \n; pode chegar em pedaços
    dados = b""
    while b"\n" not in dados:
        pedaco = conexao.recv(4096)
        if not pedaco:
            break
        dados += pedaco
    return dados.split(b"\n")[0].decode("utf-8", errors="replace")


def formatar_reais(valor):
    # 1250.5 -> R$ 1.250,50
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def formatar_segundos(segundos):
    return f"{segundos:.2f}".replace(".", ",") + " s"


def perguntar_destino():
    while True:
        destino = input("Destino: ").strip()
        if destino:
            return destino
        print("Informe o destino.")


def perguntar_data(rotulo, depois_de=None):
    while True:
        texto = input(f"{rotulo} (DD/MM/AAAA): ").strip()
        try:
            data = datetime.strptime(texto, FORMATO_DATA)
        except ValueError:
            print("Data inválida. Use o formato DD/MM/AAAA, por exemplo 10/12/2026.")
            continue
        if depois_de is not None and data <= depois_de:
            print("O check-out deve ser depois do check-in.")
            continue
        return data


def perguntar_hospedes():
    while True:
        texto = input("Hóspedes: ").strip()
        if texto.isdecimal() and int(texto) >= 1:
            return int(texto)
        print("Informe um número inteiro maior ou igual a 1.")


def perguntar_modo():
    while True:
        opcao = input("Modo (1 = sequencial, 2 = concorrente): ").strip()
        if opcao == "1":
            return "sequencial"
        if opcao == "2":
            return "concorrente"
        print("Digite 1 ou 2.")


def montar_pedido():
    print()
    destino = perguntar_destino()
    checkin = perguntar_data("Check-in")
    checkout = perguntar_data("Check-out", depois_de=checkin)
    hospedes = perguntar_hospedes()
    modo = perguntar_modo()
    return {
        "operacao": "pesquisar",
        "destino": destino,
        "checkin": checkin.strftime(FORMATO_DATA),
        "checkout": checkout.strftime(FORMATO_DATA),
        "hospedes": hospedes,
        "modo": modo,
    }


def enviar_pesquisa(pedido):
    inicio = time.perf_counter()
    with socket.create_connection((HOST, PORTA), timeout=5) as conexao:
        conexao.settimeout(30)
        conexao.sendall((json.dumps(pedido, ensure_ascii=False) + "\n").encode("utf-8"))
        resposta = json.loads(ler_linha(conexao))
    return resposta, time.perf_counter() - inicio


def mostrar_resultado(pedido, resposta, ida_e_volta):
    print()
    if resposta.get("status") != "sucesso":
        print("Erro:", resposta.get("mensagem", "resposta inesperada do agregador"))
        return

    print(f"{pedido['destino']} | {pedido['checkin']} a {pedido['checkout']} | "
          f"{pedido['hospedes']} hóspede(s) | {resposta['modo']}")
    print()

    if not resposta["resultados"]:
        print("Nenhuma hospedagem encontrada para esse destino.")
    else:
        print(f"{'#':>2}  {'Hospedagem':<36} {'Tipo':<12} {'Estrelas':<9} {'Diária':<13} {'Total':<13}")
        mais = resposta["mais_economica"]
        for posicao, h in enumerate(resposta["resultados"], start=1):
            nome = f"{h['nome']} ({h['fonte']})"
            marca = ""
            if mais and h["fonte"] == mais["fonte"] and h["nome"] == mais["nome"]:
                marca = "   <- MAIS ECONÔMICA"
            print(f"{posicao:>2}  {nome:<36} {h['tipo']:<12} {h['estrelas']:<9} "
                  f"{formatar_reais(h['preco_diaria']):<13} {formatar_reais(h['preco_total']):<13}{marca}")

    print()
    for f in resposta["fornecedores"]:
        if f["status"] != "sucesso":
            print(f"{f['fonte']}: {TEXTO_STATUS.get(f['status'], f['status'])}")
    print(f"Tempo total do agregador: {formatar_segundos(resposta['tempo_total_ms'] / 1000)}")
    print(f"Tempo total (ida e volta): {formatar_segundos(ida_e_volta)}")


def mostrar_detalhes(resposta):
    print()
    for f in resposta["fornecedores"]:
        situacao = TEXTO_STATUS.get(f["status"], f["status"])
        if f["status"] == "sucesso":
            situacao = f"{f['quantidade']} hospedagem(ns)"
        print(f"{f['fonte']}: {situacao}, {formatar_segundos(f['tempo_ms'] / 1000)}")


def menu_final(resposta):
    # devolve True para uma nova pesquisa e False para sair
    pode_detalhar = resposta is not None and resposta.get("status") == "sucesso"
    while True:
        print()
        print("1 - Nova pesquisa")
        if pode_detalhar:
            print("2 - Ver tempo de cada fornecedor")
        print("0 - Sair")
        opcao = input("Opção: ").strip()
        if opcao == "1":
            return True
        if opcao == "0":
            return False
        if opcao == "2" and pode_detalhar:
            mostrar_detalhes(resposta)
        else:
            print("Opção inválida.")


def main():
    print("=== Comparador de Hospedagens ===")
    try:
        while True:
            pedido = montar_pedido()
            print("\nPesquisando...")
            resposta = None
            try:
                resposta, ida_e_volta = enviar_pesquisa(pedido)
                mostrar_resultado(pedido, resposta, ida_e_volta)
            except ConnectionRefusedError:
                print("\nNão foi possível conectar ao agregador. Ele está em execução?")
            except TimeoutError:
                print("\nO agregador demorou demais para responder.")
            except OSError as erro:
                print(f"\nFalha de comunicação com o agregador: {erro}")
            except ValueError:
                print("\nO agregador enviou uma resposta inválida.")
                resposta = None

            if not menu_final(resposta):
                break
    except (KeyboardInterrupt, EOFError):
        pass
    print("\nEncerrado.")


if __name__ == "__main__":
    main()
