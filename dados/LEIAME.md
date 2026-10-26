# As tabelas de referência

As três tabelas vêm da Wikipédia em inglês, coletadas em **26/10/2026** por `ferramentas/gerar_tabelas.py`
(que baixa o texto-fonte das páginas e refaz os arquivos). O conteúdo da Wikipédia é publicado sob a licença
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); estas tabelas são extraídas dele, com
atribuição às páginas abaixo.

| Arquivo | O que tem | Página de origem |
|---|---|---|
| `faixas_uf.csv` | as faixas de letras de placa de cada estado: `inicio` e `fim` (3 letras), `numero_min` e `numero_max` (só a série SAV é dividida pelo número: até 1000 é de SP, dali em diante do CE), `uf` e `sequencia` (a ordem em que o estado recebeu a faixa) | [Vehicle registration plates of Brazil](https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Brazil), seção "Vertical Distribution of Alphanumeric Combinations", que cita o Sinesp/Senatran (atualizada em janeiro de 2025) |
| `pais_chassi.csv` | o país pelos 2 primeiros caracteres do chassi (ou pelo 1º, quando o país tem a letra inteira), já em português | [Vehicle identification number](https://en.wikipedia.org/wiki/Vehicle_identification_number), seção "Country or region codes" |
| `fabricante_chassi.csv` | o fabricante pelos 3 primeiros caracteres, só os com fábrica no Brasil, com o nome como a página escreve (em inglês) | [Vehicle identification number](https://en.wikipedia.org/wiki/Vehicle_identification_number), seção "List of many WMIs" |

Conferido na coleta: 240 faixas, os 27 estados, nenhuma faixa sobreposta a outra; as placas de teste de
26/10/2026 (do Piauí, da Paraíba e de Alagoas) caíram no estado que o tabelafipebrasil.com informa como "emitida
originalmente".

Para atualizar: `python ferramentas/gerar_tabelas.py`, depois `python ferramentas/sincronizar.py`, depois a data
acima e a do README.
