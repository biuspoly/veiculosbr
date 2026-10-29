## R CMD check results

0 errors | 0 warnings | 1 note

* This is a new release. It replaces an unconfirmed submission of the same version made earlier today
  (29/10/2026) under another maintainer name and address, which were wrong; please disregard that one.

Checked with `R CMD check --as-cran` on Windows 11, R 4.6.1.

## Notes for the reviewers

* The documentation is in Brazilian Portuguese (`Language: pt-BR`): the package handles Brazilian vehicle
  plates, RENAVAM numbers and the Brazilian FIPE price table, and its users are Brazilian.
* Examples that query web services are wrapped in `\dontrun{}`. The FIPE catalogue API allows 500 requests
  per IP per day, the plate web page limits requests per IP, and the plate API allows 5 requests per month,
  so running them on check machines would spend those quotas. The tests never access the internet: they read
  recorded responses from `tests/testthat/casos/respostas`.
* Functions that access the internet stop with an informative, classed condition when a site is unavailable
  or refuses a request (HTTP 403/429), and then make no further requests to that site for 10 minutes.
  Nothing is written to the user's file system.
* The data table `inst/extdata/faixas_uf.csv` is derived from Wikipedia (CC BY-SA 4.0); see
  `inst/COPYRIGHTS`.
