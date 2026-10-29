# A tabela de referência

`faixas_uf.csv` vem da Wikipédia em inglês, coletada em **26/10/2026** por `ferramentas/gerar_tabelas.py`
(que baixa o texto-fonte da página e refaz o arquivo). O conteúdo da Wikipédia é publicado sob a licença
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); esta tabela é extraída dele, com atribuição à
página de origem.

| Coluna | O que é |
|---|---|
| `inicio`, `fim` | as 3 letras do começo e do fim da faixa |
| `numero_min`, `numero_max` | só a série SAV é dividida pelo número: até 1000 é de SP, dali em diante do CE |
| `uf` | o estado que recebeu a faixa |
| `sequencia` | a ordem em que o estado recebeu a faixa |

Página de origem: [Vehicle registration plates of Brazil](https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Brazil),
seção "Vertical Distribution of Alphanumeric Combinations", que cita o Sinesp/Senatran (atualizada em janeiro
de 2025).

Conferido na coleta: 240 faixas, os 27 estados, nenhuma faixa sobreposta a outra; as placas reais consultadas
em 26/10/2026 (do Piauí, da Paraíba e de Alagoas) caíram no estado que o tabelafipebrasil.com informa como
"emitida originalmente".

Para atualizar: `python ferramentas/gerar_tabelas.py`, depois `python ferramentas/sincronizar.py`, depois a data
acima e a do README.
