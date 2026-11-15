# Documento de Requisitos - Comparador de Hospedagens

Disciplina: Sistemas Distribuídos
Tema 4: Comparador de Hospedagens

## 1. Descrição do problema

Quem procura hospedagem precisa consultar vários fornecedores, cada um em um lugar diferente, para comparar preços. Se essas consultas forem feitas uma depois da outra, o tempo total é a soma do tempo de cada fornecedor. Como as consultas são independentes entre si, elas podem ser feitas ao mesmo tempo, e o tempo total passa a ser aproximadamente o do fornecedor mais lento.

## 2. Objetivo do sistema

Desenvolver uma aplicação cliente-servidor que consulte fornecedores de hospedagem independentes, junte os resultados, ordene pelo valor e identifique a opção mais econômica. O sistema deve permitir consultar os fornecedores de forma sequencial e de forma concorrente, para comparar o tempo de cada estratégia.

## 3. Escopo

O sistema contém:

- um cliente, executado no terminal, onde o usuário informa a pesquisa;
- um agregador, que recebe a pesquisa, consulta os fornecedores e devolve o resultado consolidado;
- quatro fornecedores independentes, com dados de hospedagem simulados;
- consulta sequencial e consulta concorrente;
- atendimento de vários clientes ao mesmo tempo;
- registro do tempo de execução das pesquisas;
- tratamento de falhas de comunicação e de fornecedores indisponíveis;
- experimentos de desempenho comparando as estratégias.

O sistema não faz reserva, pagamento, cadastro de usuários nem integração com sistemas reais de hospedagem.

## 4. Atores

| Ator | Tipo | Descrição |
|---|---|---|
| Usuário | Primário | Pessoa que usa o cliente para pesquisar hospedagens |
| Fornecedor de hospedagem | Secundário | Serviço independente (A, B, C e D) consultado pelo agregador. Cada um tem sua base simulada de hospedagens |

## 5. Requisitos funcionais

| Código | Requisito |
|---|---|
| RF01 | O sistema deve permitir que o usuário informe destino, data de check-in, data de check-out e quantidade de hóspedes. |
| RF02 | O sistema deve permitir que o usuário escolha o modo da consulta: sequencial ou concorrente. |
| RF03 | O sistema deve validar os dados da pesquisa e informar o erro ao usuário quando forem inválidos. |
| RF04 | O sistema deve consultar quatro fornecedores de hospedagem independentes. |
| RF05 | O sistema deve permitir consultas sequenciais, em que os fornecedores são consultados um após o outro. |
| RF06 | O sistema deve permitir consultas concorrentes, em que todos os fornecedores são consultados ao mesmo tempo. |
| RF07 | O sistema deve apresentar as hospedagens encontradas com fornecedor, nome, tipo, estrelas, preço da diária e preço total. |
| RF08 | O sistema deve ordenar as hospedagens pelo preço total, do menor para o maior, usando a quantidade de estrelas (maior primeiro) como desempate. |
| RF09 | O sistema deve identificar e destacar a opção mais econômica. |
| RF10 | O sistema deve exibir ao usuário o tempo total de cada pesquisa. |
| RF11 | O sistema deve registrar em arquivo o tempo total e o tempo de cada fornecedor em cada pesquisa. |
| RF12 | O sistema deve continuar a pesquisa quando um fornecedor falhar, apresentando os resultados dos demais e informando qual fornecedor ficou indisponível. |

## 6. Requisitos não funcionais

| Código | Requisito |
|---|---|
| RNF01 | A comunicação entre cliente, agregador e fornecedores deve utilizar sockets TCP reais. |
| RNF02 | A estratégia concorrente deve utilizar threads. |
| RNF03 | O agregador deve atender múltiplos clientes simultaneamente. |
| RNF04 | Cada fornecedor deve executar como um processo independente, em uma porta TCP própria. |
| RNF05 | A comunicação deve seguir o protocolo de aplicação documentado, com mensagens JSON. |
| RNF06 | O sistema deve tratar falhas de comunicação (conexão recusada, tempo esgotado de 3 segundos por fornecedor e desconexão do cliente) sem interromper o funcionamento do agregador. |
| RNF07 | O sistema deve permitir experimentos de desempenho, com atraso configurável em cada fornecedor. |

## 7. Restrições

- A implementação é feita em Python.
- Os dados de hospedagem são simulados.
- Todos os componentes executam na mesma máquina (127.0.0.1), em portas TCP distintas.
- São no mínimo quatro fornecedores.

## 8. Casos de uso

| Código | Caso de uso | Ator | Requisitos |
|---|---|---|---|
| UC01 | Pesquisar hospedagens | Usuário | RF01, RF02, RF03, RF11 |
| UC02 | Consultar fornecedores | Fornecedor de hospedagem | RF04, RF05, RF06, RF12 |
| UC03 | Visualizar resultados | Usuário | RF07, RF08, RF09, RF10 |

O caso de uso UC01 inclui UC02 e UC03.

## 9. Critérios de aceitação

| Código | Critério |
|---|---|
| CA01 | Em uma pesquisa válida, o sistema apresenta as hospedagens ordenadas pelo preço total e destaca a mais econômica (RF07, RF08, RF09). |
| CA02 | Com atrasos diferentes nos fornecedores, o tempo da consulta concorrente fica próximo ao do fornecedor mais lento e o da sequencial fica próximo à soma dos tempos (RF05, RF06, RF10). |
| CA03 | Com um fornecedor desligado, a pesquisa termina, os resultados dos demais são exibidos e o fornecedor indisponível é informado (RF12, RNF06). |
| CA04 | Dois ou mais clientes pesquisando ao mesmo tempo recebem seus resultados corretos, sem que um bloqueie o outro (RNF03). |
| CA05 | Dados de pesquisa inválidos geram mensagem de erro e o agregador continua funcionando (RF03). |
| CA06 | Após cada pesquisa, o tempo total e o tempo de cada fornecedor ficam registrados em arquivo (RF11). |
| CA07 | Se um cliente se desconectar durante a pesquisa, o agregador continua atendendo os outros clientes (RNF06). |
| CA08 | Os quatro fornecedores executam como processos separados, em portas diferentes (RNF04). |
