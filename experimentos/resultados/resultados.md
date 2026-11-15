# Resultados dos experimentos

Executado em 14/11/2026 23:44, Python 3.15.2, duração 9.0 min.
Tempos em milissegundos. Média e desvio padrão amostral das repetições.

## Experimentos 1 e 2: consulta sequencial e consulta concorrente

Atrasos dos fornecedores: A 0,5 s, B 1 s, C 1,5 s, D 2 s. Repetições por modo: 10 (mais uma de aquecimento, descartada).

| modo | repeticoes | media_ms | desvio_ms | min_ms | max_ms | soma_tempos_fornecedores_ms | maior_tempo_fornecedor_ms |
|---|---|---|---|---|---|---|---|
| sequencial | 10 | 5060,3 | 13,3 | 5038 | 5082 | 5060,1 | 2018,4 |
| concorrente | 10 | 2015,0 | 6,2 | 2004 | 2024 | 5033,8 | 2013,0 |

Ganho do concorrente (média sequencial / média concorrente): 2,51x

## Experimento 3: simulação de latência

Os quatro fornecedores usam o mesmo atraso em cada linha. Valor teórico: sequencial = 4 x atraso; concorrente = atraso.

| atraso_por_fornecedor_s | modo | repeticoes | media_ms | desvio_ms | min_ms | max_ms | teorico_ms |
|---|---|---|---|---|---|---|---|
| 0,50 | sequencial | 5 | 2065,4 | 8,3 | 2056 | 2074 | 2000 |
| 0,50 | concorrente | 5 | 516,6 | 1,5 | 514 | 518 | 500 |
| 1,00 | sequencial | 5 | 4062,4 | 6,5 | 4056 | 4072 | 4000 |
| 1,00 | concorrente | 5 | 1017,2 | 0,4 | 1017 | 1018 | 1000 |
| 1,50 | sequencial | 5 | 6074,6 | 9,4 | 6059 | 6084 | 6000 |
| 1,50 | concorrente | 5 | 1514,8 | 5,5 | 1505 | 1518 | 1500 |
| 2,00 | sequencial | 5 | 8068,0 | 13,7 | 8048 | 8084 | 8000 |
| 2,00 | concorrente | 5 | 2018,2 | 1,1 | 2017 | 2020 | 2000 |
| 2,50 | sequencial | 5 | 10067,4 | 17,9 | 10046 | 10087 | 10000 |
| 2,50 | concorrente | 5 | 2512,2 | 7,0 | 2504 | 2518 | 2500 |

## Experimento 4: vários clientes ao mesmo tempo

Atrasos dos fornecedores: iguais aos do experimento 1. Cada rodada dispara todos os clientes ao mesmo tempo. Tempos medidos pelo cliente (ida e volta).

| modo | clientes | repeticoes | media_por_cliente_ms | maior_tempo_ms | tempo_total_ms | pesquisas_com_falha |
|---|---|---|---|---|---|---|
| sequencial | 1 | 3 | 5077,7 | 5077,7 | 5079,3 | 0 |
| sequencial | 5 | 3 | 5062,7 | 5092,3 | 5094,7 | 0 |
| sequencial | 10 | 3 | 5043,3 | 5076,7 | 5080,0 | 0 |
| sequencial | 20 | 3 | 5044,9 | 5090,3 | 5095,7 | 0 |
| concorrente | 1 | 3 | 2025,3 | 2025,3 | 2026,3 | 0 |
| concorrente | 5 | 3 | 2019,4 | 2030,7 | 2032,3 | 0 |
| concorrente | 10 | 3 | 2018,0 | 2029,0 | 2031,0 | 0 |
| concorrente | 20 | 3 | 2017,0 | 2023,0 | 2025,3 | 0 |

## Experimento 5: indisponibilidade de um fornecedor

O fornecedor C tem atraso de 1,5 s. No último cenário, o processo do C é encerrado 1 s depois do início da pesquisa.

| cenario | modo | repeticoes | media_ms | desvio_ms | min_ms | max_ms | status_do_C | tempo_do_C_ms | hospedagens_encontradas | mais_economica |
|---|---|---|---|---|---|---|---|---|---|---|
| todos ativos | sequencial | 5 | 5064,0 | 5,9 | 5056 | 5071 | sucesso | 1512,4 | 8 | Hostel Lapa (Fornecedor C) R$ 600,00 |
| todos ativos | concorrente | 5 | 2012,6 | 7,0 | 2005 | 2019 | sucesso | 1508,2 | 8 | Hostel Lapa (Fornecedor C) R$ 600,00 |
| C desativado antes da pesquisa | sequencial | 5 | 5589,8 | 24,3 | 5560 | 5625 | indisponivel | 2042,8 | 6 | Hotel Sol (Fornecedor B) R$ 1.100,00 |
| C desativado antes da pesquisa | concorrente | 5 | 2037,6 | 13,9 | 2024 | 2061 | indisponivel | 2035,8 | 6 | Hotel Sol (Fornecedor B) R$ 1.100,00 |
| C desativado 1 s depois do início | sequencial | 5 | 5585,6 | 9,2 | 5579 | 5601 | indisponivel | 2037,0 | 6 | Hotel Sol (Fornecedor B) R$ 1.100,00 |
| C desativado 1 s depois do início | concorrente | 5 | 2009,6 | 6,3 | 2005 | 2017 | indisponivel | 986,2 | 6 | Hotel Sol (Fornecedor B) R$ 1.100,00 |

