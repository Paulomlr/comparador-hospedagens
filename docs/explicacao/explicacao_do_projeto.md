# Explicação do projeto (versão simples)

Este arquivo explica o projeto inteiro de forma direta, para estudar e para saber responder quando perguntarem. Não entra no detalhe de cada linha de código: explica o que cada peça faz e para que serve cada função.

## 1. O projeto em uma frase

É um comparador de hospedagens. Você diz o destino, as datas e o número de hóspedes, e o sistema pergunta a **quatro fornecedores** quanto cada um cobra, junta tudo, ordena do mais barato ao mais caro e mostra qual é a opção mais econômica. O objetivo do trabalho é comparar duas formas de perguntar aos fornecedores: **um de cada vez** (sequencial) e **todos ao mesmo tempo** (concorrente).

**Analogia.** Os fornecedores são quatro recepções de hotel que atendem telefone. O agregador é uma agência de viagens que liga para as quatro recepções e monta uma lista única. O cliente é você, que pede a lista para a agência.

## 2. Quem é quem

São **três programas** diferentes, mais os fornecedores (que são o mesmo programa rodando quatro vezes).

| Programa | Papel | Onde fica | Porta |
|---|---|---|---|
| Cliente | Você digita a pesquisa e vê o resultado (no terminal) | `cliente/cliente.py` | não escuta, só liga |
| Agregador | Recebe a pesquisa, pergunta aos fornecedores, junta e ordena | `agregador/agregador.py` | 5000 |
| Fornecedor A, B, C, D | Cada um tem seus hotéis e responde "quanto custa" | `fornecedores/fornecedor.py` | 5001, 5002, 5003, 5004 |

```
Cliente  ──►  Agregador  ──►  Fornecedor A (5001)
                          ──►  Fornecedor B (5002)
                          ──►  Fornecedor C (5003)
                          ──►  Fornecedor D (5004)
```

Cada um é um **processo separado** (você abre um terminal para cada). Eles só conversam por mensagens pela rede (TCP), nunca compartilham variáveis. Por isso o sistema é "distribuído", mesmo rodando no mesmo computador.

## 3. O que acontece em uma pesquisa

1. Você digita destino, check-in, check-out, hóspedes e o modo (sequencial ou concorrente) no **cliente**.
2. O cliente monta uma mensagem (um texto no formato JSON) e envia ao **agregador**.
3. O agregador confere se o pedido faz sentido. Se não fizer, responde com erro.
4. O agregador pergunta aos quatro **fornecedores**, de um dos dois jeitos (ver seção 4).
5. Cada fornecedor confere o pedido, espera o seu "atraso" (que simula a demora de um serviço real), procura os hotéis do destino e calcula o preço total (diária vezes o número de noites).
6. O agregador junta as respostas, ordena pelo preço total, marca a mais econômica, mede os tempos, grava uma linha no arquivo de registro e responde ao cliente.
7. O cliente mostra a tabela na tela.

Um exemplo de mensagem do cliente para o agregador:

```json
{"operacao": "pesquisar", "destino": "Rio de Janeiro", "checkin": "10/12/2026",
 "checkout": "15/12/2026", "hospedes": 2, "modo": "concorrente"}
```

## 4. O ponto principal: sequencial e concorrente

Suponha que os fornecedores demorem 0,5, 1, 1,5 e 2 segundos para responder.

- **Sequencial:** pergunta ao A, espera; pergunta ao B, espera; e assim por diante. O tempo é a **soma**: cerca de 5 segundos.
- **Concorrente:** cria uma **thread** (uma linha de trabalho) para cada fornecedor e pergunta a todos ao mesmo tempo. O tempo é o do **mais lento**: cerca de 2 segundos.

Isso funciona porque o agregador passa quase todo o tempo **esperando a rede**, e as esperas podem acontecer em paralelo. É a ideia do trabalho inteiro.

**Em Java:** é como criar quatro `Thread`, chamar `start()` em todas e depois `join()` em cada uma para esperar terminar.

## 5. Palavras que aparecem no código

| Palavra | O que é, de forma simples |
|---|---|
| Socket | O "telefone" de um programa. Serve para ligar para outro programa ou para esperar ligações |
| Porta | O "ramal" onde um programa atende (5000, 5001...) |
| TCP | Ligação confiável: as mensagens chegam inteiras e na ordem |
| JSON | Texto organizado em "campo: valor", usado para as mensagens |
| `\n` | O "fim de linha". Marca onde a mensagem termina, porque o TCP não separa mensagens sozinho |
| Thread | Uma linha de trabalho. Com várias, várias esperas acontecem juntas |
| Timeout | Tempo máximo de espera (aqui, 3 segundos por fornecedor) antes de desistir |
| Processo | Um programa rodando, com memória própria |

## 6. Python para quem vem de Java

O projeto **não tem classes**: só **funções** soltas. Cada `def` é como um método estático do Java. Mais algumas equivalências:

| Python | Java |
|---|---|
| `def nome(parametros):` | `static tipo nome(parametros)` |
| `dict` (`{"chave": valor}`) | `HashMap` / objeto JSON |
| lista de tuplas `[(a, b)]` | lista de pares |
| `try / except` | `try / catch` |
| `if __name__ == "__main__": main()` | `public static void main` |
| o recuo (indentação) | as chaves `{ }` |

## 7. Os arquivos e as funções (o "mapa")

### 7.1 `fornecedores/fornecedor.py` — o fornecedor

Atende uma consulta por conexão. É executado quatro vezes: `python fornecedor.py A 5001 0.5` (letra, porta, atraso).

| Função | O que faz |
|---|---|
| `main` | Lê a letra, a porta e o atraso; abre o socket na porta; fica esperando ligações. A cada ligação, cria uma thread para atender |
| `atender` | Cuida de **uma** ligação: lê o pedido, monta a resposta, envia e fecha. Se algo inesperado der errado, responde com erro |
| `ler_linha` | Lê da conexão até encontrar o `\n` (o fim da mensagem) |
| `montar_resposta` | O trabalho de verdade: confere o pedido, espera o atraso, busca os hotéis, calcula o preço total e devolve a resposta |
| `normalizar` | Tira acentos e maiúsculas do destino, para "Marabá", "MARABA" e "maraba" serem o mesmo |
| `resposta_erro` | Monta a resposta de erro, com o motivo |

### 7.2 `fornecedores/dados_fornecedores.py` — os hotéis

Só tem uma coisa: `BASE`, um dicionário com os hotéis de cada fornecedor, por destino (Rio de Janeiro, São Paulo, Belém e Marabá). Cada hotel tem nome, tipo, estrelas e preço da diária. É aqui que você muda hotéis e preços.

### 7.3 `agregador/agregador.py` — o agregador

O cérebro do sistema. Escuta na porta 5000. No começo do arquivo há as configurações: a porta, o `TIMEOUT` (3 segundos), a lista `FORNECEDORES` (endereços e portas) e o arquivo de registro.

| Função | O que faz |
|---|---|
| `main` | Abre a porta 5000 e espera clientes. A cada cliente, cria uma thread |
| `atender` | Cuida de **um** cliente: lê o pedido, chama `processar`, responde e fecha. Tem uma rede de segurança para erros inesperados |
| `processar` | Coordena tudo: lê o JSON, valida, escolhe o modo, mede o tempo, consulta, registra, junta e monta a resposta. Se nenhum fornecedor respondeu, devolve erro |
| `validar_pesquisa` | Confere o pedido do cliente: operação, destino, hóspedes, datas (o check-out tem que ser depois do check-in) e modo |
| `consultar_fornecedor` | Liga para **um** fornecedor, com tempo limite de 3 s. Classifica o resultado em "sucesso", "erro" ou "indisponivel" e mede quanto demorou |
| `hospedagens_validas`, `eh_numero` | Conferem se a resposta de um fornecedor tem o formato certo. Se vier quebrada, só aquele fornecedor é marcado como "erro" |
| `consultar_sequencial` | Chama `consultar_fornecedor` para A, depois B, C e D, um por vez |
| `consultar_concorrente` | Cria uma thread por fornecedor, inicia todas e espera todas terminarem |
| `consultar_e_guardar` | O que cada thread executa: consulta o fornecedor e guarda o resultado na posição dele |
| `ESTRATEGIAS` | Um dicionário que liga o nome do modo à função (`"sequencial"` → `consultar_sequencial`). Assim o agregador escolhe a forma sem vários `if` |
| `consolidar` | Junta as hospedagens de todos, ordena pelo preço total (empate: mais estrelas primeiro), escolhe a mais econômica e monta a lista de fornecedores com estado e tempo |
| `registrar_tempos` | Grava uma linha no arquivo CSV com o modo, o tempo total e o tempo de cada fornecedor. Usa uma "trava" porque várias pesquisas podem gravar ao mesmo tempo |
| `ler_linha`, `resposta_erro` | Iguais às do fornecedor |

### 7.4 `cliente/cliente.py` — o que você usa

Um programa de terminal que fica aberto e permite várias pesquisas seguidas.

| Função | O que faz |
|---|---|
| `main` | O laço principal: monta o pedido, envia, mostra o resultado e abre o menu final |
| `montar_pedido` | Pede os dados ao usuário (usando as funções abaixo) e monta a mensagem |
| `perguntar_destino`, `perguntar_data`, `perguntar_hospedes`, `perguntar_modo` | Cada uma faz uma pergunta e **repete** se a resposta for inválida |
| `enviar_pesquisa` | Conecta ao agregador, envia o JSON, lê a resposta e mede o tempo de ida e volta |
| `mostrar_resultado` | Desenha a tabela, destaca a mais econômica, avisa os fornecedores indisponíveis e mostra os tempos |
| `mostrar_detalhes` | Mostra o tempo de cada fornecedor (opção do menu) |
| `menu_final` | O menu: nova pesquisa, ver tempos ou sair |
| `formatar_reais`, `formatar_segundos` | Mostram `R$ 1.250,00` e `2,02 s` no padrão brasileiro. Dentro das mensagens o número vai com ponto; a vírgula é só para exibir |
| `ler_linha` | Igual às outras |

### 7.5 `experimentos/experimentos.py` — mede o sistema

Roda os 5 experimentos do enunciado sozinho e grava as tabelas. Abre e fecha os fornecedores e o agregador, muda os atrasos, dispara pesquisas e calcula média e desvio.

| Função | O que faz |
|---|---|
| `main` | Confere que as portas estão livres, sobe o agregador, roda os 5 experimentos e grava o `resultados.md` |
| `experimento_1_2` | Compara sequencial e concorrente (10 vezes cada) |
| `experimento_3` | Repete com atrasos de 0,5 a 2,5 s e compara com o valor teórico |
| `experimento_4` | Dispara 1, 5, 10 e 20 clientes ao mesmo tempo |
| `experimento_5` | Desliga o fornecedor C antes e durante a pesquisa |
| `clientes_simultaneos` | Dispara vários clientes juntos (usada pelo experimento 4) |
| `pesquisar` | Faz uma pesquisa, como se fosse um cliente |
| `configurar`, `subir_fornecedor`, `subir_agregador`, `derrubar` | Abrem e fecham os programas com os atrasos desejados |
| `porta_aberta`, `esperar_porta`, `ambiente` | Ajudam a saber se um programa já está pronto e preparam o ambiente |
| `estatisticas`, `gravar_csv`, `tabela_md`, `virgula`, `curto`, `valor` | Calculam média e desvio e formatam as tabelas |

### 7.6 `experimentos/graficos.py` — desenha os gráficos

Lê as tabelas geradas e cria os quatro gráficos (PNG). Funções: `grafico_comparacao`, `grafico_latencia`, `grafico_clientes` e `grafico_falhas`, mais `ler`, `numero` e `salvar` como apoio. Precisa do matplotlib.

### 7.7 `testes/teste_sistema.py` — confere que tudo funciona

Abre o sistema e faz 41 verificações, mostrando OK ou FALHA. `testar_fornecedor`, `testar_agregador` e `testar_falhas` são os três grupos de testes; o resto (`verifica`, `subir`, `enviar`, `pesquisa`, `servidor_falso`...) é apoio. O `servidor_falso` simula um fornecedor que responde lixo, para ver se o agregador aguenta.

### 7.8 `iniciar_fornecedores.bat`

Abre os quatro fornecedores de uma vez, cada um em uma janela, com atrasos de 0,5, 1, 1,5 e 2 segundos.

## 8. Quando algo dá errado

O sistema foi feito para **não parar** quando uma parte falha:

| Situação | O que acontece |
|---|---|
| Pedido inválido (data errada, 0 hóspedes...) | O cliente avisa na hora; o agregador também recusa com mensagem |
| Fornecedor desligado | É marcado como "indisponivel", e a pesquisa continua com os outros |
| Fornecedor demora mais de 3 s | Também "indisponivel" |
| Fornecedor responde algo quebrado | Marcado como "erro", e a pesquisa continua |
| Todos os fornecedores falham | O agregador responde com erro |
| Cliente fecha no meio | O agregador não é afetado e atende os outros |
| Agregador desligado | O cliente avisa que não conseguiu conectar |

## 9. Por que foi feito assim

- **Um processo por fornecedor, cada um em uma porta:** o enunciado pede serviços independentes e permite portas diferentes na mesma máquina.
- **Uma conexão por pedido:** mais simples, e cada pesquisa é independente das outras.
- **Uma thread por conexão (no agregador e nos fornecedores):** para atender vários clientes ao mesmo tempo sem um esperar o outro.
- **Resultados guardados na posição de cada fornecedor:** assim a ordem final não depende de quem respondeu primeiro, e não precisa de trava.
- **Desempate por estrelas:** deixa o resultado sempre igual, mesmo no modo concorrente.
- **Dados simulados:** o enunciado permite.

## 10. O que os experimentos mostraram

| Experimento | Resultado |
|---|---|
| 1 e 2 | Sequencial 5,06 s; concorrente 2,02 s (2,51 vezes mais rápido) |
| 3 | O sequencial cresce em 4 vezes o atraso; o concorrente, em 1 vez |
| 4 | De 1 a 20 clientes ao mesmo tempo, o tempo por cliente não piorou |
| 5 | Com o fornecedor C desligado a pesquisa continua, e a mais barata muda de R$ 600 para R$ 1.100 |

A conclusão sobre multithreading: o tempo passa a ser o do serviço mais lento, o ganho cresce com a lentidão dos fornecedores, e a falha de um fornecedor fica isolada. O custo é mais complexidade e mais recursos.

## 11. Como rodar (três comandos)

Cada um em um terminal, na pasta do projeto:

```
iniciar_fornecedores.bat
python agregador\agregador.py
python cliente\cliente.py
```

Para testar tudo de uma vez: `python testes\teste_sistema.py`. Para refazer os experimentos: `python experimentos\experimentos.py`.

## 12. Perguntas que o professor pode fazer

| Pergunta | Resposta curta |
|---|---|
| É distribuído se está tudo no mesmo computador? | São processos independentes que só trocam mensagens. O enunciado permite a mesma máquina, e a latência foi simulada. Não foi testado em máquinas diferentes |
| Onde está a concorrência? | Em `consultar_concorrente`: uma thread por fornecedor, e o `join` espera todas |
| E se o agregador cair? | O sistema para: ele é um ponto único de falha |
| Como o agregador acha os fornecedores? | Por uma lista fixa de endereços no código |
| Por que 3 segundos de timeout? | Escolha para não travar esperando um fornecedor lento |
| Quantos clientes aguenta? | Testamos até 20 sem piorar. O limite não foi encontrado |
| Os dados são reais? | São simulados, como o enunciado permite |
