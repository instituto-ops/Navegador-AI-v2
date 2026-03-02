# A Tríade de Desenvolvimento Autônomo (DevEx)

A Experiência do Desenvolvedor (DevEx) no projeto NeuroStrategy OS é moldada através de três papéis essenciais e interconectados que minimizam a complexidade operacional, mitigam custos abusivos e automatizam o fluxo com velocidade através do Google AI.

## 1. Dr. Victor (Tech Lead / *Human-in-the-loop*)
A autoridade médica corporativa final, que atua como dono do produto e líder técnico.
- Define os requisitos clínicos e estratégias de inteligência de marketing médico.
- Mantém o foco no propósito do Agente do NeuroStrategy OS.
- Entra no circuito apenas para aprovar/descartar Pull Requests completos validados e arquitetados pela dupla (Antigravity e Jules).

## 2. Antigravity IDE (O Arquiteto)
Sua extensão de monitoramento e criação local. Ele é o *Guard Dog* implacável do repositório físico do seu computador.
- Traduz intenções em Especificações Técnicas (Prompts altamente estruturados).
- Audita arquiteturas criadas e valida em tempo real a árvore estrutural do projeto e dependências (LSP, repositório).
- É o responsável local por impedir ativamente a injeção acidental de dependências ou bibliotecas que quebrem as filosofias base (ex: uso de APIs pagas da OpenAI/Claude ou peso indevido no cliente/server).
- Atua como a ponte final no Fluxo: Fazer *Code Review* minucioso das implementações submetidas via PR antes da aprovação final humana.

## 3. Google Jules (O Operador)
O operário silencioso e onipresente que codifica na nuvem, acessando repositórios ligados ao ambiente de trabalho. É movido pela incrível estrutura assíncrona do Google AI Pro.
- Fica aguardando as chamadas em background (as "Issues" delegadas).
- Mergulha em arquivos, refatora bibliotecas e resolve conflitos, gerando a maior parte do código massivo e scripts base sem gastar os recursos de CPU do Arquiteto (que roda local).
- Empacota tudo numa branch focada na funcionalidade exigida e propõe ao repositório central na forma de um PR (Pull Request) polido.

---

### O Fluxo: Planejamento à Execução (Human -> Architect -> Operator)

```mermaid
gitGraph
    commit id: "Inicia repositório"
    branch especificação-architect
    checkout especificação-architect
    commit id: "Antigravity cria a issue/plano"
    branch jules-worker
    checkout jules-worker
    commit id: "Jules baixa contexto local"
    commit id: "Jules: implementa WebGPU/Puter.js"
    commit id: "Jules: aplica testes de Code Review"
    checkout especificação-architect
    merge jules-worker id: "Jules abre PR -> Antigravity faz Lint"
    checkout main
    merge especificação-architect id: "Dr. Victor (Tech Lead) dá OK e Merge"
```
