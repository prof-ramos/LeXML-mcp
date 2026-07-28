# PRD v2.0 — LexML MCP
## Estabilização do núcleo SRU/MCP

| Campo | Valor |
|---|---|
| Produto | LexML MCP |
| Versão do produto | v2.0 |
| Versão do documento | 2.0.0 |
| Status | Pronto para implementação |
| Data | 27 de julho de 2026 |
| Escopo da release | Núcleo Python/MCP para SRU, resolução de URN e `explain` |
| Transporte da release | `stdio` |
| Perfil de implantação | Local, monousuário e sem serviços auxiliares obrigatórios |

---

## 1. Resumo executivo

O **LexML MCP** é um servidor MCP em Python destinado a disponibilizar capacidades do LexML Brasil para agentes e clientes compatíveis com o Model Context Protocol.

O MVP já possui três operações centrais:

- pesquisa no acervo por SRU/CQL;
- resolução de URN LexML;
- consulta da operação SRU `explain`.

A principal limitação observada é que o endpoint público do LexML pode devolver uma página HTML de verificação de segurança do Senado em lugar do XML SRU esperado. Além disso, o MVP ainda precisa de contratos estruturados, parsing XML seguro, normalização sem perda silenciosa, tratamento consistente de erros, testes determinísticos e documentação alinhada ao comportamento real.

Esta versão reduz deliberadamente o escopo do PRD anterior. A v2.0 não tentará integrar parser, linker, renderer DOCX, workers JVM, containers auxiliares ou transporte remoto. Seu objetivo é transformar o núcleo existente em uma base confiável, segura, auditável e compatível com clientes MCP por `stdio`.

Parser, linker, renderer, recursos binários, Streamable HTTP, autenticação e multi-tenancy permanecem na visão de produto, mas serão tratados em releases posteriores, condicionados a investigação técnica e validação dos artefatos oficiais.

---

## 2. Estado atual e premissas

### 2.1 Estado documentado do MVP

Segundo os materiais fornecidos, o projeto possui uma implementação funcional em Python, baseada no SDK oficial `mcp` e em `FastMCP`, que:

- monta chamadas SRU `searchRetrieve`;
- aceita consultas CQL;
- utiliza `startRecord`, `maximumRecords` e `recordSchema`;
- tenta converter respostas XML em estruturas Python/JSON;
- resolve URNs LexML para URLs públicas;
- consulta `operation=explain`;
- preserva informações de diagnóstico quando recebe conteúdo inesperado;
- pode receber HTML de verificação de segurança em vez de XML SRU.

### 2.2 Nomenclatura das tools

A informação operacional mais recente do projeto identifica como nomes canônicos:

- `lexml_search`;
- `lexml_resolve_urn`;
- `lexml_explain`.

Documentação anterior utiliza variações como:

- `search_lexml`;
- `resolve_lexml_urn`;
- `explain_lexml`;
- `search_acervo_lexml`;
- `explain_acervo`.

A auditoria inicial deverá confirmar quais nomes estão efetivamente registrados e quais já foram publicados para usuários.

**Decisão da v2.0:**

1. os nomes canônicos serão `lexml_search`, `lexml_resolve_urn` e `lexml_explain`;
2. qualquer nome alternativo comprovadamente já exposto deverá ser preservado como alias de compatibilidade durante a série v2.x;
3. nenhum alias novo será criado apenas porque apareceu em documentação preliminar;
4. a depreciação de aliases deverá ser documentada e coberta por testes.

### 2.3 Limite da informação jurídica

Nesta release, o produto trabalha principalmente com pesquisa, metadados, identificadores e resolução de endereços.

O sistema não deve presumir que:

- um registro contém o inteiro teor do documento;
- uma URL resolvida corresponde a uma cópia oficial;
- uma norma está vigente;
- uma norma está consolidada;
- o resultado mais recente é o juridicamente aplicável;
- um identificador prova autenticidade, integridade ou vigência;
- metadados substituem consulta à fonte oficial competente.

Quando essas informações não forem fornecidas de forma inequívoca pelo upstream, devem permanecer ausentes ou explicitamente desconhecidas.

---

## 3. Problema

O acervo LexML é valioso para pesquisa jurídica e legislativa, mas seu uso por agentes apresenta cinco problemas principais:

1. **interface técnica pouco amigável para agentes:** clientes precisam conhecer SRU, CQL, XML, namespaces e schemas;
2. **comportamento instável do upstream:** acessos automatizados podem receber HTML de verificação em vez do XML esperado;
3. **contratos inconsistentes:** o MVP ainda não possui modelos estáveis, versionados e documentados para todas as respostas;
4. **risco de perda de dados:** normalizações simplificadas podem sobrescrever campos repetidos ou ignorar extensões;
5. **risco jurídico e de segurança:** agentes podem tratar metadados como conteúdo oficial, processar XML hostil ou receber HTML externo como se fosse dado confiável.

A v2.0 deve resolver esses problemas sem ampliar o projeto para componentes ainda não validados.

---

## 4. Visão de produto

A visão de longo prazo é que o LexML MCP funcione como um gateway MCP organizado sobre capacidades do ecossistema LexML, com conectores isolados e contratos previsíveis.

A visão completa pode incluir futuramente:

- pesquisa no acervo via SRU/XML;
- recursos MCP associados a URNs e registros;
- parsing de documentos normativos;
- reconhecimento de remissões;
- renderização LexML para DOCX;
- artefatos binários temporários;
- transporte remoto autenticado.

A v2.0 implementará apenas o núcleo necessário para sustentar essa evolução:

- busca SRU;
- resolução de URN;
- `explain`;
- segurança;
- contratos;
- erros;
- testes;
- documentação;
- compatibilidade por `stdio`.

---

## 5. Objetivos da v2.0

### 5.1 Objetivo principal

Entregar uma versão confiável do núcleo SRU/MCP existente, preservando compatibilidade retroativa e tornando seu comportamento previsível diante de respostas válidas, vazias, parciais, hostis ou bloqueadas.

### 5.2 Objetivos específicos

- preservar as três tools existentes;
- padronizar contratos de entrada e saída;
- versionar schemas de resposta;
- validar parâmetros antes de acessar o upstream;
- utilizar parsing XML seguro;
- preservar campos repetidos e extensões desconhecidas;
- tratar diagnósticos SRU;
- usar `nextRecordPosition` na paginação;
- permitir sucesso parcial por registro;
- identificar HTML de challenge mesmo com HTTP 200;
- não devolver HTML bruto ao modelo por padrão;
- adotar timeouts e retries limitados;
- adicionar cache em memória com TTL e limite;
- produzir logs estruturados sem conteúdo sensível;
- oferecer testes determinísticos com fixtures locais;
- validar execução via `stdio`;
- alinhar README, contratos e comportamento real.

---

## 6. Não objetivos da v2.0

Não fazem parte desta release:

- parser de projeto de lei;
- parser LexML genérico;
- linker de remissões;
- renderer LexML para DOCX;
- armazenamento de arquivos;
- resources binários;
- worker JVM;
- serviços Java, Scala ou Haskell;
- execução de CLI oficial do LexML;
- containers auxiliares;
- Streamable HTTP;
- SSE legado;
- autenticação;
- autorização;
- multi-tenancy;
- Redis;
- banco de dados;
- cache persistente;
- interface gráfica;
- dashboard administrativo;
- publicação em PyPI;
- implantação automática em produção;
- alta disponibilidade;
- tracing distribuído;
- métricas externas ou stack de observabilidade dedicada;
- download automático de todas as páginas de resultados;
- automação de CAPTCHA ou de challenge JavaScript;
- rotação de IP ou técnicas destinadas a evitar controles do provedor;
- obtenção de inteiro teor quando essa capacidade não estiver comprovada.

---

## 7. Usuários-alvo

### 7.1 Primários

- desenvolvedores de agentes jurídicos;
- desenvolvedores de pipelines de pesquisa legislativa;
- profissionais de direito e compliance que utilizam clientes MCP;
- pesquisadores que precisam consultar metadados do LexML de forma estruturada.

### 7.2 Secundários

- mantenedores de servidores MCP internos;
- equipes que avaliam fontes jurídicas brasileiras para LLMs;
- desenvolvedores que pretendem integrar componentes adicionais do LexML em versões futuras.

---

## 8. Casos de uso da release

| ID | Caso de uso | Resultado esperado |
|---|---|---|
| UC-01 | Pesquisar o acervo com CQL | Lista estruturada de registros, total e posição da próxima página |
| UC-02 | Consultar uma página específica | Resultado correspondente a `start_record` e `maximum_records` |
| UC-03 | Receber zero resultados | Sucesso com lista vazia, sem erro artificial |
| UC-04 | Consultar capacidades SRU | Índices, schemas e metadados disponíveis em `explain` |
| UC-05 | Resolver uma URN | URL pública construída e, quando solicitado, verificada |
| UC-06 | Diagnosticar bloqueio | Erro `UPSTREAM_CHALLENGE` com dados sanitizados |
| UC-07 | Processar resposta parcialmente inválida | Registros válidos preservados e erros localizados |
| UC-08 | Operar sem acesso ao endpoint | Testes e desenvolvimento continuam possíveis com fixtures locais |
| UC-09 | Configurar cliente local | Servidor registrado e chamado por `stdio` |

---

## 9. Decisões de produto da v2.0

| ID | Decisão |
|---|---|
| D-01 | O perfil suportado é local e monousuário. |
| D-02 | O transporte obrigatório é `stdio`. |
| D-03 | O SDK deve ser o pacote oficial `mcp`; documentação do pacote independente `fastmcp` não será usada como referência de implementação. |
| D-04 | O cache será exclusivamente em memória. |
| D-05 | O servidor não fará paginação automática completa. |
| D-06 | Respostas brutas permanecerão desativadas por padrão. |
| D-07 | HTML de challenge será tratado como erro, nunca como sucesso. |
| D-08 | Parser, linker e renderer permanecerão no roadmap até validação técnica própria. |
| D-09 | O produto não afirmará oficialidade, vigência ou consolidação sem dado explícito da fonte. |
| D-10 | Contratos serão específicos por tool, sem envelope universal excessivamente verboso. |
| D-11 | Metadados técnicos internos serão preferencialmente enviados em `_meta` quando suportado. |
| D-12 | Mudanças incompatíveis de schema exigirão nova versão principal do contrato. |

---

## 10. Escopo funcional

### RF-01 — Registro e compatibilidade das tools

O servidor deve registrar como ferramentas canônicas:

- `lexml_search`;
- `lexml_resolve_urn`;
- `lexml_explain`.

A implementação deve:

- preservar parâmetros públicos existentes;
- manter aliases que a auditoria comprovar terem sido publicados;
- marcar aliases como deprecated na documentação, quando aplicável;
- garantir que alias e nome canônico usem a mesma implementação interna;
- evitar duplicação de lógica;
- incluir testes de contrato para cada nome suportado.

Quando o SDK permitir, as tools devem ser anotadas como:

- somente leitura;
- não destrutivas;
- idempotentes para os mesmos parâmetros e estado do upstream;
- dependentes de sistema externo.

### RF-02 — Tool `lexml_search`

#### Entrada obrigatória

```json
{
  "query": "dc.title any \"codigo de defesa do consumidor\"",
  "start_record": 1,
  "maximum_records": 10,
  "record_schema": "dc"
}
```

#### Parâmetros

| Parâmetro | Tipo | Obrigatório | Regra |
|---|---|---:|---|
| `query` | string | Sim | CQL não vazio dentro do limite configurado |
| `start_record` | inteiro | Não | Padrão 1; mínimo 1 |
| `maximum_records` | inteiro | Não | Padrão 10; mínimo 1; máximo configurável |
| `record_schema` | string | Não | Padrão `dc`; validar formato e allowlist configurável |

#### Comportamento

A tool deve:

1. validar todos os parâmetros localmente;
2. construir a requisição SRU sem concatenação insegura;
3. executar `operation=searchRetrieve`;
4. enviar a versão SRU configurada;
5. classificar a resposta antes de parseá-la;
6. rejeitar conteúdo acima do limite;
7. extrair total, registros, diagnósticos e paginação;
8. preservar a ordem dos registros;
9. retornar zero resultados como sucesso;
10. permitir sucesso parcial quando registros individuais falharem;
11. não carregar páginas adicionais automaticamente;
12. não corrigir ou reescrever silenciosamente o CQL informado.

#### Paginação

A resposta deve conter:

- `number_of_records`;
- `start_record`;
- `returned_records`;
- `next_record_position`, quando informado pelo serviço.

A próxima página não deve ser calculada apenas por `start_record + maximum_records` quando o SRU fornecer `nextRecordPosition`.

#### Modelo de resultado

```json
{
  "schema_version": "1.0.0",
  "query": "dc.title any \"codigo de defesa do consumidor\"",
  "start_record": 1,
  "requested_maximum_records": 10,
  "returned_records": 1,
  "number_of_records": 123,
  "next_record_position": 11,
  "records": [
    {
      "record_position": 1,
      "record_schema": "dc",
      "data": {
        "title": "Código de Defesa do Consumidor",
        "identifier": "urn:lex:br:federal:lei:1990-09-11;8078"
      },
      "field_values": {
        "title": [
          "Código de Defesa do Consumidor"
        ],
        "identifier": [
          "urn:lex:br:federal:lei:1990-09-11;8078"
        ]
      },
      "extensions": [],
      "warnings": []
    }
  ],
  "diagnostics": [],
  "partial_success": false,
  "record_errors": [],
  "provenance": {
    "source": "lexml-sru",
    "source_url": "https://...",
    "retrieved_at": "2026-07-27T00:00:00Z",
    "record_schema": "dc"
  }
}
```

#### Compatibilidade do campo `data`

O campo `data` deverá preservar a projeção já consumida pelos clientes existentes.

O campo `field_values` será a representação canônica sem perda, na qual cada nome de campo aponta para uma lista de valores. Dessa forma, campos repetidos não serão sobrescritos.

Se a auditoria confirmar que o contrato atual já usa listas em `data`, a duplicação poderá ser evitada, desde que:

- a compatibilidade seja mantida;
- todos os valores repetidos sejam preservados;
- o schema final seja documentado;
- testes provem que não há perda silenciosa.

### RF-03 — Sucesso parcial por registro

Quando o envelope SRU for válido, mas um ou mais registros não puderem ser normalizados, o servidor deve:

- preservar os registros válidos;
- marcar `partial_success=true`;
- informar `record_position` quando disponível;
- adicionar um item em `record_errors`;
- não encerrar a tool com erro integral, salvo se nenhum resultado útil puder ser extraído.

Exemplo:

```json
{
  "partial_success": true,
  "records": [],
  "record_errors": [
    {
      "record_position": 4,
      "code": "RECORD_PARSE_ERROR",
      "message": "Não foi possível normalizar o registro.",
      "details": {}
    }
  ]
}
```

### RF-04 — Tool `lexml_resolve_urn`

#### Entrada mínima

```json
{
  "urn": "urn:lex:br:federal:lei:1993-06-21;8666"
}
```

A tool deve:

- rejeitar entrada vazia;
- validar a estrutura básica de uma URN LexML;
- construir o endereço somente a partir do resolver configurado;
- não aceitar URL arbitrária no lugar da URN;
- aplicar codificação segura;
- devolver a URL resolvida;
- não afirmar que o conteúdo é oficial, integral, vigente ou consolidado.

A verificação HTTP poderá ser adicionada como parâmetro opcional somente se não quebrar o contrato atual. Seu valor padrão deverá preservar o comportamento identificado durante a auditoria.

Quando a verificação estiver habilitada, a tool deve:

- utilizar apenas HTTPS;
- limitar redirecionamentos;
- validar o host final contra allowlist;
- bloquear destinos privados, loopback, link-local e serviços de metadata;
- devolver status HTTP e URL final;
- falhar com `UNSAFE_REDIRECT` quando o destino não for permitido.

Exemplo de saída:

```json
{
  "schema_version": "1.0.0",
  "urn": "urn:lex:br:federal:lei:1993-06-21;8666",
  "resolved_url": "https://...",
  "verified": true,
  "final_url": "https://...",
  "status_code": 200,
  "redirect_count": 1,
  "provenance": {
    "source": "lexml-resolver",
    "retrieved_at": "2026-07-27T00:00:00Z"
  }
}
```

### RF-05 — Tool `lexml_explain`

A tool deve:

- executar `operation=explain`;
- validar e classificar a resposta;
- extrair metadados do serviço;
- extrair índices pesquisáveis quando disponíveis;
- extrair schemas e configurações anunciadas;
- preservar diagnósticos;
- usar cache em memória;
- nunca devolver XML bruto por padrão;
- tratar challenge da mesma forma que `lexml_search`.

Exemplo de saída:

```json
{
  "schema_version": "1.0.0",
  "service": {
    "name": "LexML SRU",
    "version": "1.2",
    "description": null
  },
  "indexes": [],
  "schemas": [],
  "diagnostics": [],
  "provenance": {
    "source": "lexml-sru-explain",
    "source_url": "https://...",
    "retrieved_at": "2026-07-27T00:00:00Z"
  }
}
```

### RF-06 — Classificação de resposta upstream

Antes do parsing, o sistema deve classificar a resposta usando, no mínimo:

- status HTTP;
- `Content-Type`;
- tamanho da resposta;
- primeiros bytes;
- presença de marcação HTML;
- raiz XML;
- namespace SRU esperado;
- conteúdo vazio ou truncado.

Categorias internas mínimas:

- `sru_xml`;
- `html_challenge`;
- `html_other`;
- `xml_invalid`;
- `unexpected_content`;
- `empty_response`;
- `response_too_large`.

O sistema não deve confiar apenas no header `Content-Type`.

### RF-07 — Detecção e tratamento de challenge

Uma resposta deve ser classificada como challenge quando houver evidências suficientes, como:

- HTML em vez de XML;
- conteúdo de verificação de segurança;
- challenge JavaScript;
- página de bloqueio ou validação do Senado;
- combinação equivalente reconhecida pelo classificador.

Quando houver challenge:

- a tool deve terminar com erro `UPSTREAM_CHALLENGE`;
- o resultado não deve ser tratado como pesquisa bem-sucedida;
- não deve haver retry imediato;
- a resposta não deve entrar no cache de sucesso;
- o HTML completo não deve ser devolvido ao modelo;
- logs devem conter somente dados sanitizados;
- um excerpt limitado poderá ser incluído apenas em modo de debug local;
- cookies e headers sensíveis nunca poderão ser expostos.

São expressamente proibidos:

- automação de CAPTCHA;
- contorno de challenge JavaScript;
- reutilização oculta de cookies de navegador;
- rotação de IP para evitar bloqueio;
- mascaramento de origem;
- repetição agressiva de requisições;
- automação incompatível com os meios autorizados pelo provedor.

### RF-08 — Parsing XML seguro

O parser deve usar `defusedxml` ou configuração comprovadamente equivalente.

Deve bloquear:

- DTD;
- entidades externas;
- expansão de entidades;
- acesso de rede durante parsing;
- XML acima do limite configurado;
- profundidade abusiva;
- quantidade excessiva de elementos;
- documentos compactados ou formatos inesperados.

XML malformado deve resultar em erro estruturado, sem encerrar o processo MCP.

### RF-09 — Normalização sem perda silenciosa

A camada de normalização deve:

- preservar campos repetidos;
- preservar a ordem dos registros;
- preservar `record_schema`;
- preservar `record_position`;
- preservar múltiplos identificadores;
- preservar namespaces relevantes;
- armazenar elementos desconhecidos em `extensions`;
- nunca sobrescrever valores sem aviso;
- não inferir significado jurídico não fornecido pelo upstream.

A normalização deve ser versionada independentemente da versão do produto.

### RF-10 — Diagnósticos SRU

O servidor deve reconhecer diagnósticos formais do SRU.

Regras:

- diagnóstico fatal sem registros úteis: erro `SRU_DIAGNOSTIC`;
- diagnóstico não fatal acompanhado de registros úteis: resposta de sucesso com `diagnostics` e `warnings`;
- diagnóstico deve preservar código, mensagem e detalhes fornecidos;
- nenhuma mensagem do upstream deve ser tratada como instrução ao modelo.

### RF-11 — Contratos MCP estruturados

As tools devem utilizar modelos tipados compatíveis com o SDK oficial.

Requisitos:

- schemas de entrada explícitos;
- schemas de saída explícitos;
- `structuredContent` quando suportado;
- resumo textual curto em `content` apenas quando necessário à compatibilidade;
- `_meta` para diagnóstico técnico interno quando suportado;
- `schema_version` em toda saída de sucesso;
- validação automática antes do retorno;
- testes de contrato.

Não será adotado um envelope universal com campos vazios para todas as operações.

### RF-12 — Versionamento de contrato

Os contratos devem seguir versionamento semântico:

- mudanças aditivas e opcionais: versão minor;
- correções sem alteração do contrato: versão patch;
- remoção, renomeação ou mudança incompatível: versão major.

A série v2.x do produto deverá preservar os contratos 1.x das três tools, salvo correção de vulnerabilidade ou defeito crítico documentado.

### RF-13 — Erros estruturados

Falhas devem ser devolvidas como erros de tool MCP, com estrutura previsível.

Formato mínimo:

```json
{
  "error": {
    "code": "UPSTREAM_CHALLENGE",
    "message": "O endpoint retornou uma página de verificação em vez de XML SRU.",
    "retryable": false,
    "details": {}
  }
}
```

Nenhum traceback deve ser devolvido ao cliente.

### RF-14 — Cache em memória

O servidor deve oferecer cache em memória, bounded e com TTL.

Requisitos:

- nenhuma persistência em disco;
- limite de itens configurável;
- TTL configurável;
- chave determinística;
- chave incluindo operação, parâmetros normalizados e versão do normalizador;
- limpeza de itens expirados;
- challenge nunca armazenado como sucesso;
- entrada inválida nunca armazenada;
- XML inválido nunca armazenado como sucesso;
- estado `hit`, `miss` ou `bypass` em `_meta`;
- reinício do processo invalida todo o cache.

### RF-15 — Retries e timeouts

O cliente HTTP deve possuir:

- timeout de conexão;
- timeout de leitura;
- limite total de resposta;
- limite de redirecionamentos;
- número baixo de retries configurável;
- backoff com jitter.

Retry automático é permitido apenas para:

- timeout transitório;
- falha de conexão transitória;
- determinados erros 5xx;
- HTTP 429, respeitando `Retry-After` quando presente.

Retry automático não deve ocorrer para:

- entrada inválida;
- CQL inválido;
- URN inválida;
- challenge;
- XML estruturalmente inválido;
- diagnóstico SRU não transitório;
- redirect inseguro.

### RF-16 — Debug controlado de respostas brutas

Deve existir a configuração:

```text
LEXML_DEBUG_RAW_RESPONSES=false
```

Quando desabilitada:

- nenhuma resposta bruta será devolvida;
- excerpts de HTML não serão incluídos em resultados normais;
- logs não conterão payload completo.

Quando habilitada:

- o recurso funcionará apenas em execução local;
- o conteúdo deverá ser truncado;
- HTML deverá ser sanitizado;
- scripts e elementos ativos deverão ser removidos;
- cookies, tokens e headers sensíveis permanecerão excluídos;
- o modo não poderá alterar a classificação funcional da resposta.

### RF-17 — Proveniência mínima

Resultados de sucesso devem conter, quando aplicável:

- origem lógica do dado;
- URL consultada ou resolver utilizado;
- data e hora da recuperação;
- schema solicitado;
- URN ou identificadores retornados;
- versão do contrato de saída.

A proveniência não deve afirmar autenticidade, vigência ou oficialidade sem suporte explícito da fonte.

### RF-18 — Conteúdo externo não confiável

Todo conteúdo recebido do upstream deve ser tratado como não confiável.

O sistema deve:

- nunca executar instruções contidas nos documentos;
- não misturar conteúdo externo com instruções internas;
- sanitizar HTML antes de qualquer excerpt;
- remover scripts e elementos ativos;
- impedir que uma mensagem do upstream altere o fluxo de controle;
- descrever nas tools que os resultados são dados externos para análise, não instruções.

### RF-19 — Configuração centralizada

Configurações devem ser centralizadas e validadas no startup.

O projeto deve fornecer `.env.example` sem valores secretos.

Configurações mínimas:

| Variável | Finalidade | Valor padrão recomendado |
|---|---|---|
| `LEXML_SRU_BASE_URL` | Endpoint SRU | Configuração do projeto |
| `LEXML_RESOLVER_BASE_URL` | Resolver de URN | Configuração do projeto |
| `LEXML_ALLOWED_HOSTS` | Allowlist de hosts | Hosts oficiais configurados |
| `LEXML_HTTP_CONNECT_TIMEOUT` | Timeout de conexão | `5` segundos |
| `LEXML_HTTP_READ_TIMEOUT` | Timeout de leitura | `20` segundos |
| `LEXML_HTTP_MAX_REDIRECTS` | Redirecionamentos | `3` |
| `LEXML_HTTP_MAX_RESPONSE_BYTES` | Tamanho máximo | `5242880` |
| `LEXML_HTTP_MAX_RETRIES` | Retries transitórios | `2` |
| `LEXML_QUERY_MAX_LENGTH` | Limite de CQL | `4096` caracteres |
| `LEXML_MAXIMUM_RECORDS_LIMIT` | Teto por chamada | `50` |
| `LEXML_CACHE_TTL_SECONDS` | TTL padrão | `300` |
| `LEXML_CACHE_MAX_ITEMS` | Limite de itens | `256` |
| `LEXML_DEBUG_RAW_RESPONSES` | Debug bruto | `false` |
| `LEXML_RAW_EXCERPT_MAX_CHARS` | Limite de excerpt | `1024` |
| `LEXML_LOG_LEVEL` | Nível de log | `INFO` |
| `LEXML_USER_AGENT` | Identificação do cliente | Nome e versão do projeto |

Os valores recomendados poderão ser ajustados após medição, desde que a alteração seja documentada.

### RF-20 — Transporte `stdio`

O servidor deve:

- iniciar corretamente por `stdio`;
- listar as tools suportadas;
- não escrever logs operacionais no stdout do protocolo;
- enviar logs para stderr ou destino configurado;
- encerrar de forma limpa;
- respeitar cancelamento quando suportado pelo SDK;
- ser configurável em clientes MCP locais.

---

## 11. Catálogo de erros

| Código | Situação | Retry automático |
|---|---|---:|
| `INVALID_INPUT` | Tipo ou campo inválido | Não |
| `INVALID_CQL` | Query vazia, inválida ou rejeitada | Não |
| `INVALID_URN` | URN fora do formato aceito | Não |
| `INVALID_RECORD_SCHEMA` | Schema não permitido | Não |
| `PAYLOAD_TOO_LARGE` | Entrada excede limite | Não |
| `RESPONSE_TOO_LARGE` | Upstream excede limite | Não |
| `UPSTREAM_CHALLENGE` | HTML de verificação ou bloqueio | Não |
| `UPSTREAM_TIMEOUT` | Timeout de conexão ou leitura | Sim, limitado |
| `UPSTREAM_RATE_LIMITED` | HTTP 429 | Sim, conforme `Retry-After` |
| `UPSTREAM_HTTP_ERROR` | Erro HTTP do upstream | Conforme status |
| `UNSAFE_REDIRECT` | Redirect fora da allowlist ou para rede privada | Não |
| `EMPTY_RESPONSE` | Resposta vazia inesperada | Não |
| `UNEXPECTED_CONTENT` | Tipo de conteúdo não suportado | Não |
| `INVALID_XML` | XML malformado ou inseguro | Não |
| `SRU_DIAGNOSTIC` | Diagnóstico SRU fatal | Conforme diagnóstico |
| `RECORD_PARSE_ERROR` | Falha localizada em registro | Não; permite sucesso parcial |
| `CACHE_ERROR` | Falha interna não fatal de cache | Não; bypass quando seguro |
| `INTERNAL_ERROR` | Falha não classificada | Não |

Cada erro deve conter:

- `code`;
- `message` objetiva;
- `retryable`;
- `details` sanitizado;
- `request_id` em `_meta` quando suportado;
- `record_position` quando aplicável.

---

## 12. Requisitos não funcionais

### RNF-01 — Compatibilidade

- manter nomes e parâmetros existentes;
- preservar comportamento documentado quando seguro;
- adicionar testes de regressão para aliases publicados;
- evitar alterações incompatíveis sem versão major do contrato.

### RNF-02 — Confiabilidade

- nenhuma resposta conhecida deve encerrar o processo MCP;
- timeout, 403, 429, 5xx, challenge, XML inválido e resposta vazia devem produzir falhas estruturadas;
- zero resultados deve ser sucesso;
- falha de cache não deve derrubar a tool quando houver acesso direto seguro ao upstream.

### RNF-03 — Segurança

- XML seguro;
- URLs e redirects controlados;
- sem execução de shell;
- sem segredos no repositório;
- sem cookies ou tokens em logs;
- HTML tratado como conteúdo não confiável;
- limites explícitos para tamanho, registros e retries.

### RNF-04 — Privacidade

- não registrar queries completas quando contiverem conteúdo sensível além do necessário;
- não registrar documentos ou respostas integrais;
- não persistir dados por padrão;
- permitir redução ou desativação de logs de conteúdo;
- limitar excerpts ao modo debug local.

### RNF-05 — Portabilidade

O núcleo deve funcionar sem Docker em:

- macOS Apple Silicon;
- Linux AMD64 ou ARM64 compatível com a versão de Python escolhida.

A release não deve iniciar JVM, Scala, Haskell ou workers externos.

### RNF-06 — Simplicidade operacional

Um desenvolvedor deve conseguir:

1. instalar dependências com `uv`;
2. executar o servidor;
3. registrar o comando em um cliente MCP;
4. listar as tools;
5. executar testes determinísticos.

Também deve existir alternativa documentada com `pip` quando compatível com o projeto.

### RNF-07 — Eficiência

- nenhuma operação pode carregar resultados ilimitados;
- respostas HTTP devem possuir limite de bytes;
- cache deve possuir limite de itens;
- a implementação não deve iniciar componentes não utilizados;
- dependências devem ser mínimas;
- consumo de memória deve ser medido e documentado na entrega, sem exigir infraestrutura pesada.

### RNF-08 — Manutenibilidade

- separar MCP, HTTP, classificação, parsing, normalização, erros, cache e configuração;
- evitar abstrações para backends ainda não implementados;
- utilizar type hints;
- manter funções pequenas e testáveis;
- documentar decisões arquiteturais relevantes em ADR quando necessário.

### RNF-09 — Observabilidade mínima

A release deve oferecer logs estruturados com:

- timestamp;
- nível;
- `request_id`;
- operação;
- duração;
- status;
- código de erro;
- estado do cache;
- challenge detectado;
- quantidade de registros.

Não é exigida stack externa de métricas nesta versão.

### RNF-10 — Dependências

- usar a versão estável atual da série 1.x do SDK oficial `mcp`, com limite superior `<2`;
- registrar versão efetiva em lockfile;
- não misturar o SDK oficial com o pacote independente `fastmcp` sem decisão arquitetural explícita;
- justificar cada nova dependência;
- preferir biblioteca padrão quando adequada;
- verificar licença de cada dependência.

---

## 13. Arquitetura proposta

### 13.1 Componentes

| Componente | Responsabilidade |
|---|---|
| MCP Server | Registro das tools, validação externa e adaptação para MCP |
| Tool Schemas | Modelos de entrada e saída versionados |
| Acervo Connector | Requisições HTTP ao SRU e resolver |
| Response Classifier | Classificação de XML, HTML, challenge e conteúdo inesperado |
| SRU Parser | Parsing seguro do envelope, registros e diagnósticos |
| Normalization Layer | Conversão sem perda para contratos do projeto |
| Error Layer | Exceções internas e erros MCP estruturados |
| Memory Cache | Cache bounded com TTL |
| Configuration | Variáveis, defaults e validação de startup |
| Logging | Logs estruturados e sanitizados |

### 13.2 Fluxo de busca

```text
Cliente MCP
    │
    ▼
lexml_search
    │ valida entrada
    ▼
Acervo Connector
    │ HTTP/SRU
    ▼
Response Classifier
    ├── challenge ─────► erro UPSTREAM_CHALLENGE
    ├── HTTP inválido ─► erro estruturado
    ├── conteúdo inválido ─► erro estruturado
    └── XML SRU
            │
            ▼
        SRU Parser
            │
            ▼
        Normalization
            │
            ▼
       structuredContent
```

### 13.3 Fluxo de resolução de URN

```text
Cliente MCP
    │
    ▼
lexml_resolve_urn
    │ valida URN
    ▼
Resolver Builder
    │
    ├── sem verificação HTTP ─► URL resolvida
    │
    └── com verificação HTTP
            │
            ▼
      Redirect Validator
            │
            ▼
      Resultado estruturado
```

### 13.4 Estrutura de diretórios sugerida

A estrutura existente deve ser preservada quando adequada. Caso a auditoria identifique acoplamento excessivo, a seguinte organização poderá ser adotada incrementalmente:

```text
src/lexml_mcp/
├── server.py
├── config.py
├── schemas/
│   ├── common.py
│   ├── search.py
│   ├── resolve.py
│   └── explain.py
├── connectors/
│   └── acervo.py
├── sru/
│   ├── classifier.py
│   ├── parser.py
│   └── normalizer.py
├── errors.py
├── cache.py
└── logging.py

tests/
├── fixtures/
├── unit/
├── integration/
└── contract/
```

Não é obrigatório reorganizar o repositório para esse formato quando a estrutura atual já separar adequadamente as responsabilidades.

---

## 14. Segurança e modelo de ameaça

### 14.1 Ameaças cobertas

| Ameaça | Controle |
|---|---|
| XML External Entity | DTD e entidades externas bloqueadas |
| Billion Laughs e expansão abusiva | Parser seguro e limites |
| Resposta excessiva | Limite de bytes antes do parsing |
| SSRF | Bases configuradas, allowlist e redirects validados |
| Redirect para rede privada | Bloqueio de IP privado, loopback e link-local |
| HTML tratado como XML | Classificador antes do parser |
| Prompt injection em conteúdo externo | Sanitização e separação entre dado e instrução |
| Vazamento por logs | Redação e ausência de payload integral |
| Loop de retries | Limites e regras por tipo de erro |
| Cache de challenge | Apenas respostas válidas podem ser cacheadas |
| Quebra de cliente por schema | Versionamento e testes de contrato |
| Interpretação jurídica indevida | Limitações explícitas e ausência de inferência silenciosa |

### 14.2 Segredos

O núcleo não requer segredo para as operações públicas previstas. Ainda assim:

- nenhum token deve ser incluído no repositório;
- `.env.example` não deve conter valores reais;
- futuras credenciais devem vir de variáveis de ambiente;
- logs devem redigir headers sensíveis automaticamente.

### 14.3 Conteúdo jurídico

O servidor é um adaptador técnico e não deve emitir conclusão jurídica sobre:

- vigência;
- revogação;
- consolidação;
- autenticidade;
- aplicabilidade;
- hierarquia normativa;
- interpretação do conteúdo.

Esses dados só poderão ser expostos como fatos quando fornecidos explicitamente por fonte confiável e preservados com proveniência.

---

## 15. Estratégia de testes

### 15.1 Testes unitários

Devem cobrir:

- validação de CQL;
- validação de URN;
- construção de parâmetros SRU;
- construção da URL de resolução;
- allowlist de hosts;
- parsing do envelope SRU;
- namespaces;
- campos repetidos;
- múltiplos identificadores;
- campos desconhecidos;
- diagnósticos SRU;
- `nextRecordPosition`;
- zero resultados;
- sucesso parcial;
- classificação de challenge;
- HTML comum;
- XML truncado;
- XML com DTD;
- XML hostil;
- resposta vazia;
- resposta excessiva;
- cache;
- sanitização;
- catálogo de erros;
- ausência de conteúdo sensível nos logs.

### 15.2 Fixtures obrigatórias

O repositório deve incluir fixtures locais para:

- resposta SRU válida com um registro;
- resposta SRU válida com múltiplos registros;
- zero resultados;
- múltiplos títulos;
- múltiplos identificadores;
- namespaces adicionais;
- elemento desconhecido;
- diagnóstico SRU fatal;
- diagnóstico não fatal;
- registro individual inválido;
- HTML de challenge;
- HTML comum;
- XML malformado;
- XML com `DOCTYPE`;
- XML excessivamente profundo;
- resposta vazia;
- HTTP 403;
- HTTP 429;
- HTTP 500;
- timeout;
- redirect permitido;
- redirect para host não permitido;
- resposta acima do limite.

### 15.3 Testes de integração

Devem testar, com transporte HTTP simulado:

- fluxo completo de busca;
- fluxo completo de `explain`;
- resolução com e sem verificação;
- retries permitidos;
- ausência de retry em challenge;
- cache hit e miss;
- sucesso parcial;
- transformação de exceções em erros MCP.

### 15.4 Testes de contrato MCP

Devem verificar:

- inicialização do servidor;
- listagem das tools;
- nomes canônicos;
- aliases comprovadamente legados;
- schemas de entrada;
- schemas de saída;
- `structuredContent`;
- erros de tool;
- execução por `stdio`;
- stdout livre de logs operacionais;
- encerramento limpo;
- cancelamento quando suportado.

### 15.5 Teste real controlado

O teste contra o endpoint público deve ser separado da suíte determinística.

Quando executado, deve tentar:

- uma busca conhecida;
- `explain`;
- uma resolução de URN.

O teste é considerado correto quando:

- recebe e normaliza XML válido; ou
- identifica corretamente o challenge e retorna `UPSTREAM_CHALLENGE`.

A indisponibilidade ou o challenge do upstream não deve bloquear a release quando o comportamento estiver corretamente classificado e toda a suíte determinística passar.

### 15.6 Qualidade

Antes da release devem passar:

- formatter adotado pelo projeto;
- lint;
- type checking;
- testes unitários;
- testes de integração;
- testes de contrato MCP.

A cobertura deve abranger todos os ramos críticos de segurança, classificação e erro. Percentual global isolado não substitui testes dos cenários obrigatórios.

---

## 16. Documentação obrigatória

A v2.0 deve criar ou atualizar somente documentos com conteúdo material:

- `README.md`;
- `ARCHITECTURE.md`;
- `SECURITY.md`;
- `ROADMAP.md`;
- `TODO.md`;
- `CHANGELOG.md`;
- `docs/contracts.md`;
- `docs/errors.md`;
- `.env.example`.

### 16.1 README

Deve incluir:

- finalidade;
- escopo atual;
- status real;
- limitações;
- instalação com `uv`;
- alternativa com `pip`;
- execução;
- configuração por `stdio`;
- tools e aliases suportados;
- exemplos CQL;
- comportamento diante de challenge;
- execução dos testes;
- modo debug;
- aviso de que os resultados não comprovam vigência ou oficialidade.

### 16.2 ARCHITECTURE

Deve documentar:

- componentes;
- fluxo de requisição;
- limites de responsabilidade;
- decisões de compatibilidade;
- estrutura de contratos;
- estratégia de cache;
- tratamento de conteúdo externo.

### 16.3 SECURITY

Deve documentar:

- XML seguro;
- SSRF;
- redirects;
- logging;
- debug bruto;
- prompt injection;
- política para challenge;
- reporte de vulnerabilidade.

### 16.4 ROADMAP

Deve manter fora do escopo atual:

- resources MCP;
- filtros estruturados que geram CQL;
- recuperação de inteiro teor;
- parser;
- linker;
- renderer;
- DOCX;
- artifact store;
- Streamable HTTP;
- autenticação;
- multi-tenancy;
- containers;
- publicação e implantação remota.

### 16.5 TODO

Deve refletir o estado real da execução, com:

- tarefas;
- prioridade;
- status;
- dependências;
- bloqueadores;
- referência a testes e commits quando aplicável.

---

## 17. Métricas de sucesso da release

| Métrica | Meta |
|---|---:|
| Tools canônicas listadas por `stdio` | 100% |
| Testes obrigatórios aprovados | 100% |
| Cenários críticos de XML e challenge cobertos | 100% |
| Respostas conhecidas que encerram o processo | 0 |
| Challenge tratado como sucesso | 0 |
| Campos repetidos perdidos nas fixtures | 0 |
| Payload integral sensível em logs | 0 |
| Dependência obrigatória de endpoint público para testes | 0 |
| Regressões conhecidas dos contratos existentes | 0 |
| Documentos obrigatórios incompatíveis com o código | 0 |

Métricas de latência p50/p95/p99, tracing e dashboards não fazem parte desta versão.

---

## 18. Plano de entrega

### Fase 0 — Auditoria

1. inspecionar a estrutura atual;
2. identificar nomes reais das tools;
3. identificar comandos atuais;
4. registrar versões de Python, `mcp` e dependências;
5. executar testes existentes;
6. iniciar o servidor;
7. realizar chamada por `stdio`;
8. identificar divergências entre código e README;
9. criar ou atualizar `TODO.md`;
10. não refatorar antes de registrar o comportamento atual.

### Fase 1 — Contratos e compatibilidade

1. definir modelos tipados;
2. versionar saídas;
3. preservar nomes e parâmetros;
4. implementar aliases comprovadamente necessários;
5. criar catálogo de erros;
6. adicionar testes de contrato.

### Fase 2 — HTTP e segurança SRU

1. isolar o connector;
2. configurar headers e `User-Agent`;
3. configurar timeouts;
4. limitar redirects;
5. limitar bytes;
6. implementar classificador;
7. substituir parsing inseguro;
8. tratar diagnósticos SRU.

### Fase 3 — Normalização e resiliência

1. preservar campos repetidos;
2. adicionar `field_values` ou solução compatível equivalente;
3. preservar extensões;
4. implementar sucesso parcial;
5. corrigir paginação;
6. implementar retries limitados;
7. implementar cache em memória;
8. implementar logs estruturados.

### Fase 4 — Testes e documentação

1. criar todas as fixtures obrigatórias;
2. completar testes unitários;
3. completar testes de integração;
4. completar testes MCP;
5. validar `stdio`;
6. executar teste real controlado;
7. atualizar documentação;
8. revisar segurança;
9. atualizar changelog.

### Fase 5 — Release

1. revisar diff completo;
2. confirmar ausência de segredos;
3. confirmar lockfile;
4. registrar limitações;
5. medir consumo básico de memória e startup;
6. criar tag ou release conforme prática do repositório;
7. publicar resumo de entrega.

---

## 19. Critérios de aceite

### 19.1 Compatibilidade

- [ ] `lexml_search` funciona;
- [ ] `lexml_resolve_urn` funciona;
- [ ] `lexml_explain` funciona;
- [ ] parâmetros existentes foram preservados;
- [ ] aliases públicos comprovados continuam funcionando;
- [ ] aliases usam a mesma implementação interna;
- [ ] contratos estão versionados.

### 19.2 Busca e SRU

- [ ] busca válida retorna estrutura tipada;
- [ ] zero resultados retorna sucesso;
- [ ] diagnósticos SRU são reconhecidos;
- [ ] `nextRecordPosition` é utilizado;
- [ ] nenhuma paginação automática completa ocorre;
- [ ] campos repetidos são preservados;
- [ ] extensões desconhecidas não são descartadas silenciosamente;
- [ ] sucesso parcial informa erros por registro.

### 19.3 Challenge e HTTP

- [ ] HTML de challenge é detectado mesmo com HTTP 200;
- [ ] challenge retorna `UPSTREAM_CHALLENGE`;
- [ ] challenge não entra no cache de sucesso;
- [ ] challenge não provoca retry imediato;
- [ ] HTML bruto não é devolvido por padrão;
- [ ] timeouts estão configurados;
- [ ] retries só ocorrem em falhas transitórias;
- [ ] resposta acima do limite é interrompida com erro estruturado.

### 19.4 Segurança

- [ ] DTD é bloqueado;
- [ ] entidades externas são bloqueadas;
- [ ] XML hostil não encerra o processo;
- [ ] redirects são validados;
- [ ] destinos privados são bloqueados;
- [ ] logs não contêm cookies, tokens ou payload integral;
- [ ] modo bruto está desabilitado por padrão;
- [ ] conteúdo externo é tratado como não confiável.

### 19.5 Cache e observabilidade

- [ ] cache possui TTL;
- [ ] cache possui limite;
- [ ] cache é apenas em memória;
- [ ] chave inclui versão do normalizador;
- [ ] estado do cache aparece em diagnóstico;
- [ ] logs estruturados possuem `request_id`;
- [ ] logs não interferem no stdout do MCP.

### 19.6 Testes e documentação

- [ ] todas as fixtures obrigatórias existem;
- [ ] testes unitários passam;
- [ ] testes de integração passam;
- [ ] testes de contrato MCP passam;
- [ ] execução por `stdio` foi validada;
- [ ] teste real controlado foi executado ou sua impossibilidade foi registrada;
- [ ] README reflete o comportamento real;
- [ ] limitações estão documentadas;
- [ ] ROADMAP separa itens futuros;
- [ ] CHANGELOG registra a release;
- [ ] nenhuma credencial está presente no repositório.

---

## 20. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Challenge persistente do Senado | Busca real indisponível | Classificação explícita, testes locais e contato institucional fora do código |
| Alteração do endpoint SRU | Quebra de integração | Configuração centralizada e connector isolado |
| XML inconsistente | Perda ou falha | Parser seguro, extensões e sucesso parcial |
| Divergência de nomes das tools | Quebra de clientes | Auditoria, nomes canônicos e aliases comprovados |
| Normalização destrutiva | Informação incompleta | Valores em listas, extensões e testes com repetição |
| Interpretação jurídica indevida | Decisão errada do usuário/agente | Limites explícitos, proveniência e ausência de inferência |
| Logs com conteúdo sensível | Exposição de dados | Sanitização e ausência de payload integral |
| Abstração prematura | Complexidade e atraso | Escopo restrito ao núcleo SRU |
| Dependência do endpoint nos testes | Suíte instável | Fixtures e mock do transporte |
| Atualização incompatível do SDK | Quebra do servidor | Lockfile e limite `<2` |

---

## 21. Roadmap posterior

### v2.1 — Experiência MCP ampliada

Possíveis itens:

- resource `lexml://sru/explain`;
- resource `lexml://record/{encoded_urn}`;
- filtros estruturados com geração segura de CQL;
- cache persistente apenas se houver necessidade comprovada;
- exportação paginada para artefato, sem carregar tudo no contexto;
- estudo de recuperação de conteúdo integral.

`lexml://document/{urn}` só deverá existir quando o produto recuperar efetivamente o documento, e não apenas metadados ou resolução de URL.

### v2.2 — Spike do parser

Antes de criar tool pública:

- identificar o artefato oficial exato;
- construir de forma reproduzível;
- validar Java/Scala e arquitetura;
- confirmar entradas e saídas reais;
- produzir fixtures;
- medir memória e latência;
- avaliar licença;
- decidir entre biblioteca, worker, CLI, container ou serviço interno.

Um spike poderá terminar com decisão de não integrar o componente.

### v2.3 — Spike e integração do linker

Antes de publicar contrato:

- executar a ferramenta oficial;
- identificar formatos de entrada e saída;
- separar campos nativos de campos derivados;
- criar corpus de remissões;
- definir metodologia de avaliação;
- medir precisão e recall apenas após anotação confiável;
- validar isolamento de subprocesso.

### v2.4 — Renderer e artefatos DOCX

Itens condicionados à validação do renderer:

- worker JVM ou integração equivalente;
- artifact store temporário;
- resource binário;
- TTL;
- hash;
- validação da estrutura DOCX;
- limites de tamanho;
- autorização para implantação remota.

DOCX não deverá ser devolvido integralmente em base64 no resultado normal da tool.

### v3.0 — Servidor remoto

Itens condicionados a threat model próprio:

- Streamable HTTP;
- autenticação;
- autorização;
- validação de origem;
- rate limiting;
- isolamento por tenant;
- storage autenticado;
- observabilidade externa;
- deployment e rollback;
- testes de carga;
- SBOM e processo formal de release.

---

## 22. Pendências não bloqueadoras

| Pendência | Tratamento |
|---|---|
| Confirmar nomes registrados no código atual | Resolver na Fase 0 |
| Confirmar schemas anunciados por `explain` | Preservar configuração e testar quando o upstream responder |
| Definir allowlist final de hosts | Derivar da configuração real e documentar |
| Negociar acesso automatizado legítimo | Ação institucional externa ao código |
| Determinar eventual distribuição pública | Roadmap posterior |
| Avaliar contato e identificação no `User-Agent` | Definir antes da release |

Nenhuma dessas pendências autoriza contorno do challenge ou ampliação silenciosa do escopo.

---

## 23. Definição de concluído

A v2.0 estará concluída quando:

1. as três tools canônicas estiverem funcionais por `stdio`;
2. aliases comprovadamente necessários estiverem preservados;
3. contratos estiverem tipados, versionados e documentados;
4. parsing XML seguro estiver ativo;
5. challenge estiver corretamente classificado;
6. diagnósticos SRU estiverem tratados;
7. paginação utilizar `nextRecordPosition`;
8. campos repetidos não forem perdidos;
9. sucesso parcial estiver implementado;
10. timeouts, limits e retries estiverem configurados;
11. cache em memória estiver limitado e testado;
12. logs estiverem sanitizados;
13. testes determinísticos não dependerem do endpoint público;
14. toda a suíte obrigatória estiver aprovada;
15. README e documentação refletirem o código real;
16. não houver segredo no repositório;
17. não houver regressão conhecida não documentada;
18. nenhum item fora do escopo tiver sido implementado como dependência obrigatória;
19. riscos críticos estiverem mitigados ou explicitamente bloquearem a release;
20. a entrega final registrar testes, limitações e decisões.

A conclusão não poderá ser declarada quando houver:

- teste obrigatório falhando;
- comportamento alegado, mas não executado;
- documentação incompatível com o código;
- vulnerabilidade crítica conhecida;
- quebra não documentada de compatibilidade;
- challenge tratado como sucesso;
- payload sensível exposto;
- dependência obrigatória de parser, linker, renderer, JVM ou serviço remoto.

---

## 24. Entregáveis da implementação

A entrega deverá apresentar:

1. resumo executivo das alterações;
2. arquitetura implementada;
3. lista de arquivos criados e modificados;
4. tools e aliases disponíveis;
5. contratos de entrada e saída;
6. catálogo de erros;
7. configurações e defaults;
8. testes executados e resultados;
9. resultado do teste real controlado;
10. ambiente utilizado na validação;
11. consumo básico de memória e startup observado;
12. limitações conhecidas;
13. riscos residuais;
14. decisões arquiteturais;
15. instruções de instalação e execução;
16. itens mantidos no roadmap;
17. commits ou referência equivalente da implementação.

---

## 25. Resumo da decisão de escopo

A v2.0 do LexML MCP não será uma implementação completa da stack LexML.

Ela será uma release de estabilização do núcleo existente, com três responsabilidades:

1. pesquisar o acervo por SRU de forma segura e previsível;
2. resolver URNs sem extrapolar o significado jurídico do resultado;
3. expor capacidades do serviço SRU por `explain`.

A expansão para parser, linker, renderer, DOCX e servidor remoto somente ocorrerá após validação específica de cada componente e sem transformar hipóteses arquiteturais em contratos públicos.
