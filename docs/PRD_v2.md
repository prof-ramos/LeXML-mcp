# PRD v2 — LexML MCP

## Visão geral

Este documento define a versão 2 do Product Requirements Document (PRD) do servidor MCP para integração com o ecossistema **LexML Brasil**, agora baseado não apenas no acervo via SRU/XML, mas também nos serviços e bibliotecas oficiais publicados na organização GitHub do Projeto LexML. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)

O objetivo do produto é transformar capacidades de busca, parsing, linkagem e renderização de documentos normativos em tools consumíveis por clientes compatíveis com **Model Context Protocol (MCP)**, como Claude Desktop, Cursor e outros ambientes com suporte ao SDK Python oficial. [modelcontextprotocol](https://modelcontextprotocol.io/docs/sdk)

## Contexto e problema

O LexML agrega legislação, jurisprudência, proposições legislativas, doutrina e outros documentos correlatos em uma única interface, com serviços consultáveis programaticamente. No entanto, o acesso predominante ainda é via portal web, o que limita o uso em workflows automatizados com agentes e LLMs. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)

Ao mesmo tempo, o MCP foi concebido para permitir conexões bidirecionais seguras entre fontes de dados e ferramentas de IA, com SDKs e documentação pública em múltiplas linguagens, incluindo Python. Clientes MCP esperam interfaces de tools consistentes, com contratos previsíveis, retorno estruturado e mensagens de erro claras. [raw.githubusercontent](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/refs/heads/main/README.md)

Há ainda uma diferença prática entre a documentação conceitual de serviços como o acervo LexML e o comportamento efetivo em acessos automatizados simples, que podem encontrar páginas de verificação de segurança do Senado em vez de respostas XML SRU, exigindo uma camada de tratamento apropriada. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)

## Visão de produto

O **LexML MCP** deve atuar como uma fachada organizada sobre a "LexML stack":

- **Acervo LexML via SRU/XML** para busca jurídica e legislativa. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)
- **Parser LexML de documentos normativos**, incluindo webservice e API. [github](https://github.com/lexml/lexml-parser-projeto-lei-ws)
- **Linker de remissões entre normas legislativas**. [github](https://github.com/lexml/lexml-linker)
- **Renderers de LexML para formatos como DOCX**. [github](https://github.com/lexml/lexml-renderer-docx)

Do ponto de vista de produto, a visão é ser um adaptador de alto nível: o MCP Python expõe tools que conversam com esses serviços JVM/Scala/Java, oferecendo respostas canônicas em JSON, tratamento uniforme de erros e uma experiência previsível para modelos e agentes.

## Metas

- Integrar o acervo LexML via SRU quando tecnicamente viável, com detecção explícita de challenge HTML e tipos de conteúdo. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)
- Encapsular serviços oficiais do ecossistema LexML (parser, linker, renderer) em conectores HTTP/REST consumidos pelo MCP Python. [github](https://github.com/lexml/lexml-parser-projeto-lei-ws-api)
- Expor tools MCP com contratos claros para busca, parsing, linkagem, renderização e resolução de URN.
- Normalizar respostas para JSON amigável a modelos e agentes, mantendo metadados de debug (URL, status, content-type, excerpt).
- Fornecer documentação suficiente para instalação, configuração e extensão do projeto por terceiros.

## Não metas

- Não substituir o portal web do LexML como interface principal para usuários humanos. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)
- Não reimplementar parsers, linkers ou renderers que já existem na org LexML — o foco é encapsular serviços existentes. [github](https://github.com/lexml)
- Não contornar mecanismos de proteção ou verificação do provider fora de meios tecnicamente e juridicamente permitidos. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)
- Não incluir interface gráfica própria (dashboard web, admin) no escopo do MCP.

## Usuários-alvo

### Primários

- Desenvolvedores que constroem agentes jurídicos ou pipelines de pesquisa legislativa.
- Profissionais de direito e compliance com workflows assistidos por IA.
- Pesquisadores e equipes de documentação jurídica que desejam integrar acervo e serviços LexML a cadeias automatizadas.

### Secundários

- Mantenedores de servidores MCP reutilizáveis em ecossistemas internos.
- Times de produto que desejam validar agentes com fontes jurídicas brasileiras e estrutura normativa em LexML.

## Casos de uso principais

| Caso de uso | Descrição | Backend |
|---|---|---|
| Busca no acervo | Buscar documentos no acervo LexML a partir de query CQL/SRU, retornando resultados estruturados ou indicando challenge. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml) | SRU/acervo |
| Explain do serviço SRU | Inspecionar metadados/capacidades do serviço SRU para debug e desenvolvimento. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml) | SRU/acervo |
| Resolução de URN | Converter uma URN LexML em URL pública navegável. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml) | Portal LexML |
| Parse de projeto de lei | Receber texto/articulado e devolver AST/estrutura normativa via parser LexML. [github](https://github.com/lexml/lexml-parser-projeto-lei-ws) | `lexml-parser-projeto-lei-ws` / `-ws-api` |
| Linkagem de remissões | Analisar norma/projeto e devolver mapa de remissões (alvos, tipo, posição), usando linker LexML. [github](https://github.com/lexml/lexml-linker) | `lexml-linker` |
| Render LexML → DOCX | Converter documento LexML em arquivo DOCX via renderer LexML. [github](https://github.com/lexml/lexml-renderer-docx) | `lexml-renderer-docx` |

## Escopo funcional

### Requisitos funcionais

#### RF-01 — Tool `search_acervo_lexml`

O sistema deve expor uma tool `search_acervo_lexml` que receba, no mínimo, `query`, `start_record`, `maximum_records` e `record_schema` para consultar o acervo via SRU. A tool deve construir a chamada `searchRetrieve`, enviar a requisição ao endpoint, devolver metadados básicos da resposta e, quando houver XML válido, parsear registros em JSON simplificado. Em caso de HTML de verificação ou outro tipo não XML, deve sinalizar explicitamente o tipo de conteúdo e fornecer um resumo da resposta. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)

#### RF-02 — Tool `explain_acervo`

O sistema deve expor uma tool `explain_acervo` para consultar a operação `explain` do serviço SRU, retornando dados básicos do serviço quando o XML estiver íntegro e preservando o payload bruto e um diagnóstico de parsing quando não estiver. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)

#### RF-03 — Tool `resolve_lexml_urn`

O sistema deve expor uma tool `resolve_lexml_urn` que receba uma URN LexML e devolva a URL pública correspondente, bem como status HTTP e URL final após redirecionamentos. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)

#### RF-04 — Tool `parse_projeto_lei`

O sistema deve expor uma tool `parse_projeto_lei` que receba um documento normativo em LexML (ou formato suportado pelo parser) e chame um serviço que encapsule o `lexml-parser-projeto-lei-ws` ou a API `lexml-parser-projeto-lei-ws-api`. A saída deve ser um JSON representando a estrutura normativa (ementa, artigos, incisos, etc.), mantendo identificadores relevantes e metadados. [github](https://github.com/lexml/lexml-parser-projeto-lei?search=1)

#### RF-05 — Tool `link_norma`

O sistema deve expor uma tool `link_norma` que receba uma norma/projeto em LexML e chame um serviço que encapsule o `lexml-linker` para extrair remissões entre normas legislativas. A saída deve ser um JSON contendo remissões (alvo, tipo de remissão, posição no texto, URN de destino quando disponível). [github](https://github.com/lexml/lexml-linker/blob/master/version)

#### RF-06 — Tool `render_lexml_docx`

O sistema deve expor uma tool `render_lexml_docx` que receba documento LexML e chame um serviço construído sobre `lexml-renderer-docx` para produzir um DOCX. A saída pode ser um blob em base64, uma URL de download ou outro formato que seja consumível por clientes MCP e ferramentas auxiliares. [github](https://github.com/lexml/lexml-renderer-docx)

#### RF-07 — Detecção de conteúdo não XML

O sistema deve detectar e sinalizar quando a resposta de backends XML (como o serviço SRU) não for XML válido, especialmente em casos de HTML de verificação de segurança. A tool deve retornar objeto estruturado com `content_type`, `is_challenge_like`, `raw_excerpt` e `request_url`.

#### RF-08 — Compatibilidade MCP

O servidor deve rodar com o SDK Python oficial do MCP e expor tools compatíveis com clientes modernos, preferencialmente via `FastMCP` e transporte `stdio` para simplicidade operacional. [py.sdk.modelcontextprotocol](https://py.sdk.modelcontextprotocol.io/api/)

#### RF-09 — Documentação

O projeto deve incluir documentação com fontes oficiais (LexML, MCP, org GitHub), instruções de instalação com `uv` e `pip`, exemplos de configuração para clientes MCP e instruções para testes básicos.

### Requisitos não funcionais

#### RNF-01 — Simplicidade de setup

Um desenvolvedor deve conseguir instalar e rodar o servidor localmente com poucos comandos, usando Python suportado e dependências mínimas. [pypi](https://pypi.org/project/mcp/1.7.1/)

#### RNF-02 — Tolerância a falhas

Falhas de rede, timeout, HTML inesperado, XML inválido, erros HTTP e campos ausentes não devem encerrar o processo sem mensagem estruturada ao cliente MCP. Os erros devem ser retornados como objetos JSON com campos padrão de diagnóstico.

#### RNF-03 — Extensibilidade

O código deve ser organizado em camadas (MCP Server, Backend Connectors, Normalization Layer, Error Layer) para permitir o acréscimo de novas tools, backends e estratégias de autenticação/sessão. [gofastmcp](https://gofastmcp.com/getting-started/welcome)

#### RNF-04 — Observabilidade

As respostas devem incluir dados suficientes para debug, como URL efetivamente usada, status HTTP, content-type e resumo da carga devolvida. Logs podem ser opcionais, mas a resposta da tool deve ser autossuficiente para diagnóstico básico.

#### RNF-05 — Portabilidade

O projeto deve funcionar em ambientes locais e VPS Linux comuns, sem dependência de serviços proprietários adicionais para o MVP.

## Arquitetura proposta

### Componentes

| Componente | Responsabilidade |
|---|---|
| MCP Server Core | Expor tools, validar parâmetros e devolver respostas compatíveis com MCP (via FastMCP/SDK Python).! [modelcontextprotocol](https://modelcontextprotocol.io/docs/sdk) |
| AcervoConnector | Realizar chamadas ao endpoint SRU/acervo e aplicar detecção de conteúdo. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml) |
| ParserConnector | Encapsular chamadas ao `lexml-parser-projeto-lei-ws` e/ou `lexml-parser-projeto-lei-ws-api`, via HTTP/REST ou cliente JVM externo. [github](https://github.com/lexml/lexml-parser-projeto-lei-ws) |
| LinkerConnector | Encapsular chamadas ao serviço construído sobre `lexml-linker` para remissões. [github](https://github.com/lexml/lexml-linker) |
| RendererConnector | Encapsular chamadas a serviço baseado em `lexml-renderer-docx` para LexML→DOCX. [github](https://github.com/lexml/lexml-renderer-docx) |
| Normalization Layer | Converter respostas específicas de cada backend (Scala/Java, XML SRU, etc.) em JSON canônico para MCP. |
| Error & Challenge Layer | Normalizar erros de rede, parsing, HTTP e challenge HTML em formato único, com campos padrão de diagnóstico. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml) |
| Config Layer | Centralizar endpoint base, timeouts, limites, flags de modo (raw vs parsed) e futuros parâmetros de sessão/autenticação. |

### Fluxo principal por tipo de tool

#### Busca no acervo (`search_acervo_lexml`)

1. Cliente MCP chama a tool com query CQL e parâmetros de paginação.
2. AcervoConnector monta a requisição SRU, envia ao endpoint e obtém resposta.
3. Response Adapter classifica o conteúdo (`application/xml`, `text/html`, etc.).
4. Para XML válido, XML Parser extrai `numberOfRecords`, `recordData`, campos DC e diagnósticos SRU.
5. Para HTML/challenge, Error & Challenge Layer encapsula a resposta em objeto de bloqueio estruturado.
6. MCP Server devolve JSON ao cliente.

#### Parse de projeto de lei (`parse_projeto_lei`)

1. Cliente MCP fornece documento normativo em LexML ou formato aceito pelo parser.
2. ParserConnector envia payload ao serviço que encapsula `lexml-parser-projeto-lei-ws` / `-ws-api`.
3. Serviço LexML retorna estrutura normativa (ementa, artigos, incisos, etc.).
4. Normalization Layer converte para JSON MCP com campos consistentes.
5. MCP Server devolve JSON ao cliente.

#### Linkagem de remissões (`link_norma`)

1. Cliente MCP fornece norma/projeto em LexML.
2. LinkerConnector envia documento ao serviço baseado em `lexml-linker`.
3. Serviço retorna remissões (alvos, tipos, posições, possivelmente URNs de destino).
4. Normalization Layer organiza remissões em estrutura JSON adequada.
5. MCP Server devolve JSON ao cliente.

#### Render LexML → DOCX (`render_lexml_docx`)

1. Cliente MCP fornece documento LexML.
2. RendererConnector envia ao serviço construído sobre `lexml-renderer-docx`.
3. Serviço gera DOCX e retorna como arquivo ou stream.
4. Normalization Layer converte em formato consumível por MCP (por exemplo, base64 + metadados de nome/size).
5. MCP Server devolve JSON ao cliente.

## Modelo de dados de resposta (exemplos)

### Exemplo de resposta de busca

```json
{
  "query": "dc.title any \"codigo de defesa do consumidor\"",
  "requestUrl": "https://www.lexml.gov.br/busca/SRU?...",
  "contentType": "application/xml",
  "numberOfRecords": 123,
  "nextRecordPosition": 11,
  "records": [
    {
      "recordSchema": "dc",
      "recordPosition": 1,
      "data": {
        "title": "Código de Defesa do Consumidor",
        "identifier": "urn:lex:br:federal:lei:1990-09-11;8078"
      }
    }
  ],
  "diagnostics": []
}
```

### Exemplo de resposta de challenge

```json
{
  "requestUrl": "https://www.lexml.gov.br/busca/SRU?...",
  "contentType": "text/html",
  "isChallengeLike": true,
  "statusCode": 200,
  "rawExcerpt": "<!DOCTYPE html> ... Verificação de segurança — Senado Federal ...",
  "message": "O endpoint retornou HTML de verificação em vez de XML SRU."
}
```

### Exemplo de resposta de parse de projeto de lei

```json
{
  "source": "lexml-parser-projeto-lei-ws",
  "success": true,
  "document": {
    "urn": "urn:lex:br:federal:pl:2024-01-15;1234",
    "ementa": "Dispõe sobre ...",
    "artigos": [
      {
        "numero": 1,
        "texto": "Art. 1º ...",
        "incisos": [
          { "rotulo": "I", "texto": "..." }
        ]
      }
    ]
  }
}
```

### Exemplo de resposta de linkagem

```json
{
  "source": "lexml-linker",
  "success": true,
  "remissoes": [
    {
      "tipo": "alteracao",
      "alvoTexto": "Lei nº 8.666, de 21 de junho de 1993",
      "posicao": { "artigo": 2, "inciso": "I" },
      "urnDestino": "urn:lex:br:federal:lei:1993-06-21;8666"
    }
  ]
}
```

### Exemplo de resposta de renderização

```json
{
  "source": "lexml-renderer-docx",
  "success": true,
  "filename": "lei-8078-lexml.docx",
  "contentBase64": "UEsDBBQABgAIA..."
}
```

## Dependências técnicas

| Dependência | Finalidade |
|---|---|
| `mcp` | SDK oficial do Model Context Protocol para servidor Python. [modelcontextprotocol](https://modelcontextprotocol.io/docs/sdk) |
| `httpx` | Cliente HTTP assíncrono para chamadas externas. |
| `xml.etree.ElementTree` | Parsing básico de XML no MVP para SRU. |
| `uv` (opcional) | Experiência de instalação e execução simplificada. [raw.githubusercontent](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/refs/heads/main/README.md) |
| JVM/Scala (serviços LexML) | Ambiente de execução para parser, linker e renderer oficiais via serviços próprios. [github](https://github.com/lexml/lexml-parser-projeto-lei-ws) |
| Serviços REST internos | Camada de integração entre MCP Python e artefatos LexML (parser, linker, renderer).

## Riscos

### Riscos técnicos

- O endpoint público do acervo pode mudar comportamento, exigir cookies, challenge JS ou políticas específicas de acesso automatizado. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)
- O XML retornado pode vir malformado ou inconsistente em alguns cenários, exigindo parser tolerante. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)
- Serviços baseados em JVM (parser/linker/renderer) podem ter latência maior ou depender de infraestrutura dedicada.
- A normalização de schemas LexML em JSON MCP pode exigir esforço contínuo com base em exemplos reais.

### Riscos de produto

- Usuários podem interpretar o projeto como um cliente LexML "pronto" para todo o stack antes da maturação do tratamento de challenge e dos serviços de suporte.
- Documentação insuficiente ou desatualizada pode inviabilizar adoção, mesmo com código funcional. [gofastmcp](https://gofastmcp.com/tutorials/create-mcp-server)

## Estratégia de mitigação

- Diferenciar claramente "MVP estruturado" de "versão de produção" na documentação.
- Detectar e expor challenge HTML de forma explícita nas tools relacionadas ao acervo. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)
- Priorizar README forte, exemplos executáveis e retorno com dados de debug (URL, status, content-type, excerpt). [modelcontextprotocol](https://modelcontextprotocol.io/docs/sdk)
- Criar camadas de conectores bem isoladas para parser/linker/renderer, permitindo substituição ou melhoria sem impactar o contrato MCP.
- Adotar testes incrementais por tool e por tipo de resposta.

## Roadmap

### Linha SRU/acervo

- **Fase 0**
  - Servidor MCP com FastMCP.
  - Tool de busca inicial (`search_acervo_lexml`).
  - Tool de URN (`resolve_lexml_urn`).
  - README básico.

- **Fase 1**
  - Parser XML mais robusto.
  - Detecção de content-type.
  - Detecção de challenge.
  - Erros estruturados.
  - Exemplos de configuração para clientes MCP. [raw.githubusercontent](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/refs/heads/main/README.md)

### Linha serviços LexML GitHub

- **Fase 1**
  - Encapsular `lexml-parser-projeto-lei-ws` / `-ws-api` em serviço REST próprio. [central.sonatype](https://central.sonatype.com/artifact/br.gov.lexml.parser.pl/lexml-parser-projeto-lei-ws-api/1.7.4)
  - Implementar tool MCP `parse_projeto_lei`.

- **Fase 2**
  - Encapsular `lexml-linker` em serviço REST.
  - Implementar tool MCP `link_norma`. [github](https://github.com/lexml/lexml-linker)

- **Fase 3**
  - Encapsular `lexml-renderer-docx` em serviço REST.
  - Implementar tool MCP `render_lexml_docx`. [github](https://github.com/lexml/lexml-renderer-docx)
  - Refinar normalização de schemas LexML em JSON MCP.

## Critérios de aceitação do MVP (v2)

| Critério | Resultado esperado |
|---|---|
| Instalação local | Subir o servidor com `uv` ou `pip` em ambiente Python suportado. [raw.githubusercontent](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/refs/heads/main/README.md) |
| Registro em cliente MCP | Apontar cliente MCP para o comando do servidor via `stdio` e listar tools disponíveis. [modelcontextprotocol](https://modelcontextprotocol.io/docs/sdk) |
| Tool de URN | Resolver pelo menos uma URN pública e devolver URL final. |
| Tool de busca | Executar chamada e devolver resposta parseada ou challenge estruturado. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml) |
| Tool de parse | Consumir serviço baseado em `lexml-parser-projeto-lei-ws` e devolver JSON de estrutura normativa. [github](https://github.com/lexml/lexml-parser-projeto-lei-ws) |
| Documentação | Explicar fontes, setup, configuração e limitações reais do projeto, incluindo a dependência de serviços LexML. [github](https://github.com/lexml) |

## Métricas de sucesso

No curto prazo, o sucesso será medido pelo tempo até a primeira execução local, taxa de sucesso na configuração em cliente MCP, clareza dos erros retornados e capacidade de um desenvolvedor externo reproduzir o setup sem suporte adicional. Em fase posterior, podem ser acompanhadas métricas de chamadas bem-sucedidas por tool, incidência de challenge HTML, tempo médio de resposta, cobertura de testes e uso de serviços LexML (parser/linker/renderer). [gofastmcp](https://gofastmcp.com/tutorials/create-mcp-server)

## Decisões em aberto

- Estratégia exata para operar diante da verificação de segurança do endpoint público do acervo. [www12.senado.leg](https://www12.senado.leg.br/dados-abertos/legislativo/legislacao/acervo-do-portal-lexml)
- Forma de exposição dos serviços JVM (se como microserviços internos, se via infra existente do LexML, etc.). [github](https://github.com/orgs/lexml/repositories)
- Nível de normalização semântica a ser incluído (apenas mapeamento de campos ou enriquecimento com convenções específicas de casos de uso jurídicos).
- Escopo de distribuição (template GitHub, pacote PyPI, imagem de contêiner, etc.).

## Resumo executivo

A v2 do PRD do **LexML MCP** posiciona o produto como um adaptador organizado sobre a stack oficial do LexML (acervo, parser, linker, renderer), em vez de um wrapper isolado de SRU. O foco está em oferecer tools MCP estáveis, com contratos claros e documentação forte, permitindo que agentes e LLMs consumam capacidades do LexML dentro de fluxos modernos de IA, sem recriar o que já existe na org nem ignorar as limitações práticas do endpoint público. [github](https://github.com/lexml)
