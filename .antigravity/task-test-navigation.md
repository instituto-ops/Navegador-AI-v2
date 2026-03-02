# TASK: Criar Teste Prático de Navegação Autônoma

Você (Google Jules) é o Operador. O objetivo desta sessão é criar, configurar e rodar um teste prático que valide o funcionamento do nosso braço executor (`browser-use`).

## Diretrizes e Arquitetura (Regra do Custo Zero)
Conforme o nosso `.antigravity/system.md` e `ARCHITECTURE.md`, nós usamos `browser-use` com Python para automação extrema usando o modelo livre, como o `ChatBrowserUse()` (ou outro compatível provido localmente/gratuitamente). NUNCA coloque chaves secretas de APIs pagas no código.

## Passos para Execução:
1. **Criar Arquivo:** Crie o arquivo `tests/test_agent_navigation.py`.
2. **Estrutura do Agente:** 
   - Instancie um `Browser` configurado de forma inteligente.
   - Instancie um `Agent` com o seguinte objetivo de tarefa: `"Vá até o Google, busque pelas palavras exatas 'NeuroStrategy OS Github' e veja se encontra algum resultado. Extraia os títulos da primeira página de busca."`
   - Opcionalmente, pode ser uma busca sobre qualquer outro dado público inofensivo que exija manipulação de cliques/extração.
3. **Mecanismo de Teste:** Se for possível na sua sanbox, rode o arquivo (ex: `python tests/test_agent_navigation.py` ou usando `uv run`, lembrando que usamos `uv` segundo o `AGENTS.md`) para verificar se o Browser foi controlado corretamente. O `AGENTS.md` recomenda `uv` e `uv run`. 
4. **Auto-Correção:** Caso o próprio browser-use lance algum erro de runtime (ex: asyncio no Windows, importação faltante, ou falha de clique), você mesmo deve ler o log de erro e corrigir o código até que a execução seja 100% livre de bugs de Setup.

## Condição de Êxito
A sessão será considerada "Completed" quando o arquivo `.py` estiver pronto, otimizado para a nossa stack e capaz de executar o fluxo planejado.
