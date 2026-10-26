# veiculosbr

Dados de veículo brasileiros em **R** e em **Python**, com as mesmas funções, os mesmos nomes e os mesmos
resultados nas duas linguagens:

- **placa** antiga (ABC1234) e Mercosul (ABC1D23): conferir, formatar, converter nos dois sentidos e dizer o
  estado onde foi emplacada;
- **RENAVAM**: conferir o dígito;
- **chassi**: conferir e dizer o país, o fabricante e o ano-modelo;
- **tabela FIPE**: marcas, modelos, anos e preço;
- **FIPE pela placa**: o preço estimado a partir da placa, com **todos os candidatos** quando houver mais de
  um, cada um com a fonte e o grau de confiança.

> **O preço pela placa é uma estimativa e pode estar errado.** O nome do modelo no cadastro da placa raramente
> é igual ao da FIPE ("15.190 CRM 4X2" no cadastro, "15-190 E Constellation" e "15-190 E Worker" na FIPE).
> Por isso o pacote nunca escolhe um sozinho quando há dúvida: devolve todos, e cada resultado diz de onde
> veio.

## De onde vêm os dados

**Nada aqui é dado oficial do Senatran, do Detran ou da FIPE consultado direto na fonte.** Cada informação
vem de um lugar:

| Informação | Fonte | Atualização |
|---|---|---|
| Faixa de letras de cada estado (`placa_uf`) | Wikipédia em inglês, ["Vehicle registration plates of Brazil"](https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Brazil), que cita o Sinesp/Senatran | coletada em 26/10/2026; vem dentro do pacote |
| País e fabricante do chassi (`chassi_pais`, `chassi_fabricante`) | Wikipédia em inglês, ["Vehicle identification number"](https://en.wikipedia.org/wiki/Vehicle_identification_number) | coletada em 26/10/2026; vem dentro do pacote |
| Regras de placa, RENAVAM e chassi | as regras públicas de formato: Resolução Contran 780/2019 (placa Mercosul), módulo 11 (RENAVAM), norma ISO 3779 (chassi) | escritas no código |
| Tabela FIPE (`fipe_*`) | API pública do [Parallelum](https://fipe.parallelum.com.br), que repete a tabela de [veiculos.fipe.org.br](https://veiculos.fipe.org.br) | consulta na hora; cache de 7 dias |
| Veículo pela placa (`placa_consultar`) | a página pública de placa do [tabelafipebrasil.com](https://www.tabelafipebrasil.com); e, **só quando pedida**, a busca por placa do Parallelum | consulta na hora; cache de 30 dias |

O cadastro da placa vem de sites que não são oficiais: se estiver errado ou desatualizado lá, vem errado aqui.
A tabela de faixas por estado é a de janeiro de 2025; faixa distribuída depois disso dá "desconhecida" até a
tabela ser refeita (`ferramentas/gerar_tabelas.py`). Detalhes e licença das tabelas em
[dados/LEIAME.md](dados/LEIAME.md).

### Boa conduta com os sites

O pacote se identifica como robô (`veiculosbr/<versão>` e o endereço deste repositório), confere o
`robots.txt` antes de ler uma página, espera 3 segundos entre consultas ao mesmo site, guarda as respostas em
cache e, quando um site recusa (limite de consultas), fica 10 minutos sem consultá-lo. Sites que bloqueiam
robôs ou se protegem com desafio anti-robô (placafipe.com, keplaca.com) não são usados.

**É para consulta avulsa, não em massa.** O tabelafipebrasil.com limita as consultas de placa por endereço de
internet (em 26/10/2026, pouco mais de uma dezena de consultas numa tarde bastou para ele pedir uma pausa de
mais de uma hora). A busca por placa do Parallelum dá 5 consultas por **mês** sem token e 10 com o token gratuito, por
isso só entra quando pedida.

## Instalar

```r
# R (>= 4.1)
remotes::install_github("biuspoly/veiculosbr", subdir = "r")
```

```bash
# Python (>= 3.10)
pip install "git+https://github.com/biuspoly/veiculosbr#subdirectory=python"
```

## Usar

```r
library(veiculosbr)

placa_valida(c("ABC-1234", "ABC1D23", "AB12345"))   # TRUE TRUE FALSE
placa_para_mercosul("MUA5678")                      # "MUA5G78"
placa_uf("PIA1B11")                                 # "PI": emplacada no Piauí
renavam_valido("94613459057")                       # TRUE
chassi_fabricante("9BWZZZ377VT004251")              # "Volkswagen do Brasil"

fipe_preco("caminhoes", "515134-1", 2018)           # o preço de outubro/2026, com a fonte

resultado = fipe_por_placa("ABC1D23")
resultado$veiculo      # marca, modelo, ano, cidade... e de qual site veio
resultado$candidatos   # todos os códigos FIPE possíveis, com preço, confiança e semelhança
resultado$avisos       # sempre inclui o aviso de que pode estar errado
```

```python
import veiculosbr as vb

vb.placa_para_mercosul("MUA5678")          # 'MUA5G78'
vb.placa_uf("PIA1B11")                     # 'PI'
vb.fipe_preco("caminhoes", "515134-1", 2018)

resultado = vb.fipe_por_placa("ABC1D23")
for candidato in resultado.candidatos:
    print(candidato.codigo_fipe, candidato.modelo_fipe, candidato.preco, candidato.confianca)
print(resultado.avisos)
```

Pela linha de comando: `python -m veiculosbr ABC1D23` mostra tudo o que o pacote sabe da placa.

### A confiança de cada candidato

| Confiança | Quando |
|---|---|
| alta | a fonte da placa indicou um código FIPE só, e ele existe no catálogo no ano-modelo do veículo |
| media | a fonte indicou mais de um código, ou não deu para conferir no catálogo |
| baixa | a fonte não indicou código, e ele veio da busca por nome parecido no catálogo |

Na busca por nome parecido entram todos os modelos da marca, naquele ano, que ficam a até 0,15 da nota do
melhor (`semelhanca`, de 0 a 1). Sem o ano-modelo, só com o de fabricação, o pacote procura nos dois anos
possíveis (o veículo fabricado em 2017 pode ser modelo 2017 ou 2018).

### Variáveis de ambiente

| Variável | Para quê |
|---|---|
| `VEICULOSBR_FIPE_TOKEN` | o token gratuito de [fipe.api.br](https://fipe.api.br): aumenta o limite do Parallelum |
| `VEICULOSBR_CACHE` | outra pasta para o cache; `0` desliga |
| `VEICULOSBR_RESPOSTAS_GRAVADAS` | usada pelos testes: lê as respostas de uma pasta em vez de ir à internet |

## Como o repositório se organiza

```
casos/       os casos de teste, em JSON, que R e Python conferem (e as respostas gravadas dos sites)
dados/       as tabelas de referência (faixas por estado, país e fabricante do chassi)
ferramentas/ gerar_tabelas.py (refaz dados/ pela Wikipédia) e sincronizar.py (copia dados/ e casos/ para os pacotes)
r/           o pacote em R
python/      o pacote em Python
docs/        o plano e a origem do projeto
```

`dados/` e `casos/` são a fonte; cada pacote tem a sua cópia. Mudou um deles, rode
`python ferramentas/sincronizar.py`: um teste do Python acusa cópia esquecida.

Testes: `cd python && uv run pytest` e, no R, `R CMD build r` seguido de `R CMD check --as-cran`. Nenhum teste
vai à internet nem gasta cota: todos leem `casos/respostas/`.

## Licença

MIT. As tabelas de `dados/` derivam da Wikipédia (CC BY-SA 4.0): veja [dados/LEIAME.md](dados/LEIAME.md).
