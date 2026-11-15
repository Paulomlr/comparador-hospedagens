# Teste automático do sistema: sobe os fornecedores e o agregador, executa os cenários
# e mostra OK ou FALHA para cada verificação.
# Uso: python testes/teste_sistema.py   (leva cerca de 1 minuto)
# Feche os fornecedores, o agregador e o cliente antes de rodar.

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORNECEDOR = os.path.join(RAIZ, "fornecedores", "fornecedor.py")
AGREGADOR = os.path.join(RAIZ, "agregador", "agregador.py")

HOST = "127.0.0.1"
PORTA_AGREGADOR = 5000
PORTAS = {"A": 5001, "B": 5002, "C": 5003, "D": 5004}
ATRASOS = {"A": 0.2, "B": 0.4, "C": 0.6, "D": 0.8}  # soma 2,0 s; maior 0,8 s

processos = {}
falhas = 0


def verifica(nome, condicao, detalhe=""):
    global falhas
    if not condicao:
        falhas += 1
    print(("OK     " if condicao else "FALHA  ") + nome + (f"   [{detalhe}]" if not condicao and detalhe else ""))


def porta_aberta(porta):
    try:
        with socket.create_connection((HOST, porta), timeout=1):
            return True
    except OSError:
        return False


def esperar_porta(porta):
    fim = time.time() + 20
    while time.time() < fim:
        if porta_aberta(porta):
            return
        time.sleep(0.3)
    raise RuntimeError(f"a porta {porta} não abriu")


def subir(nome, argumentos, registro):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", REGISTRO_TEMPOS=registro)
    processos[nome] = subprocess.Popen([sys.executable] + argumentos, env=env,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def subir_fornecedor(letra, registro):
    subir(letra, [FORNECEDOR, letra, str(PORTAS[letra]), str(ATRASOS[letra])], registro)
    esperar_porta(PORTAS[letra])


def derrubar(nome):
    processo = processos.pop(nome, None)
    if processo is not None and processo.poll() is None:
        processo.kill()
        processo.wait()


def enviar(porta, mensagem_bytes, fechar_logo=False):
    # envia uma linha e devolve a resposta (dicionário), ou None se não houver resposta
    with socket.create_connection((HOST, porta), timeout=5) as conexao:
        conexao.settimeout(30)
        conexao.sendall(mensagem_bytes)
        if fechar_logo:
            return None
        dados = b""
        while b"\n" not in dados:
            pedaco = conexao.recv(4096)
            if not pedaco:
                break
            dados += pedaco
    return json.loads(dados.decode("utf-8")) if dados else None


def linha(dicionario):
    return (json.dumps(dicionario) + "\n").encode("utf-8")


def consulta(**campos):
    base = {"operacao": "consultar", "destino": "Rio de Janeiro", "checkin": "10/12/2026",
            "checkout": "15/12/2026", "hospedes": 2}
    base.update(campos)
    return linha(base)


def pesquisa(modo="concorrente", **campos):
    base = {"operacao": "pesquisar", "destino": "Rio de Janeiro", "checkin": "10/12/2026",
            "checkout": "15/12/2026", "hospedes": 2, "modo": modo}
    base.update(campos)
    inicio = time.perf_counter()
    resposta = enviar(PORTA_AGREGADOR, linha(base))
    return resposta, (time.perf_counter() - inicio) * 1000


def status_dos_fornecedores(resposta):
    return {f["fonte"][-1]: f["status"] for f in resposta["fornecedores"]}


def servidor_falso(resposta_bytes, parar):
    # faz o papel do fornecedor C, devolvendo sempre a mesma resposta
    servidor = socket.socket()
    servidor.bind((HOST, PORTAS["C"]))
    servidor.listen()
    servidor.settimeout(0.3)
    while not parar.is_set():
        try:
            conexao, _ = servidor.accept()
        except socket.timeout:
            continue
        try:
            conexao.settimeout(2)
            dados = b""
            while b"\n" not in dados:
                pedaco = conexao.recv(1024)
                if not pedaco:
                    break
                dados += pedaco
            conexao.sendall(resposta_bytes)
        except OSError:
            pass
        conexao.close()
    servidor.close()


def com_fornecedor_falso(resposta_bytes):
    parar = threading.Event()
    thread = threading.Thread(target=servidor_falso, args=(resposta_bytes, parar))
    thread.start()
    time.sleep(0.5)
    try:
        resposta, _ = pesquisa("concorrente")
    finally:
        parar.set()
        thread.join()
    return resposta


def testar_fornecedor():
    print("\n--- Fornecedor (consulta direta ao fornecedor C) ---")
    r = enviar(PORTAS["C"], consulta())
    verifica("pedido válido: status sucesso e fonte correta", r["status"] == "sucesso" and r["fonte"] == "Fornecedor C")
    campos = {"nome", "tipo", "estrelas", "preco_diaria", "preco_total"}
    verifica("cada hospedagem tem os 5 campos do protocolo", all(set(h) == campos for h in r["hospedagens"]))
    verifica("preço total = diária x 5 noites",
             all(abs(h["preco_total"] - 5 * h["preco_diaria"]) < 0.01 for h in r["hospedagens"]))

    r = enviar(PORTAS["C"], consulta(destino="marabá"))
    verifica("destino sem acento e em minúsculo é encontrado", len(r["hospedagens"]) == 2)
    r = enviar(PORTAS["C"], consulta(destino="Atlantida"))
    verifica("destino inexistente: sucesso com lista vazia", r["status"] == "sucesso" and r["hospedagens"] == [])

    invalidos = {
        "JSON inválido": b"isto nao e json\n",
        "operação desconhecida": consulta(operacao="apagar"),
        "hóspedes igual a zero": consulta(hospedes=0),
        "data inexistente": consulta(checkin="31/02/2026"),
        "checkout antes do checkin": consulta(checkin="15/12/2026", checkout="10/12/2026"),
    }
    for nome, mensagem in invalidos.items():
        r = enviar(PORTAS["C"], mensagem)
        verifica(f"pedido inválido recusado: {nome}", r["status"] == "erro" and "mensagem" in r)


def testar_agregador():
    print("\n--- Agregador: pesquisas válidas ---")
    conc, tempo_conc = pesquisa("concorrente")
    seq, tempo_seq = pesquisa("sequencial")
    verifica("pesquisa concorrente com sucesso e 8 hospedagens", conc["status"] == "sucesso" and len(conc["resultados"]) == 8)
    verifica("pesquisa sequencial com sucesso e 8 hospedagens", seq["status"] == "sucesso" and len(seq["resultados"]) == 8)

    precos = [(h["preco_total"], -h["estrelas"]) for h in conc["resultados"]]
    verifica("resultados ordenados por preço (desempate por estrelas)", precos == sorted(precos))
    primeira = conc["resultados"][0]
    mais = conc["mais_economica"]
    verifica("mais econômica é a primeira da lista",
             mais["nome"] == primeira["nome"] and mais["fonte"] == primeira["fonte"])
    verifica("mais econômica no Rio é o Hostel Lapa (R$ 600)", mais["nome"] == "Hostel Lapa" and mais["preco_total"] == 600)
    verifica("os dois modos devolvem os mesmos resultados", conc["resultados"] == seq["resultados"])

    soma = sum(f["tempo_ms"] for f in seq["fornecedores"])
    verifica("sequencial: tempo total é cerca da soma dos fornecedores", seq["tempo_total_ms"] >= 0.9 * soma,
             f"total {seq['tempo_total_ms']} ms, soma {soma} ms")
    maior = max(f["tempo_ms"] for f in conc["fornecedores"])
    verifica("concorrente: tempo total é cerca do maior fornecedor", conc["tempo_total_ms"] <= maior + 400,
             f"total {conc['tempo_total_ms']} ms, maior {maior} ms")
    verifica("concorrente é bem mais rápido que o sequencial", conc["tempo_total_ms"] < 0.7 * seq["tempo_total_ms"],
             f"{conc['tempo_total_ms']} ms contra {seq['tempo_total_ms']} ms")

    vazio, _ = pesquisa("concorrente", destino="Atlantida")
    verifica("destino sem hospedagem: sucesso, lista vazia e mais econômica nula",
             vazio["status"] == "sucesso" and vazio["resultados"] == [] and vazio["mais_economica"] is None)

    print("\n--- Agregador: pedidos inválidos ---")
    invalidos = {
        "checkout antes do checkin": {"checkin": "15/12/2026", "checkout": "10/12/2026"},
        "data inexistente": {"checkin": "31/02/2026"},
        "formato de data errado": {"checkin": "2026-12-10"},
        "hóspedes igual a zero": {"hospedes": 0},
        "hóspedes como texto": {"hospedes": "2"},
        "destino vazio": {"destino": "  "},
        "modo desconhecido": {"modo": "xpto"},
        "operação desconhecida": {"operacao": "apagar"},
    }
    for nome, campos in invalidos.items():
        r, _ = pesquisa(**campos)
        verifica(f"recusado: {nome}", r["status"] == "erro" and "mensagem" in r)
    r = enviar(PORTA_AGREGADOR, b"isto nao e json\n")
    verifica("recusado: JSON inválido", r["status"] == "erro")

    print("\n--- Agregador: vários clientes e cliente que desconecta ---")
    resultados = [None] * 5
    largada = threading.Barrier(5)

    def cliente(i):
        largada.wait()
        resultados[i] = pesquisa("concorrente")

    inicio = time.perf_counter()
    threads = [threading.Thread(target=cliente, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    parede = (time.perf_counter() - inicio) * 1000
    verifica("5 clientes ao mesmo tempo, todos com sucesso", all(r and r[0]["status"] == "sucesso" for r in resultados))
    verifica("5 clientes ao mesmo tempo levam o tempo de um só (não 5 vezes)", parede < 2 * tempo_conc + 1000,
             f"{parede:.0f} ms contra {tempo_conc:.0f} ms de um cliente")

    enviar(PORTA_AGREGADOR, linha({"operacao": "pesquisar", "destino": "Rio de Janeiro", "checkin": "10/12/2026",
                                   "checkout": "15/12/2026", "hospedes": 2, "modo": "sequencial"}), fechar_logo=True)
    r, _ = pesquisa("concorrente")
    verifica("cliente que desconecta no meio não afeta os outros", r["status"] == "sucesso")


def testar_falhas(registro):
    print("\n--- Agregador: falhas de fornecedores ---")
    derrubar("C")
    time.sleep(0.5)
    r, _ = pesquisa("concorrente")
    estados = status_dos_fornecedores(r)
    verifica("fornecedor C desligado: marcado como indisponível, os outros com sucesso",
             estados == {"A": "sucesso", "B": "sucesso", "C": "indisponivel", "D": "sucesso"}, str(estados))
    verifica("pesquisa continua com os outros (6 hospedagens)", r["status"] == "sucesso" and len(r["resultados"]) == 6)
    verifica("com o C desligado a mais econômica passa a ser o Hotel Sol", r["mais_economica"]["nome"] == "Hotel Sol")
    r, _ = pesquisa("sequencial")
    verifica("o mesmo vale no modo sequencial", status_dos_fornecedores(r)["C"] == "indisponivel" and len(r["resultados"]) == 6)

    r = com_fornecedor_falso(b"isto nao e json\n")
    verifica("fornecedor que responde texto solto: só ele fica com erro",
             status_dos_fornecedores(r) == {"A": "sucesso", "B": "sucesso", "C": "erro", "D": "sucesso"})
    incompleto = {"fonte": "Fornecedor C", "status": "sucesso", "hospedagens": [{"nome": "X"}]}
    r = com_fornecedor_falso(linha(incompleto))
    verifica("fornecedor que responde dados incompletos: só ele fica com erro, a pesquisa não cai",
             r["status"] == "sucesso" and status_dos_fornecedores(r)["C"] == "erro")

    for letra in "ABD":
        derrubar(letra)
    time.sleep(0.5)
    r, _ = pesquisa("concorrente")
    verifica("todos os fornecedores desligados: resposta de erro", r["status"] == "erro")

    print("\n--- Registro de tempos ---")
    with open(registro, encoding="utf-8-sig") as arquivo:
        linhas = arquivo.read().splitlines()
    verifica("o arquivo de registro foi criado com cabeçalho", linhas[0].startswith("data_hora;modo;destino;tempo_total_ms"))
    verifica("há uma linha por pesquisa que consultou fornecedores", len(linhas) - 1 >= 10, f"{len(linhas) - 1} linhas")


def main():
    ocupadas = [p for p in [PORTA_AGREGADOR] + list(PORTAS.values()) if porta_aberta(p)]
    if ocupadas:
        print(f"As portas {ocupadas} já estão em uso. Feche os programas do sistema e tente de novo.")
        sys.exit(1)

    pasta = tempfile.mkdtemp()
    registro = os.path.join(pasta, "registro_teste.csv")
    try:
        for letra in PORTAS:
            subir_fornecedor(letra, registro)
        subir("agregador", [AGREGADOR], registro)
        esperar_porta(PORTA_AGREGADOR)

        testar_fornecedor()
        testar_agregador()
        testar_falhas(registro)
    finally:
        for nome in list(processos):
            derrubar(nome)
        shutil.rmtree(pasta, ignore_errors=True)

    print()
    print("TODAS AS VERIFICAÇÕES PASSARAM." if falhas == 0 else f"{falhas} VERIFICAÇÃO(ÕES) COM FALHA.")
    sys.exit(0 if falhas == 0 else 1)


if __name__ == "__main__":
    main()
