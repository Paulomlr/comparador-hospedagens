# Comparador de Hospedagens

Trabalho 1 de Sistemas Distribuídos (UNIFESSPA, FACSI), Tema 4.

Aplicação cliente-servidor em Python que consulta fornecedores de hospedagem independentes por sockets TCP, de forma sequencial e de forma concorrente (com threads), e compara os tempos das duas estratégias. Os dados de hospedagem são simulados.

## Como funciona

```
Cliente(s) --TCP/JSON--> Agregador --TCP/JSON--> Fornecedor A (porta 5001)
                                             --> Fornecedor B (porta 5002)
                                             --> Fornecedor C (porta 5003)
                                             --> Fornecedor D (porta 5004)
```

- O **cliente** (terminal) pede destino, datas, número de hóspedes e o modo da consulta (sequencial ou concorrente).
- O **agregador** (porta 5000) valida o pedido, consulta os quatro fornecedores, junta as hospedagens, ordena pelo preço total (desempate por estrelas), aponta a mais econômica, mede os tempos e grava um registro.
- Cada **fornecedor** é um processo independente, com sua porta, sua base de hospedagens e um atraso configurável.

Cada pedido usa uma conexão nova. As mensagens são JSON em uma linha terminada por `\n`. O protocolo completo está em `docs/protocolo/protocolo.md`.

## Estrutura do projeto

```
agregador/
    agregador.py            agregador (porta 5000)
cliente/
    cliente.py              cliente de terminal
fornecedores/
    fornecedor.py           fornecedor (usado 4 vezes, com letra e porta diferentes)
    dados_fornecedores.py   hospedagens simuladas dos fornecedores A, B, C e D
experimentos/
    experimentos.py         experimentos 1 a 5 (gera as tabelas)
    graficos.py             gráficos a partir das tabelas
    resultados/             tabelas (.csv e .md) e gráficos (.png) gerados
testes/
    teste_sistema.py        teste automático do sistema
docs/
    requisitos/             documento de requisitos
    protocolo/              protocolo de comunicação
    modelagem/              diagramas (casos de uso, arquitetura e sequência)
iniciar_fornecedores.bat    abre os 4 fornecedores (Windows)
```

## Requisitos

- Python 3 (testado com Python 3.15.2 no Windows 11; não foi testado em outras versões).
- O sistema usa apenas a biblioteca padrão do Python.
- Só os gráficos precisam do matplotlib: `python -m pip install matplotlib`.

## Obter o código

```
git clone https://github.com/Paulomlr/comparador-hospedagens.git
cd comparador-hospedagens
```

## Como executar

Rode cada programa em um terminal diferente, sempre na pasta do projeto. Digite os comandos no terminal; não use o botão de executar do VS Code para o segundo programa em diante, porque ele interrompe o programa que já estava rodando no mesmo terminal.

**1. Fornecedores.** No Windows, dê dois cliques em `iniciar_fornecedores.bat` (ou rode `iniciar_fornecedores.bat` no terminal). Ele abre 4 janelas. Também dá para abrir cada um à mão, em 4 terminais (o último número é o atraso em segundos):

```
python fornecedores\fornecedor.py A 5001 0.5
python fornecedores\fornecedor.py B 5002 1
python fornecedores\fornecedor.py C 5003 1.5
python fornecedores\fornecedor.py D 5004 2
```

**2. Agregador:**

```
python agregador\agregador.py
```

**3. Cliente:**

```
python cliente\cliente.py
```

No Linux ou macOS, troque `\` por `/` nos caminhos e abra os fornecedores à mão.

Para encerrar qualquer programa, use `Ctrl+C` no terminal dele (ou feche a janela, no caso dos fornecedores).

| Programa | Porta |
|---|---|
| Agregador | 5000 |
| Fornecedor A | 5001 |
| Fornecedor B | 5002 |
| Fornecedor C | 5003 |
| Fornecedor D | 5004 |

## Como testar

### 1. Teste automático

Com todos os programas fechados, rode na pasta do projeto:

```
python testes\teste_sistema.py
```

O teste abre os fornecedores e o agregador sozinho, leva cerca de 30 segundos e mostra `OK` ou `FALHA` para cada verificação. Ele confere:

- o protocolo do fornecedor (resposta de sucesso, destino inexistente, pedidos inválidos);
- as pesquisas do agregador nos dois modos (ordenação, mais econômica, mesmos resultados, tempo sequencial próximo da soma e concorrente próximo do maior);
- os pedidos inválidos recusados pelo agregador;
- cinco clientes ao mesmo tempo e cliente que desconecta no meio;
- falhas: fornecedor desligado, fornecedor que responde lixo ou dados incompletos, todos desligados;
- o arquivo de registro de tempos.

Ao final aparece `TODAS AS VERIFICAÇÕES PASSARAM.` ou o número de falhas.

### 2. Roteiro manual (serve também para a demonstração)

Suba os fornecedores, o agregador e o cliente, como na seção anterior.

1. **Modo concorrente.** Pesquise Rio de Janeiro, check-in 10/12/2026, check-out 15/12/2026, 2 hóspedes, modo 2. O tempo deve ficar perto de 2 s (o fornecedor mais lento tem 2 s) e a mais econômica deve ser o Hostel Lapa, R$ 600,00.
2. **Modo sequencial.** Repita com o modo 1. O tempo deve ficar perto de 5 s (0,5 + 1 + 1,5 + 2) e os resultados são os mesmos.
3. **Dados inválidos.** Digite uma data como 31/02/2026, um check-out antes do check-in ou 0 hóspedes. O cliente avisa e pergunta de novo.
4. **Fornecedor fora do ar.** Feche a janela do fornecedor C e pesquise de novo. A tela mostra `Fornecedor C: indisponível`, a pesquisa continua com os outros três e a mais econômica passa a ser o Hotel Sol, R$ 1.100,00.
5. **Vários clientes.** Abra dois ou três terminais com o cliente e pesquise ao mesmo tempo no modo 2. Todos devem responder em cerca de 2 s.
6. **Agregador desligado.** Feche o agregador e pesquise. O cliente avisa que não conseguiu conectar.
7. **Registro de tempos.** Abra `agregador/registro_tempos.csv` (por exemplo no Excel). Há uma linha por pesquisa, com o modo, o tempo total e o tempo de cada fornecedor.

### 3. Experimentos

Com todos os programas fechados:

```
python experimentos\experimentos.py
python experimentos\graficos.py
```

O primeiro leva cerca de 10 minutos. Ele abre os fornecedores e o agregador sozinho, executa os experimentos 1 a 5 do enunciado com várias repetições e grava as tabelas em `experimentos/resultados/` (`resultados.md` reúne todas). O segundo gera os três gráficos (PNG) na mesma pasta e precisa do matplotlib. Para uma execução rápida só para testar, use `python experimentos\experimentos.py --rapido`. Durante a execução, evite usar o computador para outras tarefas pesadas, para não alterar os tempos medidos.

## Configurações

- **Atraso de um fornecedor:** terceiro argumento do `fornecedor.py`, em segundos (entre 0 e 60).
- **Tempo limite do agregador:** `TIMEOUT` em `agregador/agregador.py` (3 segundos por fornecedor).
- **Endereços dos fornecedores:** lista `FORNECEDORES` em `agregador/agregador.py`.
- **Hospedagens simuladas:** `fornecedores/dados_fornecedores.py`.
- **Registro de tempos:** `agregador/registro_tempos.csv`, separado por `;`, com as colunas `data_hora`, `modo`, `destino`, `tempo_total_ms`, `tempo_A_ms` a `tempo_D_ms` e `fornecedores_ok`.

## Onde alterar

| Para mudar | Onde |
|---|---|
| Hotéis e preços | `fornecedores/dados_fornecedores.py` |
| Porta ou atraso de um fornecedor | argumentos do `fornecedor.py` (e linhas do `iniciar_fornecedores.bat`) |
| Tempo limite por fornecedor | `TIMEOUT` em `agregador/agregador.py` |
| Regra de ordenação ou da opção mais econômica | função `consolidar` em `agregador/agregador.py` |
| Validação do pedido | `validar_pesquisa` em `agregador/agregador.py` e `montar_resposta` em `fornecedores/fornecedor.py` |
| Nova forma de consultar os fornecedores | nova função `consultar_...` registrada em `ESTRATEGIAS` no agregador (e o modo aceito em `validar_pesquisa` e no menu do cliente) |
| O que aparece na tela do cliente | `mostrar_resultado` e `mostrar_detalhes` em `cliente/cliente.py` |
| Formato das mensagens | `docs/protocolo/protocolo.md` e os três programas |

Para acrescentar um quinto fornecedor, são necessários: seus dados em `dados_fornecedores.py`, uma linha na lista `FORNECEDORES` do agregador e a mensagem de letra válida do `fornecedor.py` (hoje cita A a D). O teste automático e os experimentos assumem exatamente quatro fornecedores (A a D) e também precisam de ajuste.

## Como contribuir

1. Crie uma branch para a alteração.
2. Rode `python testes\teste_sistema.py` antes de enviar. Se mexer no agregador ou no fornecedor, rode também os experimentos de novo, porque as tabelas e os gráficos dependem do código.
3. Se a alteração mudar o comportamento, atualize o README e, quando for o caso, o protocolo (`docs/protocolo/`) e os requisitos (`docs/requisitos/`).
4. Não envie o arquivo `agregador/registro_tempos.csv` (ele é gerado ao usar o sistema e já está no `.gitignore`).
5. Abra um pull request ou avise o grupo.

## Observações

- Um fornecedor com atraso de 3 s ou mais é considerado indisponível pelo agregador (tempo limite). Nos experimentos, os atrasos ficam abaixo disso.
- No Windows, tentar conectar a um fornecedor desligado leva cerca de 2 s para falhar. Esse tempo aparece nas medições.
- Os destinos disponíveis na base simulada são Rio de Janeiro, São Paulo, Belém e Marabá. Outro destino devolve uma lista vazia.

## Documentos

- Requisitos: `docs/requisitos/requisitos.md`
- Protocolo de comunicação: `docs/protocolo/protocolo.md`
- Diagramas: `docs/modelagem/`

## Possíveis evoluções

Ideias para trabalhos futuros, que não fazem parte desta entrega: interface gráfica ou web para o cliente, cache dos resultados e adaptadores para fornecedores com formatos de mensagem diferentes.
