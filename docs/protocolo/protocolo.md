# Protocolo de comunicação - Comparador de Hospedagens

## 1. Componentes e portas

O sistema tem três tipos de programa:

- Cliente: o usuário informa a pesquisa e vê o resultado.
- Agregador: recebe a pesquisa do cliente, consulta os fornecedores, junta e ordena os resultados.
- Fornecedor: servidor com uma base simulada de hospedagens, que responde às consultas do agregador.

Todos rodam na mesma máquina (127.0.0.1), cada um em uma porta TCP:

| Programa | Porta |
|---|---|
| Agregador | 5000 |
| Fornecedor A | 5001 |
| Fornecedor B | 5002 |
| Fornecedor C | 5003 |
| Fornecedor D | 5004 |

Existem duas conversas:

1. Cliente -> Agregador, operação `pesquisar`.
2. Agregador -> Fornecedor, operação `consultar`.

## 2. Regras gerais

- A comunicação usa sockets TCP.
- As mensagens são JSON, codificadas em UTF-8.
- Cada mensagem é um JSON em uma única linha, terminada por `\n`. Quem recebe lê até encontrar o `\n`.
- Datas no formato `DD/MM/AAAA`, com o ano de 4 dígitos (exemplo: `10/12/2026`).
- Valores em reais com ponto decimal dentro das mensagens (exemplo: `250.00`). A vírgula (`R$ 250,00`) só é usada pelo cliente na hora de exibir.
- Tempos em milissegundos, como número inteiro. O cliente converte para segundos na hora de exibir.
- Todo pedido tem o campo `operacao`. Toda resposta tem o campo `status`.

## 3. Cliente -> Agregador

### 3.1 Pedido

```json
{
  "operacao": "pesquisar",
  "destino": "Rio de Janeiro",
  "checkin": "10/12/2026",
  "checkout": "15/12/2026",
  "hospedes": 2,
  "modo": "concorrente"
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| operacao | texto | Sempre `"pesquisar"` |
| destino | texto | Cidade de destino |
| checkin | texto | Data de entrada |
| checkout | texto | Data de saída, depois do checkin |
| hospedes | inteiro | Quantidade de hóspedes, no mínimo 1 |
| modo | texto | `"sequencial"` ou `"concorrente"` |

### 3.2 Resposta de sucesso

```json
{
  "status": "sucesso",
  "modo": "concorrente",
  "tempo_total_ms": 2013,
  "resultados": [
    {"fonte": "Fornecedor B", "nome": "Hotel Sol", "tipo": "hotel", "estrelas": 3, "preco_diaria": 220.00, "preco_total": 1100.00},
    {"fonte": "Fornecedor A", "nome": "Pousada Mar", "tipo": "pousada", "estrelas": 3, "preco_diaria": 250.00, "preco_total": 1250.00},
    {"fonte": "Fornecedor A", "nome": "Hotel Centro", "tipo": "hotel", "estrelas": 4, "preco_diaria": 296.00, "preco_total": 1480.00},
    {"fonte": "Fornecedor D", "nome": "Resort Lagoa", "tipo": "resort", "estrelas": 5, "preco_diaria": 460.00, "preco_total": 2300.00}
  ],
  "mais_economica": {"fonte": "Fornecedor B", "nome": "Hotel Sol", "preco_total": 1100.00},
  "fornecedores": [
    {"fonte": "Fornecedor A", "status": "sucesso", "quantidade": 2, "tempo_ms": 1005},
    {"fonte": "Fornecedor B", "status": "sucesso", "quantidade": 1, "tempo_ms": 502},
    {"fonte": "Fornecedor C", "status": "indisponivel", "quantidade": 0, "tempo_ms": 3},
    {"fonte": "Fornecedor D", "status": "sucesso", "quantidade": 1, "tempo_ms": 2010}
  ]
}
```

| Campo | Descrição |
|---|---|
| status | `"sucesso"` quando o pedido é válido e pelo menos um fornecedor respondeu |
| modo | Modo usado na pesquisa |
| tempo_total_ms | Tempo que o agregador levou para consultar os fornecedores: desde o início da primeira consulta até a chegada da última resposta. No modo sequencial é aproximadamente a soma dos tempos dos fornecedores e no concorrente é aproximadamente o maior deles |
| resultados | Todas as hospedagens encontradas, já ordenadas (seção 5) |
| mais_economica | A primeira hospedagem da lista ordenada |
| fornecedores | Uma linha para cada fornecedor consultado |

Campos de cada item de `fornecedores`:

| Campo | Descrição |
|---|---|
| fonte | Nome do fornecedor |
| status | `"sucesso"`, `"erro"` ou `"indisponivel"` |
| quantidade | Quantas hospedagens o fornecedor trouxe |
| tempo_ms | Tempo entre o envio da consulta ao fornecedor e a resposta (ou a falha) |

No exemplo, o Fornecedor C estava fora do ar, por isso não há hospedagens dele em `resultados`.

Se os fornecedores responderem mas nenhum tiver hospedagem para o destino, o `status` continua `"sucesso"`, `resultados` é uma lista vazia (`[]`) e `mais_economica` é `null`.

### 3.3 Resposta de erro

```json
{
  "status": "erro",
  "mensagem": "checkout deve ser depois do checkin"
}
```

O agregador responde com erro quando:

- o pedido não é um JSON válido;
- a operação é desconhecida;
- falta algum campo ou algum valor é inválido (data inexistente, checkout igual ou antes do checkin, hospedes menor que 1, modo desconhecido);
- nenhum fornecedor conseguiu responder.

## 4. Agregador -> Fornecedor

### 4.1 Pedido

```json
{
  "operacao": "consultar",
  "destino": "Rio de Janeiro",
  "checkin": "10/12/2026",
  "checkout": "15/12/2026",
  "hospedes": 2
}
```

Os campos têm o mesmo significado do pedido do cliente.

### 4.2 Resposta de sucesso

```json
{
  "fonte": "Fornecedor A",
  "status": "sucesso",
  "hospedagens": [
    {"nome": "Pousada Mar", "tipo": "pousada", "estrelas": 3, "preco_diaria": 250.00, "preco_total": 1250.00},
    {"nome": "Hotel Centro", "tipo": "hotel", "estrelas": 4, "preco_diaria": 296.00, "preco_total": 1480.00}
  ]
}
```

O fornecedor calcula o `preco_total`: preço da diária multiplicado pelo número de noites (data de checkout menos data de checkin).

Se o fornecedor não tiver hospedagem para o destino, responde `"status": "sucesso"` com `"hospedagens": []`.

### 4.3 Resposta de erro

```json
{
  "fonte": "Fornecedor A",
  "status": "erro",
  "mensagem": "pedido inválido"
}
```

## 5. Ordenação e opção mais econômica

O agregador ordena as hospedagens por:

1. `preco_total`, do menor para o maior;
2. em caso de empate no preço, por `estrelas`, da maior para a menor.

A opção mais econômica é a primeira da lista ordenada.

## 6. Tratamento de erros e falhas

| Situação | O que acontece |
|---|---|
| Pedido do cliente inválido | O agregador responde `status: "erro"` com `mensagem` |
| Fornecedor fora do ar (conexão recusada) | O agregador marca o fornecedor como `"indisponivel"` e continua com os outros |
| Fornecedor não responde em 3 segundos | O agregador marca o fornecedor como `"indisponivel"` e continua com os outros |
| Fornecedor responde com erro | O agregador marca o fornecedor como `"erro"` e continua com os outros |
| Fornecedor responde fora do formato do protocolo (JSON inválido ou hospedagens incompletas) | O agregador marca o fornecedor como `"erro"` e continua com os outros |
| Todos os fornecedores falham | O agregador responde `status: "erro"` |
| Cliente desconecta durante a pesquisa | O agregador descarta aquela pesquisa e continua atendendo os outros clientes |

## 7. Encerramento das conexões

- Cada pedido usa uma conexão nova: quem pede conecta, envia uma mensagem, recebe uma resposta e fecha a conexão.
- O agregador e os fornecedores continuam rodando e aceitando novas conexões.
- O cliente pode fazer várias pesquisas seguidas, abrindo uma conexão para cada uma.
