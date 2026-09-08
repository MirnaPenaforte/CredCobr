# Layout esperado para importações

Documento de referência para a importação manual e para a futura view de ingestão. Os layouts foram verificados nas duas planilhas em Imports exemple em 26/08/2026.

## Regras gerais

- As linhas iniciais são metadados; o cabeçalho real ocorre na linha 7 da XLSX e na linha 6 da XLS.
- Datas devem ser interpretadas como datas, nunca como texto ou número serial do Excel.
- Valores monetários usam duas casas decimais e devem ser normalizados para Decimal.
- Identificadores devem ser convertidos para texto para preservar zeros à esquerda em futuras cargas.
- Linhas sem campos obrigatórios devem ser rejeitadas individualmente, sem interromper as demais.
- A identidade de um boleto é estado + empresa + número do documento + parcela.
- ATR é o atraso informado pela origem; o sistema também calcula o atraso corrente pela data de vencimento.
- A planilha XLS não possui estado ou empresa. Esses campos devem vir do contexto da carga e nunca ser inferidos do nome do cliente.

## Layout A — Boletos em aberto (XLSX)

Arquivo: Boletos em aberto SISTEMA.xlsx

- Aba: Relatorio 1
- Dimensão: 27.367 linhas × 17 colunas (A1:Q27367)
- Cabeçalho: linha 7
- Dados: linhas 8–27.367 (27.360 registros)
- Metadados: grupo na linha 1, estabelecimento na linha 3, emissão/agente na linha 4 e usuário/data na linha 5.

| Campo | Tipo/formato observado | Obrigatório | Uso e validação |
|---|---|---:|---|
| CLIENTE | Texto com código final entre parênteses, ex. NOME LTDA (18409) | Sim | Separar nome e código; código é o identificador |
| ENDEREÇO | Texto livre | Sim | Não vazio |
| FONE | Texto, ex. Fone: (87) 999911999 | Sim | Preservar e normalizar depois |
| CONTATO | Texto ou vazio | Não | Aceitar nulo |
| FANTASIA | Texto ou vazio | Não | Aceitar nulo |
| INFORMAÇÕES | Texto livre | Sim | Preservar integralmente |
| TÍTULO | Texto no padrão DP <número> <parcela> | Sim | Separar último token como parcela |
| EMISSÃO | Data Excel | Sim | Data válida |
| PRZ | Inteiro (7–182 observado) | Sim | Inteiro não negativo |
| VENCIM | Data Excel | Sim | Data válida para cálculo de atraso |
| VALOR | Decimal (3,65–27.373,87 observado) | Sim | Decimal >= 0 |
| SALDO | Decimal (3,65–27.373,87 observado) | Sim | Decimal >= 0 |
| ATR | Inteiro (0–19 observado) | Sim | Inteiro >= 0; preservar como atraso da fonte |
| J/D | Decimal | Sim | Decimal >= 0 |
| AGT | Inteiro (341 em todos os registros observados) | Sim | Inteiro |
| COMISSÃO | Decimal (0–522,80015 observado) | Sim | Decimal >= 0 |
| OBS.: | Texto ou vazio | Não | Aceitar nulo |

Resumo: 2.439 clientes distintos, 27.360 títulos distintos, emissão de 30/07/2026 a 25/08/2026 e vencimentos de 06/08/2026 a 15/02/2027.

## Layout B — Posição de cobrança (XLS)

Arquivo: RELÁTÓRIO DE POSIÇÃO DE COBRANÇA POR VENDEDOR - GRUPO CLIENTES.xls

- Aba: Sheet 1
- Dimensão: 8.669 linhas × 13 colunas
- Cabeçalho: linha 6
- Dados: linhas 7–8.669 (8.663 registros)
- Metadados: grupo na linha 1, estabelecimentos na linha 3, emissão/usuário na linha 4 e período/status na linha 5.

| Campo | Tipo/formato observado | Obrigatório | Uso e validação |
|---|---|---:|---|
| GRUPO | Texto, ex. AFEC(309) | Sim | Grupo econômico; não vazio |
| Cod_Cliente | Inteiro (27–18.702 observado) | Sim | Converter para texto; identificador do cliente |
| Num_Documento | Inteiro (213.581–1.979.242 observado) | Sim | Número do boleto; positivo |
| Par_Documento | Texto curto (A–P observado) | Sim | Parcela; não vazio |
| EMISSÃO | Data Excel | Sim | Data válida |
| C_Prazo | Inteiro (1–160 observado) | Sim | Prazo contratado; positivo |
| Dat_Vencimento | Data Excel | Sim | Vencimento usado nas faixas |
| Vlr_Documento | Decimal (1,69–11.831,80 observado) | Sim | Valor original; >= 0 |
| Vlr_Saldo | Decimal (1,69–11.831,80 observado) | Sim | Saldo em aberto; >= 0 |
| ATR | Inteiro (5–85 observado) | Sim | Dias de atraso da origem; >= 0 |
| TOT JUROS | Decimal (0,07–1.020,90 observado) | Sim | Juros totais; >= 0 |
| %JUR | Decimal percentual (0,2 ou 0,3) | Sim | Taxa da origem; >= 0 |
| SLD+JUR | Decimal (1,76–12.293,24 observado) | Sim | Saldo acrescido; validar relação com saldo e juros |

Resumo: 8.663 registros, 1.120 clientes, 184 grupos, 5.512 documentos e vencimentos de 01/06/2026 a 20/08/2026. Todos os campos estavam preenchidos e não havia valores negativos.

## Contrato normalizado

A view/importador deve converter ambos os formatos para:

customer_identifier, customer_name, economic_group, title_number, installment, company, state, original_amount, outstanding_amount, issued_at, due_date, source_overdue_days (ATR), interest_amount, source_reference.

### Layout C — visão BI atualizada

O coletor SQL detecta o esquema publicado e aceita tanto os nomes antigos quanto os aliases abaixo. Datas textuais seguem estritamente `MM/DD/YYYY` (SQL Server estilo 101).

| Coluna nova | Destino | Compatibilidade antiga |
|---|---|---|
| Dias_Atraso | source_overdue_days (somente referência) | Dias_Atraso |
| Dat_Vencimento | due_date | Dat_Vencimento |
| Dat_Emissao | issued_at | Dat_Emissao |
| Vlr_Documento | original_amount | Vlr_Documento |
| Per_Juros | interest_rate | Per_Juros |
| Ao_Dia | daily_interest_amount | opcional |
| Vlr_Jrs+Mult | interest_amount | Vlr_Jrs+Mult |
| Vlr_Atual | outstanding_amount e balance_with_interest | Vlr_Atual |
| Status_Documento | source_status | opcional |
| Cod_Documento | title_number e source_reference | Num_Documento / Cod_Documento |
| boleto_pacela | installment | Par_Documento |
| CNPJ | customer_identifier e customer.document | Cgc_Cpf |
| Razao_Social | customer.name | Razao_Social |
| Cidade | customer.city | opcional |
| UF | state | UF |
| Vendedor | seller | Vendedor |
| Cod_GrpCli | economic_group.source_code | Cod_GrpCli |
| Gp_Cliente | economic_group.name | Des_GrpCli |
| Cod_Agente | agent_code | Cod_Agente |
| Cod_EstOri | origin_establishment_code | Cod_EstOri |
| Estabecimento | company.name | Cod_Estabe |

`Dias_Atraso` é preservado para rastreabilidade, mas todas as métricas e faixas são calculadas pela diferença entre `due_date` e a data de referência. Um título vence somente quando `due_date < data_de_referência`; vencimentos no próprio dia permanecem em dia.

Mapeamento do Layout B:

- Cod_Cliente → customer_identifier; quando não houver nome, usar Cliente <código>.
- GRUPO → economic_group.
- Num_Documento → title_number.
- Par_Documento → installment.
- Dat_Vencimento → due_date.
- ATR → source_overdue_days.
- Vlr_Documento/Vlr_Saldo → original_amount/outstanding_amount.
- TOT JUROS → interest_amount.

## Critérios de rejeição

1. Rejeitar arquivo sem a aba esperada ou sem cabeçalhos obrigatórios.
2. Rejeitar linha com cliente, grupo, documento, parcela, data, valor ou saldo ausente.
3. Rejeitar datas inválidas e valores não numéricos/negativos.
4. Rejeitar estados fora de CE, BA e PE quando o estado estiver no contexto da carga.
5. Registrar linha, motivo e payload original em ImportRejection.
6. Detectar duplicidade pela identidade do boleto antes de persistir.
7. Calcular faixas pelo atraso corrente derivado de due_date e preservar ATR como referência da origem.
8. Para o Layout B, exigir state e company no contexto, pois não existem no arquivo.

## Validação realizada

- Layout A: 27.360/27.360 linhas válidas.
- Layout B: 8.663/8.663 linhas válidas estruturalmente.
- Layout B: estado e empresa ausentes no arquivo; devem ser fornecidos como metadados externos.
