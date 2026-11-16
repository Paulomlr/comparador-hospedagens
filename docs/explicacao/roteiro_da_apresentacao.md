# Roteiro da apresentação, slide por slide

Este arquivo explica cada slide como se fosse a apresentação: o que aparece, o que dizer (uma sugestão de fala, para adaptar com as suas palavras) e o que está por trás do slide, para você entender e não só repetir. As mesmas falas estão nas notas do orador do arquivo `apresentacao.pptx`.

O tempo total fica em torno de 18 minutos. O enunciado pede de 15 a 20, com os dois integrantes participando.

## Como o tempo se divide (sugestão do enunciado)

| Bloco | Tempo | Slides |
|---|---|---|
| Problema e objetivos | 2 min | 1 a 3 |
| Requisitos e modelagem | 4 min | 4 a 7 |
| Arquitetura e implementação | 4 min | 8 a 10 |
| Demonstração prática | 5 min | 11 |
| Experimentos e conclusões | 3 a 4 min | 12 a 17 |

Os números pequenos no canto dos slides (01, 02...) começam no segundo slide. Aqui usamos a posição do slide na apresentação.

---

## Slide 1: Capa (30 s)

**O que aparece:** o título "Comparador de Hospedagens" e os nomes do grupo.

**O que dizer:**
> Boa tarde. Nosso trabalho é o Comparador de Hospedagens, do Trabalho 1 de Sistemas Distribuídos. Vamos mostrar o problema, como especificamos e modelamos o sistema, como ele funciona por dentro, uma demonstração ao vivo e os resultados dos experimentos.

**Para entender:** é só a abertura. Já diga a ordem da apresentação, para quem assiste saber onde está.

---

## Slide 2: Introdução (1 min)

**O que aparece:** um texto curto sobre o problema.

**O que dizer:**
> Sites que comparam preços precisam consultar várias fontes. Como as consultas a fontes diferentes não dependem uma da outra, elas podem ser feitas ao mesmo tempo, e isso reduz o tempo de resposta. Nosso trabalho aplica essa ideia a um comparador de hospedagens, o Tema 4, usando sockets TCP e threads.

**Para entender:** imagine que você quer o preço de um quarto em quatro hotéis e só pode ligar para eles. Se ligar para um de cada vez, o tempo total é a soma das esperas. Se pedir ajuda a quatro pessoas para ligarem ao mesmo tempo, o tempo é o da ligação mais demorada. O trabalho inteiro mede essa diferença.

---

## Slide 3: Objetivo (1 min)

**O que aparece:** o objetivo do trabalho, ao lado de uma foto.

**O que dizer:**
> O objetivo é desenvolver uma aplicação cliente-servidor que consulta fornecedores independentes por sockets TCP, de forma sequencial e concorrente, e compara o tempo das duas formas. O usuário informa destino, período e hóspedes, e recebe as hospedagens ordenadas pelo preço, com a mais econômica em destaque.

**Para entender:**
- **Cliente-servidor:** um programa pede (o cliente) e outro atende (o servidor).
- **Sequencial:** pergunta a um fornecedor de cada vez. **Concorrente:** pergunta a todos ao mesmo tempo.
- Os dados dos hotéis são **simulados**, como o enunciado permite.

---

## Slide 4: Requisitos (1 min)

**O que aparece:** "12 RF e 7 RNF" e três quadros: 12 requisitos funcionais, 7 não funcionais e 8 critérios de aceitação.

**O que dizer:**
> O enunciado pede a especificação dos requisitos antes de programar. Fizemos 12 requisitos funcionais, que dizem o que o sistema faz, 7 não funcionais, que dizem como ele deve ser, e 8 critérios de aceitação, que dizem como verificar. Os mínimos exigidos eram 8 e 5. Os atores são o Usuário, que usa o sistema, e o Fornecedor, que é consultado.

**Para entender:**
- **Requisito funcional (RF):** algo que o sistema faz. Exemplo: "ordenar as hospedagens pelo preço".
- **Requisito não funcional (RNF):** uma qualidade ou restrição. Exemplo: "usar sockets TCP", "tratar falhas".
- **Critério de aceitação:** uma forma de provar que o requisito foi cumprido. Exemplo: "com um fornecedor desligado, a pesquisa termina e avisa qual falhou".

---

## Slide 5: Casos de uso (30 s)

**O que aparece:** o diagrama UML de casos de uso.

**O que dizer:**
> O Usuário pesquisa hospedagens e vê os resultados. O Fornecedor é um ator secundário: ele é consultado pelo agregador e não inicia nada. E toda pesquisa inclui a consulta aos fornecedores.

**Para entender como ler o diagrama:**
- Os bonecos são os **atores**. As elipses são os **casos de uso**: UC01 pesquisar, UC02 consultar fornecedores, UC03 visualizar resultados.
- As linhas simples ligam o ator ao caso de uso em que ele participa.
- A seta tracejada «include» significa "sempre usa": UC01 sempre inclui UC02 e UC03.

---

## Slide 6: Arquitetura (1 min)

**O que aparece:** o diagrama de arquitetura.

**O que dizer:**
> O cliente fala com o agregador, na porta 5000. O agregador consulta os quatro fornecedores, e cada um é um processo separado, com a sua porta, de 5001 a 5004. A comunicação é por TCP, com mensagens em JSON. Tudo roda na mesma máquina, o que o enunciado permite.

**Para entender:**
- **Porta:** o "ramal" onde cada programa atende.
- As setas de duas pontas mostram que o pedido e a resposta usam a mesma conexão.
- O agregador também grava os tempos em um arquivo de registro.
- As notas amarelas do diagrama dizem que o agregador usa uma thread por cliente e, no modo concorrente, uma thread por fornecedor.

**Se perguntarem "é distribuído se está tudo no mesmo computador?":** são processos independentes que só trocam mensagens pela rede, sem compartilhar memória. A distância física não é o que define um sistema distribuído. Não testamos em máquinas diferentes.

---

## Slide 7: Sequência (1 min)

**O que aparece:** o diagrama de sequência, com duas caixas grandes.

**O que dizer:**
> Esse diagrama mostra a operação principal, a pesquisa. Depois de validar o pedido, o agregador segue um de dois caminhos, conforme o modo. No concorrente, as quatro consultas partem juntas, uma por thread. No sequencial, cada uma só começa depois da resposta da anterior. Em seguida, ele junta, ordena, registra os tempos e responde ao cliente.

**Para entender como ler:**
- O tempo corre de cima para baixo. Cada coluna é um participante.
- A caixa **alt** significa "um ou outro": só um dos dois modos acontece.
- A caixa **par** significa "ao mesmo tempo": as quatro consultas correm em paralelo.
- É o diagrama que mostra a diferença entre os dois modos, o assunto do trabalho.

---

## Slide 8: Protocolo (1 min)

**O que aparece:** seis pontos numerados sobre o protocolo.

**O que dizer:**
> O protocolo é o conjunto de regras da conversa entre os programas. As mensagens são JSON, cada uma em uma linha terminada por quebra de linha. Isso é necessário porque o TCP não separa as mensagens sozinho. Cada pedido usa uma conexão nova. São duas operações, pesquisar e consultar. Erros geram resposta com status erro e uma mensagem.

**Para entender:**
- **JSON:** texto em formato "campo: valor".
- **O `\n`:** é o "câmbio" da conversa. O programa que recebe lê até achar o `\n`, e aí sabe que a mensagem terminou.
- **Uma conexão por pedido:** conecta, envia, recebe e fecha. É mais simples e deixa cada pesquisa independente das outras.
- O documento completo está em `docs/protocolo`.

---

## Slide 9: Implementação (1 min)

**O que aparece:** três quadros: 3 programas independentes, 4 fornecedores nas portas 5001 a 5004, 4 threads por pesquisa concorrente.

**O que dizer:**
> Implementamos em Python, usando só a biblioteca padrão. São três programas: fornecedor, agregador e cliente. O fornecedor é o mesmo programa rodando quatro vezes, cada vez com uma letra, uma porta e um atraso. O agregador atende cada cliente em uma thread e, no modo concorrente, usa uma thread para cada fornecedor.

**Para entender o que cada um faz:**
- **Fornecedor:** valida o pedido, espera o atraso simulado, procura os hotéis do destino, calcula o preço total (diária vezes noites) e responde.
- **Agregador:** valida, consulta, junta, ordena e registra os tempos. Se um fornecedor falha, só ele é marcado e a pesquisa continua.
- Existe um teste automático com 41 verificações, todas aprovadas.

---

## Slide 10: Consulta concorrente (1 min)

**O que aparece:** um trecho de código à esquerda e três explicações à direita.

**O que dizer:**
> Aqui está a concorrência. Para cada fornecedor criamos uma thread e iniciamos todas. Depois chamamos o join em cada uma, que espera ela terminar. Cada thread guarda o resultado na posição do seu fornecedor, então não precisamos de trava, e a ordem dos resultados não depende de quem responde primeiro.

**Para entender o código, linha a linha:**
- `resultados = [...]`: uma lista com um "lugar" para cada fornecedor.
- O `for` cria uma `Thread` para cada fornecedor, com a função `consultar_e_guardar`, e dá `start()`.
- O segundo `for` chama `join()` em todas: o programa só continua quando as quatro terminarem.
- É como em Java: criar `Thread`, `start()` em todas e `join()` em cada uma.
- O código do slide é um trecho **simplificado** do arquivo real.

---

## Slide 11: Demonstração (5 min)

**O que aparece:** o roteiro em seis passos.

**Antes de começar:** feche qualquer fornecedor ou agregador que esteja aberto. Abra um terminal na pasta do projeto. Digite os comandos no terminal, sem usar o botão de executar do VS Code para o segundo programa em diante.

| Passo | O que fazer | O que mostrar e dizer |
|---|---|---|
| 1 | Rodar `iniciar_fornecedores.bat`, depois `python agregador\agregador.py` e, em outro terminal, `python cliente\cliente.py` | "Aqui estão os quatro fornecedores, cada um em uma janela, o agregador e o cliente" |
| 2 | Pesquisar Rio de Janeiro, 10/12/2026 a 15/12/2026, 2 hóspedes, modo 2 | Leva cerca de 2 s. A mais econômica é o Hostel Lapa, R$ 600,00. "O tempo é o do fornecedor mais lento" |
| 3 | Repetir no modo 1 | Leva cerca de 5 s, com os mesmos resultados. "Aqui os tempos se somam" |
| 4 | Digitar uma data como 31/02/2026 ou 0 hóspedes | O cliente avisa e pergunta de novo |
| 5 | Fechar a janela do fornecedor C e pesquisar | Aparece "Fornecedor C: indisponível". A pesquisa continua, e a mais econômica passa a ser o Hotel Sol, R$ 1.100,00 |
| 6 | Abrir `agregador/registro_tempos.csv` | Uma linha por pesquisa, com o modo e o tempo de cada fornecedor |

**Dica:** se algo der errado na demonstração, mantenha a calma e diga o que esperava ver. O teste automático (`python testes\teste_sistema.py`) mostra que o sistema funciona.

---

## Slide 12: Experimentos (30 s)

**O que aparece:** seis pontos sobre os experimentos.

**O que dizer:**
> Fizemos os cinco experimentos do enunciado, todos com repetições. Um programa automatizou tudo: ele abre e fecha os processos, muda os atrasos, dispara as pesquisas e grava as tabelas. Cada série começa com uma pesquisa de aquecimento, que é descartada. A execução completa levou cerca de 9 minutos.

**Para entender:**

| Experimento | O que testa | Repetições |
|---|---|---|
| 1 e 2 | Sequencial e concorrente, com atrasos de 0,5, 1, 1,5 e 2 s | 10 cada |
| 3 | Atraso de 0,5 a 2,5 s nos quatro fornecedores | 5 |
| 4 | 1, 5, 10 e 20 clientes ao mesmo tempo | 3 |
| 5 | Fornecedor C desligado antes e durante a pesquisa | 5 |

**Aquecimento:** a primeira pesquisa costuma ser um pouco mais lenta por detalhes do sistema, então ela é feita e descartada para não distorcer a média.

---

## Slide 13: Resultados 1 (1 min)

**O que aparece:** um gráfico de barras em "escada" e em paralelo, com os tempos dos quatro fornecedores.

**O que dizer:**
> No sequencial, as consultas aparecem em escada, uma depois da outra, e o total é a soma: 5,06 segundos. No concorrente, as quatro começam juntas e o total é o do mais lento, o fornecedor D: 2,02 segundos. O concorrente foi 2,51 vezes mais rápido, próximo do valor teórico de 2,5.

**Para entender:**
- O 2,5 teórico vem de 5,0 s (soma dos atrasos) dividido por 2,0 s (o maior atraso).
- O desvio padrão foi de 13 ms e 6 ms: as medições são estáveis.
- As barras mostram quando cada fornecedor foi consultado: no sequencial, cada um começa onde o anterior termina.

---

## Slide 14: Latência e clientes (1 min)

**O que aparece:** dois gráficos lado a lado.

**O que dizer:**
> À esquerda, o experimento 3. O sequencial cresce em quatro vezes o atraso dos fornecedores e o concorrente, uma vez. Com atraso de 2 segundos, são 8,07 contra 2,02. A vantagem aumenta quanto mais lentos são os fornecedores. À direita, o experimento 4: de 1 a 20 clientes ao mesmo tempo, o tempo por cliente não piorou, em nenhum dos modos.

**Para entender:**
- No gráfico da esquerda, as linhas tracejadas são o valor teórico (quatro vezes o atraso e uma vez o atraso). As medidas ficam praticamente em cima delas.
- No da direita, as linhas são quase retas: com 20 clientes, cada um esperou o mesmo que esperaria sozinho.
- **Limite honesto:** não chegamos ao limite do sistema com 20 clientes, então não sabemos onde ele começaria a piorar.

---

## Slide 15: Falhas (1 min)

**O que aparece:** um gráfico de barras com três cenários e três pontos numerados.

**O que dizer:**
> No experimento 5, desligamos o fornecedor C antes e durante a pesquisa. O sistema não parou: o agregador marcou o C como indisponível e continuou com os outros três, devolvendo seis hospedagens em vez de oito. No concorrente, o tempo quase não mudou. No sequencial, subiu cerca de meio segundo. E o mais importante: a falha mudou o resultado, a opção mais barata passou de R$ 600 para R$ 1.100.

**Para entender:**
- No concorrente, o tempo continua sendo o do mais lento (o D), então perder o C não muda o total.
- No sequencial, o aumento de 0,5 s veio de o agregador levar cerca de 2 s para perceber que a conexão com o C foi recusada, contra 1,5 s que o C levaria para responder. Isso foi observado no Windows, e a causa não foi verificada em outro sistema.
- O achado principal não é o tempo, e sim que uma falha **altera a resposta**. Por isso a resposta do sistema informa quais fornecedores não responderam.

---

## Slide 16: Conclusão (1 min)

**O que aparece:** seis pontos.

**O que dizer:**
> Sobre o multithreading, a consulta concorrente reduziu o tempo ao do fornecedor mais lento: de 5,06 para 2,02 segundos. O ganho cresce com o atraso e se manteve com 20 clientes. A falha de um fornecedor foi isolada, mas pode mudar o resultado. O custo é mais complexidade e mais recursos por pesquisa, e só vale quando a tarefa é dominada pela espera. Os limites: uma única máquina, um agregador só e uma lista fixa de fornecedores.

**Para entender por que ajuda:** cada consulta passa quase todo o tempo esperando a resposta pela rede, e não calculando. Em Python, o interpretador libera o bloqueio global (GIL) durante essa espera, então as threads esperam juntas. Se a tarefa fosse de cálculo pesado, o ganho seria bem menor, mas isso não foi medido.

**Trabalhos futuros (se perguntarem):** máquinas diferentes, replicar o agregador, descoberta de fornecedores, novas tentativas e cache.

---

## Slide 17: Obrigado e perguntas

**O que aparece:** "Obrigado".

**Respostas prontas para as perguntas mais prováveis:**

| Pergunta | Resposta |
|---|---|
| Está tudo no mesmo computador, é distribuído? | São processos independentes que só trocam mensagens. O enunciado permite a mesma máquina e simulamos a latência. Não testamos em máquinas diferentes |
| E se o agregador cair? | O sistema para. Ele é um ponto único de falha |
| Como o agregador acha os fornecedores? | Por uma lista fixa de endereços no código |
| Por que 3 segundos de timeout? | É uma escolha, para não travar esperando um fornecedor lento. Vale por operação de rede |
| Threads escalam? | Uma thread por conexão atendeu 20 clientes. Para cargas maiores, um conjunto limitado de threads ou entrada e saída assíncrona |
| Os dados são reais? | São simulados, como o enunciado permite |
| Vocês testaram de outra forma, com atrasos aleatórios? | Não. Foi uma ideia que ficou como trabalho futuro |

**Dica final:** responder com franqueza o que o sistema **não** faz passa mais segurança do que tentar escondê-lo.
